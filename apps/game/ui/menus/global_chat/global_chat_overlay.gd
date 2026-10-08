extends CanvasLayer

var input_field_focused := false
var bad_words := []

@onready var msg_node = load("res://ui/menus/global_chat/global_chat_message.tscn")


func _ready() -> void:
	hide()
	var profanity_paths = [
		"res://bad_words/en.txt",
		"res://bad_words/fi.txt",
		"res://bad_words/zh.txt"
	]
	for path in profanity_paths:
		var file = FileAccess.open(path, FileAccess.READ)
		var content = file.get_as_text()
		for bad_word in content.split("\n"):
			if not "#" in bad_word:
				bad_words.append(bad_word)
		file.close()
	print("Number of bad words in filter: " +  str(len(bad_words)))
	#print(bad_words)

func close_menu() -> void:
	hide()

@rpc("any_peer", "call_local")
func add_chat_message(msg_info) -> void:
	assert(multiplayer.is_server())
	var msg = msg_info[0]
	if msg[0] == "/":
		command(msg)
		return
	var censored_msg = censor_message(msg)
	var msg_node_instance = msg_node.instantiate()
	msg_node_instance.text = str(msg_info[1]) + ": " + censored_msg
	%MessagesContainer.add_child(msg_node_instance, true)


func command(msg) -> void:
	match msg:
		"/purge":
			for child in %MessagesContainer.get_children():
				child.queue_free()
		_:
			print("Invalid command")


func censor_message(msg: String) -> String:
	for bad_word in bad_words:
		if bad_word in msg:
			return "[INAPPROPRIATE]"
	return msg


func _on_line_edit_focus_entered() -> void:
	SignalBus.global_chat_input_focused.emit()
	input_field_focused = true
func _on_line_edit_focus_exited() -> void:
	SignalBus.global_chat_input_unfocused.emit()
	input_field_focused = false


func _on_line_edit_text_submitted(new_text: String) -> void:
	add_chat_message.rpc_id(1, [new_text, multiplayer.get_unique_id()])
	%LineEdit.text = ""
