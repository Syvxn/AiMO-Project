extends Node3D



func explode() -> void:
	%LeftWing.apply_central_impulse(Vector3(
		30.0, randf_range(-20.0, 20.0), randf_range(-20.0, 20.0)
	))
	%LeftWing.apply_torque_impulse(Vector3(
		randf_range(-10.0, 10.0), randf_range(-10.0, 10.0), randf_range(-10.0, 10.0)
	))
	%RightWing.apply_central_impulse(Vector3(
		-30.0, randf_range(-20.0, 20.0), randf_range(-20.0, 20.0)
	))
	%RightWing.apply_torque_impulse(Vector3(
		randf_range(-10.0, 10.0), randf_range(-10.0, 10.0), randf_range(-10.0, 10.0)
	))
	%Body.apply_torque_impulse(Vector3(
		randf_range(-10.0, 10.0), randf_range(-10.0, 10.0), randf_range(-10.0, 10.0)
	))
