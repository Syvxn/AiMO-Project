extends RigidBody2D

var original_height
var collectable := false


func _ready() -> void:
	original_height = global_position.y
	var sprites = $Sprites.get_children()
	for sprite in sprites:
		sprite.hide()
	sprites.pick_random().show()
	
	


func _on_body_entered(body: Node) -> void:
	if collectable and body.is_in_group("players"):
		# +1 to player.something
		queue_free()
