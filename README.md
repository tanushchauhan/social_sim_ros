# Social Environment Autonomous Navigation 2.0

This is the ROS project for SEAN: Social Environment for Autonomous Navigation

## ROS 2 migration endpoint

`ros2 launch social_sim_ros sim_tcp_bridge.launch.py` runs `sean_tcp_endpoint`,
a compatibility wrapper for ROS-TCP-Endpoint revision
`54c1a64b6d5ef6ffa0a0431570bb74329b79b15b`. It implements the connector v0.7
removal commands, serializes registration changes, and reuses registrations
when their topic type and publisher options are unchanged. Changed options
still replace the old node; removal requests are idempotent.

The launch does not globally remap node names. Each per-topic node keeps its
own name, and the bridge uses wall time so it can recover while simulation
time is unavailable. Message timestamps still come from Unity. The upstream
endpoint can log EOF and a sender write racing socket closure during reload;
these diagnostics do not establish failure or success without sensor and
registration checks. See the workspace repository's `VALIDATION.md`.

## Source Repositories

Other repositories for the project are:

  - ROS project (this repository): https://github.com/yale-sean/social_sim_ros

  - Unity Project: https://github.com/yale-sean/social_sim_unity

  - Documentation: https://github.com/yale-sean/docs

  - Dockerized Catkin Workspace: https://github.com/yale-sean/sim_ws
