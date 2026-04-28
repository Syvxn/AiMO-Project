extends Node2D

var display_name := "Quiz Game"
var game_state := "inactive"
var players : Array[CharacterBody2D]
var team_a_players : Array[CharacterBody2D]
var team_b_players : Array[CharacterBody2D]
var total_points = {"team_a" : 0, "team_b" : 0}
var current_question_points = {"team_a" : 0, "team_b" : 0}
var quiz : Dictionary
var questions_in_quiz := 0

@export var question_time_in_s := 10
@export var reward_time_in_s := 10



func _ready() -> void:
	%QuestionTimer.wait_time = question_time_in_s
	%RewardTimer.wait_time = reward_time_in_s


func start_game():
	# set game state to preparing
	# get list of players here (and prevent leaving?)
	# generate quiz
	# put players in teams and team areas (empty teams first)
	# set game state to active
	pass


func get_players_present() -> Array[CharacterBody2D]:
	var players_here = []
	for body in %EjectionArea.get_overlapping_bodies():
		if body.is_in_grop("players"):
			players_here.append(body)
	print(players_here)
	return players_here


func run_question():
	# if no questions left:
		# go to final rewards
		# set game state to inactive
		# return
	# pull next question from quiz
	# show question panel
	# await question timer
	# check cureent question points
	# reward winner (and throw comedic junk at losers?)
	# await reward timer
	# call self
	pass
