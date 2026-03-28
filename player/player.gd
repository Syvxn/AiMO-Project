extends CharacterBody2D

var username := ""
var walk_speed := 100
var push_force := 70
var current_stand_animation := "stand_down"
var controllable := true

@onready var body_sprite = $BodySprite
@onready var input_handler = $InputHandler


func _ready() -> void:
	SignalBus.chat_opened.connect(lock_controls)
	SignalBus.chat_closed.connect(release_controls)
	apply_visuals()
	$InputHandler.set_multiplayer_authority(int(name))
	$Camera2D.set_multiplayer_authority(int(name))
	$Camera2D.enable()
	SignalBus.finished_loading.emit()



func _physics_process(_delta: float) -> void: 
	#region movement and animation
	# velocity + move_and_slide() handle actual movement, rest is animation
	var walk_vec = input_handler.walk_direction
	if walk_vec == Vector2.ZERO:
		velocity = Vector2.ZERO
		body_sprite.play(current_stand_animation)
	else:
		velocity = walk_speed * walk_vec
		# iso version
		#velocity = walk_speed * Vector2(walk_vec.x, walk_vec.y * 0.5)
		if abs(walk_vec.x) > abs(walk_vec.y):
			if walk_vec.x > 0:
				body_sprite.play("walk_right")
				current_stand_animation = "stand_right"
			else:
				body_sprite.play("walk_left")
				current_stand_animation = "stand_left"
		else:
			if walk_vec.y > 0:
				body_sprite.play("walk_down")
				current_stand_animation = "stand_down"
			else:
				body_sprite.play("walk_up")
				current_stand_animation = "stand_up"
	move_and_slide()
	#endregion
	#region push movables
	for i in get_slide_collision_count():
		var collision = get_slide_collision(i)
		var collider = collision.get_collider()
		if collider.is_in_group("movables") and collider.has_method("apply_central_impulse"):
			collider.apply_central_impulse(collision.get_normal() * -1 * push_force)
	#endregion


# this would be a little more elaborate, obviously
func apply_visuals():
	if username == "Lasse":
		$BodySprite.sprite_frames = load("res://textures/sprite_frames/chell_var1.tres")
	

func lock_controls():
	# this back-and-forth is a little stupid, but hey
	input_handler.walk_direction = Vector2.ZERO
	controllable = false
func release_controls():
	controllable = true
