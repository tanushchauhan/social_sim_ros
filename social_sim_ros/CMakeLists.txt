cmake_minimum_required(VERSION 3.8)
project(social_sim_ros)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Agent.msg"
  "msg/AgentArray.msg"
  "msg/PersonEntry.msg"
  "msg/PersonEntryArray.msg"
  "msg/TrialInfo.msg"
  "msg/TrialStart.msg"
  "msg/SceneInfo.msg"
  "msg/RealDepthImage.msg"
  DEPENDENCIES builtin_interfaces std_msgs geometry_msgs
)

ament_python_install_package(sean_bridge)

install(PROGRAMS
  src/tcp_server.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch config params maps urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
