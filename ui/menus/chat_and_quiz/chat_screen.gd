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


func _ready() -> void:
	SignalBus.chat_opened.connect(show)
	SignalBus.chat_opened.connect(chat_panel.show)
	SignalBus.chat_opened.connect(quiz_panel.hide)
	SignalBus.chat_opened.connect(chat_input_field.grab_focus)
	SignalBus.chat_closed.connect(hide)
	
	


func add_bubble(text: String, side):
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
	await get_tree().process_frame
	chat_scroll_container.ensure_control_visible(chat_bubble_instance)


func submit_input(input_text):
	chat_input_field.set_text("")
	add_bubble(input_text, "right")
	#region http that should be moved to its own component
	var http_request = HTTPRequest.new()
	http_request.set_timeout(10.0)    # move this to .env.json?
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
	var body_text = body.get_string_from_utf8()
	# this is some hack shit; i gotta replace this with a proper check
	if not body_text.begins_with("{"):
		add_bubble(body_text, "left")
	else: # json, i assume?
		var quiz_data = JSON.parse_string(body_text)
		if not typeof(quiz_data) == TYPE_DICTIONARY:
			print(quiz_data)
			add_bubble("Sorry, I just got hit by a solar ray. You were saying?", "left")
			return
		add_bubble("Sure, here you go:", "left")
		chat_input_field.editable = false
		await get_tree().create_timer(0.7).timeout
		chat_panel.hide()
		chat_input_field.editable = true
		for child in quiz_container.get_children():
			child.queue_free()
		quiz_panel.show()
		quiz_title.text = quiz_data["quiz_title"]
		var questions = quiz_data["questions"]
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
	var data_to_send = {
		"student_name" : student_name,
		"quiz_title" : quiz_title.text,
		"score" : score,
		"total_questions" : total_questions
	}
	var json_string = JSON.stringify(data_to_send)
	#region send thhrough http here
	print(json_string)
	#endregion
	
	
	
	
