extends CanvasLayer


@onready var chat_bubble = load("res://ui/menus/chat_and_quiz/chat_bubble.tscn")
@onready var quiz_question = load("res://ui/menus/chat_and_quiz/quiz_question.tscn")
@onready var chat_panel = %ChatPanel
@onready var chat_scroll_container = %ChatScrollContainer
@onready var chat_container = %ChatContainer
@onready var chat_input_field = %ChatInputField
@onready var quiz_panel = %QuizPanel
@onready var quiz_title = %QuizTitle
@onready var quiz_container = %QuizContainer

var chat_socket := WebSocketPeer.new()
var socket_started := false
var pending_messages: Array[String] = []
var active_stream_bubble: Control = null
var chat_session_id: String = ""
var awaiting_response := false
var response_deadline_msec := 0
var waiting_notice_sent := false

const FIRST_RESPONSE_WAIT_MSEC := 12000
const EXTENDED_RESPONSE_WAIT_MSEC := 30000


func _ready() -> void:
	SignalBus.chat_opened.connect(show)
	SignalBus.chat_opened.connect(chat_panel.show)
	SignalBus.chat_opened.connect(quiz_panel.hide)
	SignalBus.chat_opened.connect(chat_input_field.grab_focus)
	SignalBus.chat_closed.connect(hide)
	set_process(true) # does nothing?
	_reset_chat_session()


func _process(_delta: float) -> void:
	if not socket_started:
		if awaiting_response and Time.get_ticks_msec() > response_deadline_msec:
			if not waiting_notice_sent:
				waiting_notice_sent = true
				response_deadline_msec = Time.get_ticks_msec() + EXTENDED_RESPONSE_WAIT_MSEC
				add_bubble("Hold on, let me think for a moment...", "left")
			else:
				awaiting_response = false
				waiting_notice_sent = false
				add_bubble("Sorry, I zoned out. Can you say that again?", "left")
		return

	chat_socket.poll()
	var state := chat_socket.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		_flush_pending_messages()
		_read_socket_packets()
	elif state == WebSocketPeer.STATE_CLOSED:
		if awaiting_response:
			awaiting_response = false
			add_bubble("[NPC connection closed unexpectedly.]", "left")
		socket_started = false

	if awaiting_response and Time.get_ticks_msec() > response_deadline_msec:
		if not waiting_notice_sent:
			waiting_notice_sent = true
			response_deadline_msec = Time.get_ticks_msec() + EXTENDED_RESPONSE_WAIT_MSEC
			add_bubble("Hold on, let me think for a moment...", "left")
		else:
			awaiting_response = false
			waiting_notice_sent = false
			add_bubble("Sorry, I zoned out. Can you say that again?", "left")
	
	
func close_menu():
	hide()
	SignalBus.chat_closed.emit()


func _reset_chat_session() -> void:
	chat_session_id = "%s-%s" % [str(multiplayer.get_unique_id()), str(Time.get_unix_time_from_system())]


func _connect_chat_socket() -> void:
	if socket_started and chat_socket.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		print("WebSocket already started, skipping reconnect")
		return

	chat_socket = WebSocketPeer.new()
	print("Attempting WebSocket connection to: ", Env.CHAT_STREAM_URL)
	var connection_error := chat_socket.connect_to_url(Env.CHAT_STREAM_URL)
	if connection_error != OK:
		socket_started = false
		print("WebSocket connection error: ", connection_error)
		add_bubble("[Could not reach NPC chat server.]", "left")
		return

	socket_started = true
	print("WebSocket connection initiated, state: ", chat_socket.get_ready_state())


func add_bubble(text: String, side):
	_make_bubble(text, side)


func _make_bubble(text: String, side: String) -> Control:
	var chat_bubble_instance = chat_bubble.instantiate()
	chat_bubble_instance.get_node("BubbleText").text = text
	#region garbage magic number resizing circus
	var bubble_min_size = Vector2(clamp(len(text)*10, 80, 400), 37)
	chat_bubble_instance.set_custom_minimum_size(bubble_min_size)
	#endregion
	if side == "left":
		chat_bubble_instance.set_h_size_flags(Control.SizeFlags.SIZE_SHRINK_BEGIN)
	else:
		chat_bubble_instance.set_h_size_flags(Control.SizeFlags.SIZE_SHRINK_END)
	chat_container.add_child(chat_bubble_instance)
	call_deferred("_ensure_visible", chat_bubble_instance)
	return chat_bubble_instance


func _ensure_visible(control: Control) -> void:
	chat_scroll_container.ensure_control_visible(control)


func submit_input(input_text):
	input_text = input_text.strip_edges()
	if input_text == "":
		return

	chat_input_field.set_text("")
	add_bubble(input_text, "right")
	_connect_chat_socket()
	if not socket_started:
		return

	if chat_session_id == "":
		_reset_chat_session()

	var student_name := _get_local_student_name()
	var data_to_send = {
		"type": "client_message",
		"session_id": chat_session_id,
		"npc_id": Env.CURRENT_CHAT_NPC_ID,
		"player_id": student_name,
		"text": input_text,
	}

	pending_messages.append(JSON.stringify(data_to_send))
	awaiting_response = true
	waiting_notice_sent = false
	response_deadline_msec = Time.get_ticks_msec() + FIRST_RESPONSE_WAIT_MSEC


func _get_local_student_name() -> String:
	for player in get_tree().get_nodes_in_group("players"):
		if int(player.name) == multiplayer.get_unique_id():
			return player.username
	return "unknown-player"


func _flush_pending_messages() -> void:
	if chat_socket.get_ready_state() != WebSocketPeer.STATE_OPEN:
		print("WebSocket not open yet, state: ", chat_socket.get_ready_state())
		return
	while pending_messages.size() > 0:
		var msg = pending_messages.pop_front()
		print("Sending message: ", msg)
		chat_socket.send_text(msg)


func _read_socket_packets() -> void:
	while chat_socket.get_available_packet_count() > 0:
		var body_text := chat_socket.get_packet().get_string_from_utf8()
		print("Received packet: ", body_text)
		_handle_socket_event(body_text)


func _handle_socket_event(body_text: String) -> void:
	var response_data = JSON.parse_string(body_text)
	if typeof(response_data) != TYPE_DICTIONARY:
		return

	var event_type := str(response_data.get("type", ""))
	match event_type:
		"typing_token":
			awaiting_response = false
			waiting_notice_sent = false
			_append_stream_token(str(response_data.get("text", "")))
		"assistant_message_done":
			awaiting_response = false
			waiting_notice_sent = false
			active_stream_bubble = null
		"task_started", "task_progress":
			awaiting_response = false
			waiting_notice_sent = false
			active_stream_bubble = null
			var message = str(response_data.get("message", ""))
			if message != "":
				add_bubble(message, "left")
		"quiz_ready":
			awaiting_response = false
			waiting_notice_sent = false
			active_stream_bubble = null
			_open_quiz_payload(response_data)
		"error":
			awaiting_response = false
			waiting_notice_sent = false
			active_stream_bubble = null
			add_bubble("NPC error: " + str(response_data.get("message", "Unknown error.")), "left")
		_:
			pass


func _append_stream_token(token: String) -> void:
	if active_stream_bubble == null:
		active_stream_bubble = _make_bubble("", "left")

	var bubble_text = active_stream_bubble.get_node("BubbleText")
	bubble_text.text += token
	active_stream_bubble.set_custom_minimum_size(
		Vector2(clamp(len(bubble_text.text) * 10, 80, 400), 37)
	)
	call_deferred("_ensure_visible", active_stream_bubble)


func _open_quiz_payload(response_data: Dictionary) -> void:
	if not response_data.has("quiz"):
		add_bubble("I could not parse the quiz payload.", "left")
		return

	chat_input_field.editable = false
	chat_panel.hide()
	chat_input_field.editable = true
	for child in quiz_container.get_children():
		child.queue_free()
	quiz_panel.show()

	var quiz = response_data["quiz"]
	quiz_title.text = quiz["quiz_title"]
	var questions = quiz["questions"]
	for question in questions:
		var question_instance = quiz_question.instantiate()
		quiz_container.add_child(question_instance)
		question_instance.fill_out_question(
			question["question"],
			question["options"],
			question["answer"]
		)


func add_debug_reply():
	await get_tree().create_timer(1).timeout
	var musketeerism = "\"Great criminals bear about them a kind of predestination which makes them surmount all obstacles, which makes them escape all dangers, up to the moment which a wearied Providence has marked as the rock of their impious fortunes.\""
	add_bubble(musketeerism, "left")


func _on_chat_submit_button_pressed() -> void:
	submit_input(chat_input_field.get_text())
	chat_input_field.grab_focus()


func _on_chat_input_field_text_submitted(new_text: String) -> void:
	submit_input(new_text)


func _on_quiz_close_button_pressed() -> void:
	quiz_panel.hide()
	chat_panel.show()


func _on_quiz_submit_button_pressed() -> void:
	var student_name : String
	# this shows i should have the local player saved as a global variable somewhere
	for player in get_tree().get_nodes_in_group("players"):
		if int(player.name) == multiplayer.get_unique_id():
			student_name = player.username
	var total_questions = 0
	var score = 0 
	for child in quiz_container.get_children():
		total_questions += 1
		if child.check_answer(): # has (desired) visual side effects 
			score += 1
	#region http
	var data_to_send = {
		"student_name" : student_name,
		"quiz_title" : quiz_title.text,
		"score" : score,
		"total_questions" : total_questions
	}
	var json_string = JSON.stringify(data_to_send)
	print("Submitting quiz results: " + json_string)
	var http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(self._quiz_submit_request_completed)
	var url = Env.SCORE_SERVER_URL
	var custom_headers = PackedStringArray(["Content-Type: application/json"])
	var method = HTTPClient.Method.METHOD_POST
	# sanitizer? i hardly know 'er
	var data = json_string
	http_request.request(url, custom_headers, method, data)
	#endregion


func _quiz_submit_request_completed(result, response_code, _headers, body):
	print("Quiz submission HTTP request completed: ", str(result), " ", str(response_code))
	# Here we could do something with the response body, e.g. print something
	# to the chat with add_bubble()
	print(body)
	
