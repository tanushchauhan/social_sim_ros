#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import PoseArray, PoseStamped, Twist
from nav_msgs.msg import Odometry
from ros_tcp_endpoint import TcpServer
from ros_tcp_endpoint.publisher import RosPublisher
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import CameraInfo, CompressedImage, LaserScan
from std_msgs.msg import Bool, Float32

from social_sim_ros.msg import AgentArray, SceneInfo, TrialInfo
from sean_bridge.tcp_server_tf import RosTFBroadcaster


def camera(prefix):
    return {
        f'/{prefix}/camera_info': RosPublisher(f'/{prefix}/camera_info', CameraInfo),
        f'/{prefix}/compressed': RosPublisher(f'/{prefix}/compressed', CompressedImage),
    }


def main(args=None):
    rclpy.init(args=args)

    # Unity sends these topics without registering them first, so they are declared here.
    # Topics Unity subscribes to (ROS -> Unity) are registered by the connector at runtime.
    publishers = {
        # simulated clock
        '/clock': RosPublisher('/clock', Clock, queue_size=10),

        # trial info
        '/social_sim/scene_info': RosPublisher('/social_sim/scene_info', SceneInfo, queue_size=10),
        '/social_sim/metrics': RosPublisher('/social_sim/metrics', TrialInfo, queue_size=10),
        '/social_sim/agents': RosPublisher('/social_sim/agents', AgentArray, queue_size=10),
        '/social_sim/agent_positions': RosPublisher('/social_sim/agent_positions', PoseArray, queue_size=10),
        '/social_sim/group_positions': RosPublisher('/social_sim/group_positions', PoseArray, queue_size=10),

        # implemented by InputPublisher
        '/social_sim/trigger': RosPublisher('/social_sim/trigger', Bool, queue_size=10),
        '/social_sim/cmd_vel': RosPublisher('/social_sim/cmd_vel', Twist, queue_size=10),

        # implemented by SituationRuleBased
        **{
            f'/social_sim/situations/rule_based/{name}':
                RosPublisher(f'/social_sim/situations/rule_based/{name}', Float32, queue_size=10)
            for name in ('cross_path', 'down_path', 'empty', 'join_group', 'leave_group')
        },

        # TF, implemented by WorldTransformPublisher
        '/map_to_odom': RosTFBroadcaster('odom', 'map'),
        '/map_to_base_link': RosTFBroadcaster('base_link', 'map'),
        # TF, implemented by RelativeTransformPublisher
        '/base_link_to_firstperson_rgb_link': RosTFBroadcaster('firstperson_rgb_link', 'base_link'),
        '/base_link_to_thirdperson_rgb_link': RosTFBroadcaster('thirdperson_rgb_link', 'base_link'),
        '/base_link_to_overhead_rgb_link': RosTFBroadcaster('overhead_rgb_link', 'base_link'),
        '/base_link_to_center_depth_link': RosTFBroadcaster('center_depth_link', 'base_link'),
        '/base_link_to_center_depth_optical_frame': RosTFBroadcaster('center_depth_optical_frame', 'base_link'),
        '/base_link_to_laser': RosTFBroadcaster('laser', 'base_link'),
        '/base_link_to_front_right_wheel_link': RosTFBroadcaster('front_right_wheel_link', 'base_link'),
        '/base_link_to_front_left_wheel_link': RosTFBroadcaster('front_left_wheel_link', 'base_link'),

        # odom
        '/robot_odom': RosPublisher('/robot_odom', Odometry),

        # maps, implemented in CreateMap
        '/short_map/compressed': RosPublisher('/short_map/compressed', CompressedImage),
        '/tall_map/compressed': RosPublisher('/tall_map/compressed', CompressedImage),

        '/laser_raycast': RosPublisher('/laser_raycast', LaserScan, queue_size=10),

        # goal
        '/move_base_simple/goal': RosPublisher('/move_base_simple/goal', PoseStamped),
    }

    # images, implemented in classes that derive from BaseCameraPublisher
    for prefix in ('center_depth', 'agent_rgb', 'robot_firstperson_rgb', 'robot_thirdperson_rgb',
                   'robot_overhead_rgb', 'player_firstperson_rgb'):
        publishers.update(camera(prefix))

    tcp_server = TcpServer('tcp_server')
    tcp_server.start(publishers)
    tcp_server.setup_executor()

    tcp_server.destroy_nodes()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
