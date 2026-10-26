import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    sean = get_package_share_directory('social_sim_ros')
    scene = LaunchConfiguration('scene')
    params = os.path.join(sean, 'params', 'jackal', 'nav2_params.yaml')
    command_topic = '/mobile_base_controller/cmd_vel'
    nodes = [
        ('nav2_controller', 'controller_server', [('cmd_vel', 'cmd_vel_nav')]),
        ('nav2_smoother', 'smoother_server', []),
        ('nav2_planner', 'planner_server', []),
        ('nav2_behaviors', 'behavior_server', [('cmd_vel', 'cmd_vel_nav')]),
        ('nav2_bt_navigator', 'bt_navigator', [('goal_pose', '/move_base_simple/goal')]),
        ('nav2_waypoint_follower', 'waypoint_follower', []),
        ('nav2_velocity_smoother', 'velocity_smoother', [
            ('cmd_vel', 'cmd_vel_nav'), ('cmd_vel_smoothed', command_topic),
        ]),
    ]
    actions = [
        DeclareLaunchArgument('scene', default_value='lab'),
        Node(
            package='nav2_map_server', executable='map_server', name='map_server',
            output='screen', parameters=[params, {
                'yaml_filename': PathJoinSubstitution([sean, 'maps', scene, 'map.yaml']),
            }],
        ),
    ]
    # Route navigation and recovery commands through the same velocity smoother.
    for package, executable, remappings in nodes:
        actions.append(Node(
            package=package, executable=executable, name=executable,
            output='screen', parameters=[params], remappings=remappings,
        ))
    actions.append(Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_navigation', output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': ['map_server'] + [name for _, name, _ in nodes],
        }],
    ))
    return LaunchDescription(actions)
