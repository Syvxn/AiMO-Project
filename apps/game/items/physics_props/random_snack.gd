extends RigidBody2D

var lootable_type := "snack"

@export var lootable := false


func _ready() -> void:
	var sprites = $Sprites.get_children()
	for sprite in sprites:
		sprite.hide()
	sprites.pick_random().show()
	if multiplayer.is_server():
		$DespawnTimer.start(randi_range(11, 15))


func _on_despawn_timer_timeout() -> void:
	if multiplayer.is_server():
		queue_free()
