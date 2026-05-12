extends Area2D

@export var turned_on := true
@export var groups_to_move : Array[String]
@export var direction_to_move := Vector2.DOWN
@export var speed := 50.0


func _physics_process(_delta: float) -> void:
	if not turned_on:
		return
	for body in get_overlapping_bodies():
		for group in groups_to_move:
			if body.is_in_group(group):
				if "move_and_slide" in body:
					body.velocity += direction_to_move * speed
					body.move_and_slide()
				#elif "apply_central_force" in body:
					#body.apply_central_force(direction_to_move * speed * 20.0)
				break
