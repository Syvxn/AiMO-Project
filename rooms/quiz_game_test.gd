extends Node2D

var display_name := "Quiz Game"
var game_state := "inactive"
var players : Array[CharacterBody2D]
var team_a_players : Array[CharacterBody2D]
var team_b_players : Array[CharacterBody2D]
var total_points = {"team_a" : 0, "team_b" : 0}
var current_question_points = {"team_a" : 0, "team_b" : 0}
var quiz : Dictionary
var current_question_index := 0

@export var question_time_in_s := 10
@export var reward_time_in_s := 5


func _ready() -> void:
	%QuizMenu.hide()
	SignalBus.oops_pressed.connect(request_start_game_from_server)


func request_start_game_from_server():
	start_game.rpc_id(1)


@rpc("any_peer", "call_remote")
func start_game():
	assert(multiplayer.is_server())
	game_state = "preparing"
	players = get_players_present()
	# generate quiz
	#region cheating
	var file = FileAccess.open("res://misc/test_quiz.json", FileAccess.READ)
	var json = JSON.new()
	json.parse(file.get_as_text())
	quiz = json.data
	#endregion
	make_teams()
	for player in team_a_players:
		player.global_position = %SpawnPointA.global_position
	for player in team_b_players:
		player.global_position = %SpawnPointB.global_position
	game_state = "active"
	run_next_question()
	pass


func get_players_present() -> Array[CharacterBody2D]:
	var players_here : Array[CharacterBody2D]
	for body in %EjectionArea.get_overlapping_bodies():
		if body.is_in_group("players"):
			players_here.append(body)
	print(players_here)
	return players_here


func make_teams() -> void:
	players.shuffle()
	var n = 0
	for player in players:
		if n % 2 == 0:
			team_a_players.append(player)
		else:
			team_b_players.append(player)
		n += 1
	print("Team A: ", team_a_players)
	print("Team B: ", team_b_players)


func run_next_question():
	if current_question_index == len(quiz["questions"]):
		print("end of quiz, yay")
		for player in players:
			player.global_position = %SpawnPoint.global_position
			await get_tree().create_timer(0.1).timeout
		team_a_players.clear()
		team_b_players.clear()
		for key in total_points:
			total_points[key] = 0
		for key in current_question_points:
			current_question_points[key] = 0
		game_state = "inactive"
		return
	for key in current_question_points:
		current_question_points[key] = 0
	var question = quiz["questions"][current_question_index]
	fill_and_activate_question.rpc([question])
	%QuizMenu.show()
	await get_tree().create_timer(question_time_in_s).timeout
	%QuizMenu.hide()
	# check current question points
	# reward winner (and throw comedic junk at losers?)
	if current_question_points["team_a"] > current_question_points["team_b"]:
		print("Team A wins this one!")
	elif current_question_points["team_b"] > current_question_points["team_a"]:
		print("Team B wins this one!")
	else:
		print("It's a tie!")
	print("here's where stuff would fly out at the teams")
	await get_tree().create_timer(reward_time_in_s).timeout
	current_question_index += 1
	run_next_question()


@rpc("authority","call_local")
func fill_and_activate_question(args: Array):
	var question = args[0]
	%QuizQuestion.fill_out_question(question["question"], question["options"], question["answer"])
	if not %QuizQuestion.item_list.item_selected.is_connected(on_answer_first_selected):
		%QuizQuestion.item_list.item_selected.connect(on_answer_first_selected)
	


@rpc("any_peer", "call_remote")
func give_team_point_by_player(args: Array):
	var id = args[0]
	assert(multiplayer.is_server())
	var team = ""
	if team_a_players.any(func(player): return int(player.name) == id):
		team = "team_a"
	elif team_b_players.any(func(player): return int(player.name) == id):
		team = "team_b"
	if not team == "":
		current_question_points[team] += 1
		total_points[team] += 1


func on_answer_first_selected(index: int):
	%QuizQuestion.item_list.item_selected.disconnect(on_answer_first_selected)
	if %QuizQuestion.check_answer():
		give_team_point_by_player.rpc_id(1, [multiplayer.get_unique_id()])
	
	
	
	
	
