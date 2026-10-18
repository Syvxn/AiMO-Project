extends Node3D

@onready var projectile = load("res://misc/3d_test/projectile.tscn")

func fire(targets: Array, speed: float) -> void:
	for target in targets:
		var projectile_instance = projectile.instantiate()
		add_child(projectile_instance)
		projectile_instance.look_at(target)
		projectile_instance.apply_central_impulse(projectile_instance.global_basis.z * -speed)
		
