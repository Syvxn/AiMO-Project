extends CharacterBody2D

var username := ""
var walk_speed := 100
var push_force := 70
var current_stand_animation := "stand_down"
var controllable := true

@export var debug := false

@onready var character_sprites = $CharacterSprites
@onready var input_handler = $InputHandler
@onready var nav_agent = $NavAgent


func _ready() -> void:
	SignalBus.chat_opened.connect(lock_controls)
	SignalBus.chat_closed.connect(release_controls)
	apply_visuals(fetch_visuals())
	$InputHandler.set_multiplayer_authority(int(name))
	$Camera2D.set_multiplayer_authority(int(name))
	$Camera2D.enable_if_authority()
	SignalBus.finished_loading.emit()



func _physics_process(_delta: float) -> void: 
	#region movement
	var walk_vec = input_handler.walk_direction
	if  walk_vec: # manual walk
		velocity = walk_speed * walk_vec
	elif $InputHandler.auto_move == true: # click-to-move or external
		if not nav_agent.target_position == $InputHandler.auto_move_target:
			nav_agent.target_position = $InputHandler.auto_move_target
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


func lock_controls():
	# this back-and-forth is a little stupid, but hey
	input_handler.walk_direction = Vector2.ZERO
	controllable = false
func release_controls():
	controllable = true


# anyone can call this, and it'll be called everywhere
@rpc("any_peer", "call_local")
func fetch_visuals() -> Variant:
	var file_string = "res://databaseish/{0}_visuals.json".format([username])
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


func apply_visuals(data):
	character_sprites.apply_visuals(data)


func get_applied_visuals_data() -> Dictionary:
	return $CharacterSprites.current_data


# this kinda sucks but it's fine for now
func toggle_customize_menu():
	$Camera2D.toggle_view()
	if not $CustomizeCharMenu.visible:
		$CustomizeCharMenu.show()
		$CustomizeCharMenu.select_current_options()
	else:
		$CustomizeCharMenu.hide()
