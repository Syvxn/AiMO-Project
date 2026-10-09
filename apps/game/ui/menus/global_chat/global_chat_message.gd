extends Label


@rpc("any_peer", "call_local")
func delete() -> void:
	queue_free()


func _on_gui_input(event: InputEvent) -> void:
	if event.is_action_pressed("delete_global_chat_message"):
		delete.rpc_id(1)
