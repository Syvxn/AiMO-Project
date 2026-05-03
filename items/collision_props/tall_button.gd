extends Area2D


signal pushed(id: String)

@export var cooldown_time := 0.5
@export var button_enabled := true
@export var button_id := ""


func _ready() -> void:
	$CooldownTimer.wait_time = cooldown_time


func interact():
	push()


func push():
	if button_enabled:
		button_enabled = false
		$CooldownTimer.start()
		pushed.emit(button_id)
		$AnimatedSprite2D.play("push")


func _on_cooldown_timer_timeout() -> void:
	button_enabled = true
