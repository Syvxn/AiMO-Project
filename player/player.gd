extends CharacterBody2D

var username := ""
var walk_speed := 100
var push_force := 70
var current_stand_animation := "stand_down"
var controllable := true
var auto_move := false

@export var debug := false

@onready var body_sprite = $BodySprite
@onready var input_handler = $InputHandler
@onready var nav_agent = $NavAgent


func _ready() -> void:
	SignalBus.chat_opened.connect(lock_controls)
	SignalBus.chat_closed.connect(release_controls)
	apply_visuals()
	$InputHandler.set_multiplayer_authority(int(name))
	$Camera2D.set_multiplayer_authority(int(name))
	$Camera2D.enable()
	SignalBus.finished_loading.emit()



func _physics_process(_delta: float) -> void: 
	#region movement
	var walk_vec = input_handler.walk_direction
	if  walk_vec: # manual walk
		auto_move = false
		velocity = walk_speed * walk_vec
	elif auto_move == true: # click-to-move or external
		if not nav_agent.is_target_reachable():
			velocity = Vector2.ZERO
		else:
			velocity = walk_speed * global_position.direction_to(nav_agent.get_next_path_position())
	else: # no movement
		velocity = Vector2.ZERO
	move_and_slide()
	#endregion
	#region animation
	if abs(velocity.x) > abs(velocity.y):
		if velocity.x > 0:
			body_sprite.play("walk_right")
			current_stand_animation = "stand_right"
		else:
			body_sprite.play("walk_left")
			current_stand_animation = "stand_left"
	elif abs(velocity.x) < abs(velocity.y):
		if velocity.y > 0:
			body_sprite.play("walk_down")
			current_stand_animation = "stand_down"
		else:
			body_sprite.play("walk_up")
			current_stand_animation = "stand_up"
	else:
		body_sprite.play(current_stand_animation)
	#endregion
	#region push movables
	for i in get_slide_collision_count():
		var collision = get_slide_collision(i)
		var collider = collision.get_collider()
		if collider.is_in_group("movables") and collider.has_method("apply_central_impulse"):
			collider.apply_central_impulse(collision.get_normal() * -1 * push_force)
	#endregion


func move_to(target: Vector2):
	auto_move = true
	nav_agent.target_position = target

func _on_nav_agent_target_reached() -> void:
	#velocity = Vector2.ZERO
	auto_move = false


func lock_controls():
	# this back-and-forth is a little stupid, but hey
	input_handler.walk_direction = Vector2.ZERO
	controllable = false
func release_controls():
	controllable = true



# this would be a little more elaborate, obviously
func apply_visuals():
	if username == "Lasse":
		$BodySprite.sprite_frames = load("res://textures/sprite_frames/faith.tres")
