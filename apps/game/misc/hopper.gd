extends Area2D

@export var server_only := true
@export var turned_on := true
@export var groups_to_make_go_away : Array[String]


func _physics_process(_delta: float) -> void:
	if server_only and not multiplayer.is_server():
		return
	if not turned_on:
		return
	for body in get_overlapping_bodies():
		for group in groups_to_make_go_away:
			if body.is_in_group(group):
				body.queue_free()
				break
