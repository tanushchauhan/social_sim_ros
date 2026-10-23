from geometry_msgs.msg import PoseStamped, TransformStamped
from rclpy.serialization import deserialize_message
from ros_tcp_endpoint.communication import RosSender
from tf2_ros import TransformBroadcaster


class RosTFBroadcaster(RosSender):
    """
    Receives a PoseStamped from Unity and publishes it to the TF tree.
    """

    def __init__(self, child, parent):
        super().__init__(f"tf_{parent}_to_{child}".replace("/", "_"))
        self.child = child
        self.parent = parent
        self.last_ts = 0.0
        self.br = TransformBroadcaster(self)

    def send(self, data):
        msg = deserialize_message(data, PoseStamped)
        ts = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if ts <= self.last_ts:
            return None
        self.last_ts = ts

        tf = TransformStamped()
        tf.header.stamp = msg.header.stamp
        tf.header.frame_id = self.parent
        tf.child_frame_id = self.child
        tf.transform.translation.x = msg.pose.position.x
        tf.transform.translation.y = msg.pose.position.y
        tf.transform.translation.z = msg.pose.position.z
        tf.transform.rotation = msg.pose.orientation
        self.br.sendTransform(tf)
        return None
