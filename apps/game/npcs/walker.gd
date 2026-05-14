extends CharacterBody2D

var walk_speed := 50
var push_force := 70
var current_stand_animation := "stand_down"
var walk_vec : Vector2
var auto_move := false
var auto_move_target : Vector2
var stopped := false

@export var barks : Array[String]
@export var current_bark_index := 0
@onready var character_sprites = $CharacterSprites
@onready var nav_agent = $NavAgent


func _ready() -> void:
	apply_visuals(fetch_visuals())
	if multiplayer.is_server():
		$NavAgent.target_reached.connect(_on_nav_agent_target_reached)
		$WaitTimer.timeout.connect(_on_wait_timer_timeout)
		$WalkTimer.timeout.connect(_on_walk_timer_timeout)
		$WaitTimer.start(randf_range(8.0, 14.0))


func _physics_process(_delta: float) -> void: 
	#region movement
	if multiplayer.is_server():
		if walk_vec and not stopped: # manual walk
			velocity = walk_speed * walk_vec
		elif auto_move and not stopped: # click-to-move or external
			if not nav_agent.target_position == auto_move_target:
				nav_agent.target_position = auto_move_target
			if not nav_agent.is_target_reachable():
				velocity = Vector2.ZERO
			else:
				velocity = walk_speed * global_position.direction_to(nav_agent.get_next_path_position())
		else: # no movement
			velocity = Vector2.ZERO
		move_and_slide()
	#endregion
	#region animation
	if velocity == Vector2.ZERO:
		character_sprites.play_animation(current_stand_animation)
	elif abs(velocity.x) >= abs(velocity.y):
		if velocity.x > 0:
			character_sprites.play_animation("walk_right")
			current_stand_animation = "stand_right"
		else:
			character_sprites.play_animation("walk_left")
			current_stand_animation = "stand_left"
	else:
		if velocity.y > 0:
			character_sprites.play_animation("walk_down")
			current_stand_animation = "stand_down"
		else:
			character_sprites.play_animation("walk_up")
			current_stand_animation = "stand_up"
	#endregion
	#region push movables
	for i in get_slide_collision_count():
		var collision = get_slide_collision(i)
		var collider = collision.get_collider()
		if collider.is_in_group("movables") and collider.has_method("apply_central_impulse"):
			collider.apply_central_impulse(collision.get_normal() * -1 * push_force)
	#endregion


func _on_nav_agent_target_reached() -> void:
	$InputHandler.auto_move = false


# anyone can call this, and it'll be called everywhere
@rpc("any_peer", "call_local")
func fetch_visuals() -> Variant:
	var file_string = "res://databaseish/{0}_visuals.json".format([name])
	var file = FileAccess.open(file_string, FileAccess.READ)
	if not file:
		file = FileAccess.open("res://databaseish/default_visuals.json", FileAccess.READ)
	var json = JSON.new()
	var error = json.parse(file.get_as_text())
	if error == OK:
		return json.data
	else:
		print("Error: ", error_string(error))
		return null


@rpc("any_peer", "call_local")
func apply_visuals(data):
	character_sprites.apply_visuals(data)


func get_applied_visuals_data() -> Dictionary:
	return $CharacterSprites.current_data


@rpc("authority", "call_local")
func beam_up():
	$CharacterSprites.use_parent_material = true
	get_material().set_shader_parameter("mask_y_delta", 0.0)
	for i in range(1, 6):
		await get_tree().create_timer(0.1).timeout
		get_material().set_shader_parameter("mask_y_delta", i*0.1)


@rpc("authority", "call_local")
func beam_down():
	get_material().set_shader_parameter("mask_y_delta", 0.5)
	for i in range(4, -1, -1):
		await get_tree().create_timer(0.1).timeout
		get_material().set_shader_parameter("mask_y_delta", i*0.1)
	$CharacterSprites.use_parent_material = false


func bark():
	print("woof")
	stopped = true
	%BarkLabel.show()
	%BarkLabel.text = barks[current_bark_index]
	current_bark_index += 1
	if current_bark_index >= len(barks):
		current_bark_index = 0
		%BarkLabel.hide()
	else:
		%HideBarksTimer.start()


func _on_hide_barks_timer_timeout() -> void:
	%BarkLabel.hide()
	stopped = false


func _on_wait_timer_timeout() -> void:
	# replace with nav_agent autowalk
	walk_vec = Vector2(float(randi_range(-1,1)), float(randi_range(-1,1)))
	$WalkTimer.start(randf_range(2.0, 4.0))


func _on_walk_timer_timeout() -> void:
	# replace with nav_agent autowalk
	walk_vec = Vector2.ZERO
	$WaitTimer.start(randf_range(8.0, 14.0))
