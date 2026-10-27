# Copyright 2020 Unity Technologies; lifecycle adaptations 2026.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy at http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
"""Owned reader/sender lifetime around the pinned ROS-TCP-Endpoint protocol."""
import socket
import struct
import threading
from queue import Queue

from rclpy.serialization import deserialize_message
from ros_tcp_endpoint.client import ClientThread
from ros_tcp_endpoint.tcp_sender import (UnityTcpSender, SysCommand_Handshake,
    SysCommand_Handshake_Metadata, SysCommand_Service)


def locked_send(method):
    def send(self, *args, **kwargs):
        with self.queue_lock:
            return method(self, *args, **kwargs)
    return send


class PendingResponse:
    def __init__(self):
        self.ready = threading.Event()
        self.result = None

    def resume_with_result(self, result):
        self.result = result
        self.ready.set()

    def sleep_until_resumed(self):
        self.ready.wait()


class LifecycleSender(UnityTcpSender):
    send_unity_info = locked_send(UnityTcpSender.send_unity_info)
    send_unity_warning = locked_send(UnityTcpSender.send_unity_warning)
    send_unity_error = locked_send(UnityTcpSender.send_unity_error)
    send_unity_message = locked_send(UnityTcpSender.send_unity_message)
    send_ros_service_response = locked_send(UnityTcpSender.send_ros_service_response)
    send_topic_list = locked_send(UnityTcpSender.send_topic_list)

    def __init__(self, server):
        super().__init__(server)
        self.queue_lock = threading.RLock()
        self.service_queues = {}

    def start_sender(self, conn, halt):
        queue = Queue()
        queue.put(ClientThread.serialize_command('__handshake',
            SysCommand_Handshake(SysCommand_Handshake_Metadata())))
        with self.queue_lock:
            self.queue = queue
        worker = threading.Thread(target=self.sender_loop, args=(conn, queue, halt), name='sean-sender')
        worker.start()
        return worker, queue

    def sender_loop(self, conn, queue, halt):
        try:
            while not halt.is_set():
                item = queue.get()
                if halt.is_set():
                    break
                conn.sendall(item)
        except OSError as error:
            if not halt.is_set():
                self.tcp_server.logerr(f'Unexpected Unity send failure: {error}')
                halt.set()
                try:
                    conn.shutdown(socket.SHUT_RD)
                except OSError:
                    pass
        finally:
            with self.queue_lock:
                if self.queue is queue:
                    self.queue = None

    def stop_sender(self, worker, queue, halt):
        halt.set()
        with self.queue_lock:
            if self.queue is queue:
                self.queue = None
            with self.srv_lock:
                for srv_id, pending_queue in list(self.service_queues.items()):
                    if pending_queue is queue:
                        self.services_waiting.pop(srv_id).resume_with_result(None)
                        del self.service_queues[srv_id]
        queue.put(None)  # wake an idle sender immediately
        worker.join(timeout=2)
        if worker.is_alive():
            raise RuntimeError('Unity sender did not stop within two seconds')

    def send_unity_service_request(self, topic, service_class, request):
        pauser = PendingResponse()
        with self.queue_lock:
            if self.queue is None:
                return None
            with self.srv_lock:
                srv_id = self.next_srv_id
                self.next_srv_id += 1
                self.services_waiting[srv_id] = pauser
                self.service_queues[srv_id] = self.queue
            command = SysCommand_Service()
            command.srv_id = srv_id
            self.queue.put(ClientThread.serialize_command('__request', command)
                           + ClientThread.serialize_message(topic, request))
        pauser.sleep_until_resumed()
        if pauser.result is None:
            raise ConnectionError('Unity disconnected during service request')
        return deserialize_message(pauser.result, service_class.Response)

    def send_unity_service_response(self, srv_id, data):
        with self.srv_lock:
            pauser = self.services_waiting.pop(srv_id, None)
            self.service_queues.pop(srv_id, None)
        if pauser is not None:
            pauser.resume_with_result(data)


def read_exact(conn, size, stopping, boundary=False):
    result = bytearray()
    while len(result) < size:
        try:
            chunk = conn.recv(size-len(result))
        except socket.timeout:
            if stopping.is_set():
                raise EOFError()
            continue
        if not chunk:
            if boundary and not result:
                raise EOFError()
            raise ConnectionError('Truncated Unity TCP frame')
        result.extend(chunk)
    return bytes(result)


class LifecycleClient(ClientThread):
    def __init__(self, conn, server, ip, port):
        super().__init__(conn, server, ip, port)
        self.name = 'sean-client'
        self.stopping = threading.Event()
        self.conn.settimeout(1)

    def stop(self):
        self.stopping.set()
        try:
            self.conn.shutdown(socket.SHUT_RD)
        except OSError:
            pass

    def read_frame(self):
        length = struct.unpack('<I', read_exact(self.conn, 4, self.stopping, boundary=True))[0]
        if length > 1024*1024:
            raise ValueError('Invalid Unity TCP topic length')
        topic = read_exact(self.conn, length, self.stopping).decode('utf8').rstrip('\0')
        length = struct.unpack('<I', read_exact(self.conn, 4, self.stopping))[0]
        if length > 256*1024*1024:
            raise ValueError('Invalid Unity TCP payload length')
        return topic, read_exact(self.conn, length, self.stopping)

    def run(self):
        server = self.tcp_server
        server.loginfo(f'Connection from {self.incoming_ip}')
        halt = threading.Event()
        worker, queue = server.unity_tcp_sender.start_sender(self.conn, halt)
        # Service framing state belongs to this connection, not its replacement.
        pending_id, pending_request = None, False
        try:
            while not self.stopping.is_set() and not halt.is_set():
                destination, data = self.read_frame()
                if destination == '__disconnect':
                    server.loginfo(f'Graceful Unity disconnect from {self.incoming_ip}')
                    break
                if pending_id is not None:
                    if pending_request:
                        self.send_ros_service_request(pending_id, destination, data)
                    else:
                        server.send_unity_service_response(pending_id, data)
                    pending_id = None
                elif destination in ('__request', '__response'):
                    import json
                    pending_id = json.loads(data.rstrip(b'\0'))['srv_id']
                    pending_request = destination == '__request'
                elif not destination:
                    continue
                elif destination.startswith('__'):
                    server.handle_syscommand(destination, data)
                elif destination in server.publishers_table:
                    server.publishers_table[destination].send(data)
                else:
                    raise ValueError(f'Not registered to publish topic {destination!r}')
        except EOFError:
            if not self.stopping.is_set() and not halt.is_set():
                server.logwarn('Unannounced Unity disconnect at a frame boundary')
        except (OSError, ValueError) as error:
            if not self.stopping.is_set() and not halt.is_set():
                server.logerr(f'Unexpected Unity receive failure: {error}')
        finally:
            try:
                server.unity_tcp_sender.stop_sender(worker, queue, halt)
            except RuntimeError as error:
                server.logerr(str(error))
            try:
                self.conn.shutdown(socket.SHUT_WR)
            except OSError:
                pass
            self.conn.close()
            server.loginfo(f'Disconnected from {self.incoming_ip}')
