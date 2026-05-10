extends RigidBody2D

var lootable_type := "snack"

@export var lootable := false


func _ready() -> void:
	var sprites = $Sprites.get_children()
	for sprite in sprites:
		sprite.hide()
	sprites.pick_random().show()
