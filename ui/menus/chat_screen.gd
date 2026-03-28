extends CanvasLayer


@onready var chat_bubble = load("res://ui/menus/chat_bubble.tscn")
@onready var scroll_container = %ScrollContainer
@onready var chat_container = %ChatContainer
@onready var input_field = %InputField


func _ready() -> void:
	SignalBus.chat_opened.connect(show)
	SignalBus.chat_opened.connect(input_field.grab_focus)
	SignalBus.chat_closed.connect(hide)


func add_bubble(text: String, side: String):
	var chat_bubble_instance = chat_bubble.instantiate()
	chat_bubble_instance.get_node("BubbleText").text = text
	#region garbage magic number resizing circus
	var bubble_min_size = Vector2(clamp(len(text)*10, 80, 400), 0)
	chat_bubble_instance.set_custom_minimum_size(bubble_min_size)
	#endregion
	if side == "left":
		chat_bubble_instance.set_h_size_flags(Control.SizeFlags.SIZE_SHRINK_BEGIN)
	else:
		chat_bubble_instance.set_h_size_flags(Control.SizeFlags.SIZE_SHRINK_END)
	chat_container.add_child(chat_bubble_instance)
	await get_tree().process_frame
	scroll_container.ensure_control_visible(chat_bubble_instance)


func submit_input(input_text):
	input_field.set_text("")
	add_bubble(input_text, "right")
	#region http 
	var http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(self.chat_request_completed)
	var url = Env.CHAT_SERVER_URL
	var custom_headers = PackedStringArray()
	#var method = HTTPClient.Method.METHOD_POST
	var method = HTTPClient.Method.METHOD_GET
	# sanitizer? i hardly know 'er
	var data = input_text
	http_request.request(url, custom_headers, method, data)
	#endregion


func chat_request_completed(result, response_code, _headers, body):
	print("HTTP request: ", str(result), " ", str(response_code))
	await get_tree().create_timer(0.5).timeout    # simulate wait
	add_bubble(body.get_string_from_utf8(), "left")


func add_debug_reply():
	await get_tree().create_timer(1).timeout
	var musketeerism = "\"Great criminals bear about them a kind of predestination which makes them surmount all obstacles, which makes them escape all dangers, up to the moment which a wearied Providence has marked as the rock of their impious fortunes.\""
	add_bubble(musketeerism, "left")


func _on_submit_button_pressed() -> void:
	submit_input(input_field.get_text())
	input_field.grab_focus()
func _on_input_field_text_submitted(new_text: String) -> void:
	submit_input(new_text)
