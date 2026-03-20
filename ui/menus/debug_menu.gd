extends CanvasLayer


@onready var username_field = $ColorRect/SubMenus/TeacherStudentChoice/MarginContainer/UsernameField



func _ready() -> void:
	for child in $ColorRect/SubMenus.get_children():
		child.hide()


func show_sub_menu(menu : String):
	for child in $ColorRect/SubMenus.get_children():
		child.hide()
	show()
	# i'm not juggling enum references for this; sue me
	match menu:
		"SERVERCLIENT":
			$ColorRect/SubMenus/ServerClientChoice.show()
		"TEACHERSTUDENT":
			$ColorRect/SubMenus/TeacherStudentChoice.show()


func _on_server_button_pressed() -> void:
	NetworkHandler.start_server()
	get_parent().get_node("MultiplayerSpawner/GameWorld").add_child(load("res://misc/server_camera.tscn").instantiate())
	hide()
	
func _on_client_button_pressed() -> void:
	NetworkHandler.start_client()
	show_sub_menu("TEACHERSTUDENT")


func _on_teacher_button_pressed() -> void:
	SignalBus.new_player_info_received.emit(username_field.text, "TEACHER")
	SignalBus.started_loading.emit()
	hide()

func _on_student_button_pressed() -> void:
	SignalBus.new_player_info_received.emit(username_field.text, "STUDENT")
	SignalBus.started_loading.emit()
	hide()
