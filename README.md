# Social Environment Autonomous Navigation 2.0

This is the ROS project for SEAN: Social Environment for Autonomous Navigation

## ROS 2 migration endpoint

`ros2 launch social_sim_ros sim_tcp_bridge.launch.py` runs `sean_tcp_endpoint`,
a compatibility wrapper for ROS-TCP-Endpoint revision
`54c1a64b6d5ef6ffa0a0431570bb74329b79b15b`. It implements the connector v0.7
removal commands, serializes registration changes, and reuses registrations
when their topic type and publisher options are unchanged. Changed options
still replace the old node; removal requests are idempotent. Registration changes
share the executor wait-set lock, with active-client priority over idle waits,
so removing QoS-event handles cannot race wait-set construction.

The launch does not globally remap node names. Each per-topic node keeps its
own name, and the bridge uses wall time so it can recover while simulation
time is unavailable. Message timestamps still come from Unity. The upstream
endpoint can log EOF and a sender write racing socket closure during reload;
these diagnostics do not establish failure or success without sensor and
registration checks. See the workspace repository's `VALIDATION.md`.

## Warehouse Kuri navigation

`ros2 launch social_sim_ros nav2_kuri.launch.py scene:=warehouse` uses the
configured Unity Warehouse robot, Kuri, with a dedicated navigation profile.
Verify the player's `SEAN velocity-controlled robot: Kuri` startup message.
The profile uses collision-checked Regulated Pure Pursuit, a 0.3 m/s desired
speed, a 0.60 m circular footprint enclosing the audited physical body with
clearance, and a graded inflation field extending to 1.0 m. The installed
consistent-replanning tree checks path validity and retains a valid route between
periodic replans. Collision checking and recovery remain active. Marking and
clearing use the laser's full 3.5 m observation range. Navigation and
recovery commands continue through the same velocity smoother.

`nav2_jackal.launch.py` retains its original translated DWB profile. Its name
previously led to the Warehouse fixture being labelled Jackal without checking
the live Unity robot. Kuri results do not qualify the Jackal model. See the
coordination repository's longer-navigation guide/result for exact pins,
criteria, failures, and the scope of validation.

## Source Repositories

Other repositories for the project are:

  - ROS project (this repository): https://github.com/yale-sean/social_sim_ros

  - Unity Project: https://github.com/yale-sean/social_sim_unity

  - Documentation: https://github.com/yale-sean/docs

  - Dockerized Catkin Workspace: https://github.com/yale-sean/sim_ws
