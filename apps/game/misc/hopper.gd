extends Area2D

@export var turned_on := true
@export var groups_to_make_go_away : Array[String]

func _ready() -> void:
	print(groups_to_make_go_away)

func _physics_process(_delta: float) -> void:
	if not turned_on:
		return
	for body in get_overlapping_bodies():
		for group in groups_to_make_go_away:
			if body.is_in_group(group):
				body.call_deferred("queue_free")
				break
