extends CharacterBody2D

var walk_speed := 100
var current_stand_animation := "stand_down"

@onready var body_sprite = $BodySprite
@onready var input_handler = $InputHandler


func _ready() -> void:
	apply_visuals()
	#$PlayerInputAttacher.set_multiplayer_authority(int(name))
	#$BodySprite/Camera2D.set_multiplayer_authority(int(name))
	$Camera2D.enable()



func _physics_process(_delta: float) -> void: 
	# velocity + move_and_slide() handle actual movement, rest is animation
	var walk_vec = input_handler.walk_direction
	if walk_vec == Vector2.ZERO:
		velocity = Vector2.ZERO
		body_sprite.play(current_stand_animation)
	else:
		velocity = walk_speed * walk_vec
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



func apply_visuals():
	pass
	
	
