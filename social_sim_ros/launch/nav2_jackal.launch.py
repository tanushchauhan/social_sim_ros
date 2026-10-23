import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    sean = get_package_share_directory('social_sim_ros')
    nav2 = get_package_share_directory('nav2_bringup')
    scene = LaunchConfiguration('scene')
    params = os.path.join(sean, 'params', 'jackal', 'nav2_params.yaml')

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[params, {'yaml_filename': PathJoinSubstitution([sean, 'maps', scene, 'map.yaml'])}],
    )
    map_lifecycle = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[{'use_sim_time': True, 'autostart': True, 'node_names': ['map_server']}],
    )
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2, 'launch', 'navigation_launch.py')),
        launch_arguments={
            'use_sim_time': 'true',
            'params_file': params,
            'autostart': 'true',
        }.items(),
    )
    return LaunchDescription([
        DeclareLaunchArgument('scene', default_value='lab'),
        map_server,
        map_lifecycle,
        navigation,
    ])
