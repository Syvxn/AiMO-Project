extends RigidBody2D

var original_height


func _ready() -> void:
	original_height = global_position.y
	var sprites = $Sprites.get_children()
	for sprite in sprites:
		sprite.hide()
	sprites.pick_random().show()
	
	
