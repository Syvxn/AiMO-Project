extends Area2D


var turned_on := false

@onready var random_snack = load("res://items/physics_props/random_snack.tscn")


func _ready() -> void:
	$AnimatedSprite2D.play("dark")


func interact():
	buy()

func buy():
	if turned_on:
		$AnimatedSprite2D.play("yes")
		print("You bought something! I think.")
		await get_tree().create_timer(1).timeout
		%SnackPoint.add_child(random_snack.instantiate())


func _on_body_entered(body: Node2D) -> void:
	if not turned_on:
		if body.is_in_group("players"):
			turned_on = true
			$AnimatedSprite2D.play("light_up")


func _on_body_exited(body: Node2D) -> void:
	if turned_on:
		if body.is_in_group("players"):
			$SleepTimer.start()


func _on_sleep_timer_timeout() -> void:
	turned_on = false
	$AnimatedSprite2D.play("dark")
