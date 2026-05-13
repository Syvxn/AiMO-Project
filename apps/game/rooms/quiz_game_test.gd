extends Node2D

var display_name := "Quiz Game"
var game_state := "inactive"
var points_per_question := 1
var points_per_snack := 1
var players : Array[CharacterBody2D]
var team_a_players : Array[CharacterBody2D]
var team_b_players : Array[CharacterBody2D]
var id_for_autolooters = "quizgametest"
var total_points = {"team_a" : 0, "team_b" : 0}
var current_question_points = {"team_a" : 0, "team_b" : 0}
var current_question_players_answered_count = 0
var quiz : Dictionary
var current_question_index := 0

@export var conveyor_base_speed := 40.0
@export var conveyor_speed_increment := 10.0
@export var question_time_in_s := 10
@export var reward_time_in_s := 5


func _ready() -> void:
	%QuizMenu.hide()
	SignalBus.item_autolooted.connect(_on_item_autlooted)


func _physics_process(_delta: float) -> void:
	if multiplayer.is_server():
		%APoints.text = "A: " + str(total_points["team_a"])
		%BPoints.text = "B: " + str(total_points["team_b"])


#region client functionality
# implicitly client-side since no-one to push button on server
func _on_activate_button_pushed(_id: String) -> void:
	if game_state == "inactive":
		request_start_game_from_server()

# rpc_id(1) means we're calling that function on the server
func request_start_game_from_server():
	start_game.rpc_id(1)

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
func start_game():
	assert(multiplayer.is_server())
	game_state = "preparing"
	%ApparatusScreen.text = ""
	#region quiz generation
	# cheating with JSON file for testing
	var file = FileAccess.open("res://misc/test_quiz.json", FileAccess.READ)
	var json = JSON.new()
	json.parse(file.get_as_text())
	quiz = json.data
	#endregion
	clear_rewards.rpc()
	players = get_players_present() # no state like real estate
	for player in players:
		var quiz_auto_looter_instance = load("res://misc/auto_looter.tscn").instantiate()
		quiz_auto_looter_instance.name = "QuizAutoLooter"
		player.add_child(quiz_auto_looter_instance)
		player.get_node("QuizAutoLooter").configure(20.0, id_for_autolooters, "snack", player)
	make_teams()
	for player in team_a_players:
		player.global_position = %SpawnPointA.global_position
	for player in team_b_players:
		player.global_position = %SpawnPointB.global_position
	game_state = "active"
	await show_countdown()
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


func show_countdown():
	%ApparatusScreen.text = "3"
	await get_tree().create_timer(1).timeout
	%ApparatusScreen.text = "2"
	await get_tree().create_timer(1).timeout
	%ApparatusScreen.text = "1"
	await get_tree().create_timer(1).timeout


func run_next_question():
	assert(multiplayer.is_server())
	for key in current_question_points:
		current_question_points[key] = 0
	current_question_players_answered_count = 0
	if current_question_index == len(quiz["questions"]):
		end_game()
		return
	set_conveyor_speeds(0.0)
	%ApparatusScreen.text = "?"
	var question = quiz["questions"][current_question_index]
	fill_and_activate_question.rpc([question])
	%QuizMenu.show()
	$QuestionTimer.start(question_time_in_s)
	await $QuestionTimer.timeout
	show_correct_answer.rpc()
	await get_tree().create_timer(1.5).timeout
	%QuizMenu.hide()
	var c_speed = conveyor_base_speed + (conveyor_speed_increment * current_question_index)
	set_conveyor_speeds(c_speed, true)
	check_and_reward_winners()
	await get_tree().create_timer(reward_time_in_s).timeout
	current_question_index += 1
	run_next_question()


func end_game():
		assert(multiplayer.is_server())
		print("end of quiz, yay")
		set_conveyor_speeds(0.0)
		current_question_index = 0
		print("Team A points: ", str(total_points["team_a"]))
		print("Team B points: ", str(total_points["team_b"]))
		%ApparatusScreen.text = "A: %s\nB: %s" % [total_points["team_a"], total_points["team_b"]]
		for child in %SnacksSpawner.get_children():
			child.call_deferred("queue_free")
		for player in players:
			if not player:
				continue
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
	%ApparatusScreen.text = "GO"
	var cannons_a = %CannonsA.get_children()
	var cannons_b = %CannonsB.get_children()
	if reward_a:
		for i in range(4):
			var cannon = cannons_a.pick_random()
			spew_stuff(cannon, cannon.get_child(0).global_position, "snacks")
		for i in range(2):
			var cannon = cannons_b.pick_random()
			spew_stuff(cannon, cannon.get_child(0).global_position, "snacks")
	if reward_b:
		for i in range(4):
			var cannon = cannons_b.pick_random()
			spew_stuff(cannon, cannon.get_child(0).global_position, "snacks")
		for i in range(2):
			var cannon = cannons_a.pick_random()
			spew_stuff(cannon, cannon.get_child(0).global_position, "snacks")


func spew_stuff(reward_point_node, target_position, type):
	assert(multiplayer.is_server())
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
