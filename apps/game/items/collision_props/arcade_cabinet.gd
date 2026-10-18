extends Area2D


func _ready() -> void:
	%ArcadeView.hide()


func interact() -> void:
	%ArcadeView.launch_arcade_game()


func _on_screen_timer_timeout() -> void:
	# you've heard of magic numbers, now get ready for magic colors!
	%Screen.self_modulate = [
		Color("ff94c2"),
		Color("00d9b5"),
		Color("e2b261"),
		Color("83c1fa")
	].pick_random()
