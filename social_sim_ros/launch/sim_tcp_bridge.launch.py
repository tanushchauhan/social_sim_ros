from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('ip', default_value='0.0.0.0'),
        DeclareLaunchArgument('port', default_value='10000'),
        Node(
            package='ros_tcp_endpoint',
            executable='default_server_endpoint',
            name='UnityEndpoint',
            output='screen',
            respawn=True,
            parameters=[{
                'use_sim_time': True,
                'ROS_IP': ParameterValue(LaunchConfiguration('ip'), value_type=str),
                'ROS_TCP_PORT': ParameterValue(LaunchConfiguration('port'), value_type=int),
            }],
        ),
    ])
