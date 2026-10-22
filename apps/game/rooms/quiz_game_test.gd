extends Node2D

var display_name := "Quiz Game"
var game_state := "inactive"
var points_per_question := 1
var points_per_snack := 1
var players : Array[CharacterBody2D]
var team_a_players : Array[CharacterBody2D]
var team_b_players : Array[CharacterBody2D]
var client_team := ""
var id_for_autolooters := "quizgametest"
var total_points = {"team_a" : 0, "team_b" : 0}
var current_question_points = {"team_a" : 0, "team_b" : 0}
var current_question_players_answered_count = 0
var quiz : Dictionary
var current_question_index := 0
var quiz_request: HTTPRequest
var quiz_request_pending := false
var quiz_request_kind := ""

@export var conveyor_base_speed := 40.0
@export var conveyor_speed_increment := 10.0
@export var question_time_in_s := 10
@export var reward_time_in_s := 5

@onready var chapter_picker = %ChapterPicker
@onready var chapter_option_button = %ChapterOptions


func _ready() -> void:
	%QuizMenu.hide()
	%GameHUD.hide()
	%ChapterPicker.hide()
	%QuizStatusLabel.hide()
	SignalBus.item_autolooted.connect(_on_item_autlooted)
	quiz_request = HTTPRequest.new()
	quiz_request.timeout = 240.0
	quiz_request.request_completed.connect(_on_quiz_request_completed)
	add_child(quiz_request)
	set_conveyor_speeds(0.0)


func _physics_process(_delta: float) -> void:
	if not client_team == "":
		%PointsLabel.text = str(total_points[client_team])


#region client functionality
# implicitly client-side since no-one to push button on server
func _on_activate_button_pushed(_id: String) -> void:
	if game_state == "inactive" and not quiz_request_pending:
		request_start_game_from_server()

# rpc_id(1) means we're calling that function on the server
func request_start_game_from_server():
	if OS.has_feature("web"):
		request_class_quiz()
		return
	var file = FileAccess.open("res://misc/musketeers_quiz.json", FileAccess.READ)
	if file == null:
		_show_quiz_status("Could not load the test quiz.")
		return
	var json = JSON.new()
	if json.parse(file.get_as_text()) != OK or not _is_valid_quiz(json.data):
		_show_quiz_status("The test quiz is invalid.")
		return
	start_game.rpc_id(1, [json.data])


func _show_quiz_status(message: String) -> void:
	%GameHUD.show()
	%CenterLabel.hide()
	%QuizStatusLabel.text = message
	%QuizStatusLabel.show()


func request_class_quiz() -> void:
	quiz_request_pending = true
	var token := _get_game_access_token()
	if token.is_empty():
		quiz_request_pending = false
		_show_quiz_status("Sign in on the website and reopen the game to start a class quiz.")
		return
	var host = str(JavaScriptBridge.eval("window.location.host"))
	var protocol = str(JavaScriptBridge.eval("window.location.protocol"))
	var http_scheme = "https" if protocol == "https:" else "http"
	var url = "%s://%s/api/quiz/game/chapters" % [http_scheme, host]
	var headers = PackedStringArray([
		"Content-Type: application/json",
		"Authorization: Bearer %s" % token,
	])
	quiz_request_kind = "chapters"
	_show_quiz_status("Loading chapters...")
	var error = quiz_request.request(url, headers, HTTPClient.METHOD_GET)
	if error != OK:
		quiz_request_pending = false
		quiz_request_kind = ""
		_show_quiz_status("Could not contact the quiz service. Please try again.")


func _get_game_access_token() -> String:
	for cookie_string in JavaScriptBridge.eval("document.cookie").split("; "):
		var cookie_parts = cookie_string.split("=", true, 1)
		if cookie_parts.size() == 2 and cookie_parts[0] == "aimo_token":
			return cookie_parts[1]
	return ""


func _on_quiz_request_completed(
	_result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray,
) -> void:
	if quiz_request_kind == "chapters":
		if response_code < 200 or response_code >= 300:
			quiz_request_pending = false
			quiz_request_kind = ""
			_show_quiz_error(body, "Could not load chapters from your teacher's materials.")
			return
		var chapters_response = JSON.parse_string(body.get_string_from_utf8())
		if typeof(chapters_response) != TYPE_DICTIONARY or typeof(chapters_response.get("chapters", [])) != TYPE_ARRAY:
			quiz_request_pending = false
			quiz_request_kind = ""
			_show_quiz_status("The chapter service returned invalid data.")
			return
		chapter_option_button.clear()
		for chapter in chapters_response["chapters"]:
			if typeof(chapter) != TYPE_DICTIONARY or not chapter.has("chapter_id") or not chapter.has("title"):
				continue
			# short label for game UI
			var short_label = (
				"%s — %s" % [chapter["title"], chapter.get("material_title", "Textbook"),]
			).substr(0, 53) + "..."
			chapter_option_button.add_item(short_label)
			# old type label for requests
			var chapter_label = "%s — %s" % [chapter.get("material_title", "Textbook"), chapter["title"]]
			var metadata = {
				"chapter_id": chapter["chapter_id"],
				"chapter_label": chapter_label
			}
			chapter_option_button.set_item_metadata(chapter_option_button.item_count - 1, metadata)
		if chapter_option_button.item_count == 0:
			quiz_request_pending = false
			quiz_request_kind = ""
			_show_quiz_status("No readable chapters were found in your teacher's materials.")
			return
		%QuizStatusLabel.hide()
		chapter_picker.show()
		return

	quiz_request_pending = false
	quiz_request_kind = ""
	if response_code < 200 or response_code >= 300:
		_show_quiz_error(body, "Could not prepare a class quiz. Check your class and teacher materials.")
		return
	var response_data = JSON.parse_string(body.get_string_from_utf8())
	if typeof(response_data) != TYPE_DICTIONARY or not _is_valid_quiz(response_data.get("quiz", {})):
		_show_quiz_status("The quiz service returned an invalid quiz.")
		return
	%QuizStatusLabel.hide()
	%CenterLabel.show()
	%CenterLabel.text = ""
	start_game.rpc_id(1, [response_data["quiz"]])


func _show_quiz_error(body: PackedByteArray, fallback: String) -> void:
	var error_data = JSON.parse_string(body.get_string_from_utf8())
	var message = fallback
	if typeof(error_data) == TYPE_DICTIONARY:
		message = str(error_data.get("detail", message))
	_show_quiz_status(message)


func _on_chapter_quiz_pressed() -> void:
	if chapter_option_button.item_count == 0:
		return
	var chapter_index = chapter_option_button.selected
	var chapter_id = str(chapter_option_button.get_item_metadata(chapter_index)["chapter_id"])
	if chapter_id.is_empty():
		_show_quiz_status("Select a chapter to continue.")
		return
	var chapter_label = chapter_option_button.get_item_metadata(chapter_index)["chapter_label"]
	chapter_picker.hide()
	var host = str(JavaScriptBridge.eval("window.location.host"))
	var protocol = str(JavaScriptBridge.eval("window.location.protocol"))
	var http_scheme = "https" if protocol == "https:" else "http"
	var url = "%s://%s/api/quiz/game/generate" % [http_scheme, host]
	var headers = PackedStringArray([
		"Content-Type: application/json",
		"Authorization: Bearer %s" % _get_game_access_token(),
	])
	var body = JSON.stringify({
		"topic": chapter_label,
		"chapter_id": chapter_id,
		"question_count": 3,
	})
	quiz_request_kind = "quiz"
	_show_quiz_status("Preparing your quiz from: \n%s" % chapter_label)
	var error = quiz_request.request(url, headers, HTTPClient.METHOD_POST, body)
	if error != OK:
		quiz_request_pending = false
		quiz_request_kind = ""
		_show_quiz_status("Could not contact the quiz service. Please try again.")


func _on_chapter_picker_cancelled() -> void:
	chapter_picker.hide()
	quiz_request_pending = false
	quiz_request_kind = ""
	%GameHUD.hide()


func _is_valid_quiz(quiz_data: Variant) -> bool:
	if typeof(quiz_data) != TYPE_DICTIONARY:
		return false
	if not quiz_data.get("quiz_title", "") is String:
		return false
	var questions = quiz_data.get("questions", [])
	if typeof(questions) != TYPE_ARRAY or questions.is_empty():
		return false
	for question in questions:
		if typeof(question) != TYPE_DICTIONARY:
			return false
		if not question.get("question", "") is String:
			return false
		var options = question.get("options", [])
		if typeof(options) != TYPE_ARRAY or options.size() < 2 or options.size() > 4:
			return false
		if question.get("answer", "") not in ["A", "B", "C", "D"]:
			return false
	return true

# also called on server for debugging purposes
@rpc("authority","call_local")
func fill_and_activate_question(args: Array):
	var question = args[0]
	%QuizQuestion.fill_out_question(question["question"], question["options"], question["answer"])
	if not %QuizQuestion.item_list.item_selected.is_connected(on_answer_first_selected):
		%QuizQuestion.item_list.item_selected.connect(on_answer_first_selected)

# reusing existing quiz functionality 
func on_answer_first_selected(_index: int):
	%QuizQuestion.item_list.item_selected.disconnect(on_answer_first_selected)
	if %QuizQuestion.check_answer(false):
		give_team_point_by_player.rpc_id(1, [multiplayer.get_unique_id()])
	count_answer.rpc_id(1)

# lmao
@rpc("authority", "call_local")
func show_correct_answer():
	%QuizQuestion.show_correct_answer()


# also called on server for debugging purposes
@rpc("authority", "call_local")
func clear_rewards():
	for child in %SnacksSpawner.get_children():
		child.queue_free()
#endregion


#region server functionality
@rpc("any_peer", "call_remote")
func start_game(args: Array):
	assert(multiplayer.is_server())
	if game_state != "inactive" or args.is_empty() or not _is_valid_quiz(args[0]):
		return
	var sender_id = multiplayer.get_remote_sender_id()
	if not get_players_present().any(func(player): return int(player.name) == sender_id):
		return
	game_state = "preparing"
	%CenterLabel.text = ""
	# do this kind of stuff with signals?
	for cannon in %CannonsA.get_children():
		cannon.get_node("SyncLight").show()
	for cannon in %CannonsB.get_children():
		cannon.get_node("SyncLight").show()
	quiz = args[0]
	clear_rewards.rpc()
	players = get_players_present() # no state like real estate
	for player in players:
		var quiz_auto_looter_instance = load("res://misc/auto_looter.tscn").instantiate()
		quiz_auto_looter_instance.name = "QuizAutoLooter"
		player.add_child(quiz_auto_looter_instance)
		player.get_node("QuizAutoLooter").configure(20.0, id_for_autolooters, "snack", player)
		show_hud.rpc_id(int(player.name))
	make_teams()
	for player in players:
		var team_name : String
		var spawn_side : Vector2
		if player in team_a_players:
			team_name = "team_a"
			spawn_side = %SpawnPointA.global_position
		elif player in team_b_players:
			team_name = "team_b"
			spawn_side = %SpawnPointB.global_position
		else:
			continue
		tell_client_team.rpc_id(int(player.name), [team_name])
		# lambda so the 0.5 sec beam up wait happens async hopefully
		var lambda = func():
			player.beam_up.rpc()
			player.global_position = spawn_side
			await get_tree().create_timer(0.5).timeout
			player.beam_down.rpc()
		lambda.call()
		# to avoid glitching when players moved to exact same coords
		await get_tree().create_timer(0.1).timeout
	await get_tree().create_timer(1).timeout
	game_state = "active"
	show_countdown.rpc()
	await get_tree().create_timer(3).timeout
	for cannon in %CannonsA.get_children():
		cannon.get_node("SyncLight").hide()
	for cannon in %CannonsB.get_children():
		cannon.get_node("SyncLight").hide()
	run_next_question()


func get_players_present() -> Array[CharacterBody2D]:
	assert(multiplayer.is_server())
	var players_here : Array[CharacterBody2D]
	for body in %EjectionArea.get_overlapping_bodies():
		if body.is_in_group("players"):
			players_here.append(body)
	print(players_here)
	return players_here


func make_teams() -> void:
	assert(multiplayer.is_server())
	players.shuffle()
	for i in range(len(players)):
		if i % 2 == 0:
			team_a_players.append(players[i])
		else:
			team_b_players.append(players[i])
	print("Team A: ", team_a_players)
	print("Team B: ", team_b_players)


@rpc("authority", "call_remote")
func tell_client_team(args: Array):
	client_team = args[0]


@rpc("authority", "call_local")
func show_countdown():
	%CenterLabel.text = "3"
	await get_tree().create_timer(1).timeout
	%CenterLabel.text = "2"
	await get_tree().create_timer(1).timeout
	%CenterLabel.text = "1"
	await get_tree().create_timer(1).timeout
	%CenterLabel.text = ""


func run_next_question():
	assert(multiplayer.is_server())
	for key in current_question_points:
		current_question_points[key] = 0
	current_question_players_answered_count = 0
	if current_question_index == len(quiz["questions"]):
		end_game()
		return
	set_conveyor_speeds(0.0)
	var question = quiz["questions"][current_question_index]
	fill_and_activate_question.rpc([question])
	for player in players:
		show_quiz.rpc_id(int(player.name))
	#$QuestionTimer.start(question_time_in_s)
	$QuestionTimer.start(randf_range(4.0, 7.0))
	await $QuestionTimer.timeout
	show_correct_answer.rpc()
	await get_tree().create_timer(1.5).timeout
	for player in players:
		hide_quiz.rpc_id(int(player.name))
	var c_speed = conveyor_base_speed + (conveyor_speed_increment * current_question_index)
	set_conveyor_speeds(c_speed, true)
	check_and_reward_winners()
	await get_tree().create_timer(reward_time_in_s).timeout
	current_question_index += 1
	run_next_question()


@rpc("authority", "call_remote")
func show_quiz():
	%QuizMenu.show()
@rpc("authority", "call_remote")
func hide_quiz():
	%QuizMenu.hide()
@rpc("authority", "call_remote")
func show_hud():
	%GameHUD.show()
@rpc("authority", "call_remote")
func hide_hud():
	%GameHUD.hide()



func end_game():
		assert(multiplayer.is_server())
		print("end of quiz, yay")
		await get_tree().create_timer(2.0).timeout
		set_conveyor_speeds(0.0)
		current_question_index = 0
		print("Team A points: ", str(total_points["team_a"]))
		print("Team B points: ", str(total_points["team_b"]))
		if total_points["team_a"] == total_points["team_b"]:
			%CenterLabel.say_for_secs.rpc(["Draw", 2.0])
		else:
			var winners
			var losers
			if total_points["team_a"] > total_points["team_b"]:
				winners = team_a_players
				losers = team_b_players
			else:
				winners = team_b_players
				losers = team_a_players
			for player in winners:
				%CenterLabel.say_for_secs.rpc_id(int(player.name), ["You Win!", 2.0])
			for player in losers:
				%CenterLabel.say_for_secs.rpc_id(int(player.name), ["You Lose!", 2.0])
		for child in %SnacksSpawner.get_children():
			child.call_deferred("queue_free")
		for player in players:
			if not player:
				continue
			tell_client_team.rpc_id(int(player.name), [""])
			var qal = player.get_node_or_null("QuizAutoLooter")
			if qal:
				qal.queue_free()
			player.global_position = %SpawnPoint.global_position
			await get_tree().create_timer(0.1).timeout
		team_a_players.clear()
		team_b_players.clear()
		for key in total_points:
			total_points[key] = 0
		game_state = "inactive"
		await get_tree().create_timer(4.0).timeout
		for player in players:
			hide_hud.rpc_id(int(player.name))
		print("game ended successfully")


func set_conveyor_speeds(speed: float, randomize_direction=false):
	for child in %Conveyors.get_children():
		var dir_mod = 1.0
		if randomize_direction:
			dir_mod = [-1.0, 1.0].pick_random()
		child.get_node("Area").speed = speed * dir_mod
		for segment in child.get_node("Segments").get_children():
			if dir_mod < 0.0:
				segment.play("move_up", (speed / conveyor_base_speed))
			else:
				segment.play("move_down", (speed / conveyor_base_speed))


func check_and_reward_winners():
	var reward_a = true
	var reward_b = true
	if current_question_points["team_a"] > current_question_points["team_b"]:
		reward_b = false
	elif current_question_points["team_b"] > current_question_points["team_a"]:
		reward_a = false
	%CenterLabel.say_for_secs.rpc(["Go!", 1.0])
	var cannons_a = %CannonsA.get_children()
	var cannons_b = %CannonsB.get_children()
	# TODO: replace this conditional with something a little more elegant
	if reward_a and reward_b:
		for i in range(4):
			var cannon_a = cannons_a.pick_random()
			var cannon_b = cannons_b.pick_random()
			spew_stuff(cannon_a, cannon_a.get_node("Target").global_position, "snacks")
			spew_stuff(cannon_b, cannon_b.get_node("Target").global_position, "snacks")
	else:
		var cannon_w
		var cannon_l
		for i in range(4):
			if reward_a:
				cannon_w = cannons_a.pick_random()
				cannon_l = cannons_b.pick_random()
			else:
				cannon_w = cannons_b.pick_random()
				cannon_l = cannons_a.pick_random()
			if i % 2 == 0:
				spew_stuff(cannon_l, cannon_l.get_node("Target").global_position, "snacks")
			spew_stuff(cannon_w, cannon_w.get_node("Target").global_position, "snacks")


func spew_stuff(reward_point_node, target_position, type):
	assert(multiplayer.is_server())
	var light = reward_point_node.get_node_or_null("SyncLight")
	if light:
		light.show()
		await get_tree().create_timer(2.0).timeout
		light.hide()
	var types = {
		"snacks" : "res://items/physics_props/random_snack.tscn",
	}
	var stuff = load(types[type])
	for i in range(20):
		var stuff_instance = stuff.instantiate()
		stuff_instance.global_position = reward_point_node.global_position
		if "lootable" in stuff_instance:
			stuff_instance.lootable = true
		%SnacksSpawner.add_child(stuff_instance, true)
		target_position.x += randi_range(-10, 10)
		target_position.y += randi_range(-10, 10)
		var impulse = stuff_instance.global_position.direction_to(target_position) * 500
		stuff_instance.apply_central_impulse(impulse)
		await get_tree().create_timer(0.1).timeout


@rpc("any_peer", "call_remote")
func give_team_point_by_player(args: Array):
	assert(multiplayer.is_server())
	var id = args[0]
	# no need to store anything in player
	if team_a_players.any(func(player): return int(player.name) == id):
		current_question_points["team_a"] += points_per_question
		#total_points["team_a"] += points_per_question
	elif team_b_players.any(func(player): return int(player.name) == id):
		current_question_points["team_b"] += points_per_question
		#total_points["team_b"] += points_per_question


@rpc("any_peer", "call_remote")
func count_answer() -> void:
	assert(multiplayer.is_server())
	current_question_players_answered_count += 1
	if current_question_players_answered_count == len(team_a_players) + len(team_b_players):
		print("Everybody answered")
		$QuestionTimer.start(1)


func _on_item_autlooted(autolooter_id: String, type: String, looter: Node):
	assert(multiplayer.is_server())
	if autolooter_id == id_for_autolooters and type == "snack":
		if team_a_players.any(func(player): return player.name == looter.name):
			total_points["team_a"] += points_per_snack
		if team_b_players.any(func(player): return player.name == looter.name):
			total_points["team_b"] += points_per_snack
#endregion


func _on_exception_timer_timeout() -> void:
	var exceptions = get_tree().get_nodes_in_group("vmw_exceptions")
	var exception = exceptions.pick_random()
	for i in range(randi_range(1, 3)):
		exception.hide()
		await get_tree().create_timer(randf_range(0.2, 0.9)).timeout
		exception.show()
	%ExceptionTimer.start(randf_range(1.0, 5.0))
