extends CanvasLayer

enum SubMenu {SERVERCLIENT, TEACHERSTUDENT}


func _ready() -> void:
	for child in $ColorRect/SubMenus.get_children():
		child.hide()


func show_sub_menu(menu : SubMenu):
	for child in $ColorRect/SubMenus.get_children():
		child.hide()
	show()
	match menu:
		SubMenu.SERVERCLIENT:
			$ColorRect/SubMenus/ServerClientChoice.show()
		SubMenu.TEACHERSTUDENT:
			$ColorRect/SubMenus/ServerClientChoice.show()


func _on_server_button_pressed() -> void:
	NetworkHandler.start_server()
	hide()


func _on_client_button_pressed() -> void:
	NetworkHandler.start_client()
	hide()


func _on_teacher_button_pressed() -> void:
	pass # Replace with function body.


func _on_student_button_pressed() -> void:
	pass # Replace with function body.
