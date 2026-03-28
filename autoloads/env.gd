extends Node

# read from json file, but pretend they're constants i guess
var GAME_SERVER_URL : String
var GAME_SERVER_PORT : int
var MAX_GAME_CLIENTS : int    # not used yet
var CHAT_SERVER_URL : String
#var CHAT_SERVER_PORT : int


func _ready() -> void:
	var file = FileAccess.open("res://.env.json", FileAccess.READ)
	var json = JSON.new()
	var error = json.parse(file.get_as_text())
	if error == OK:
		GAME_SERVER_URL = json.data["GAME_SERVER_URL"]
		GAME_SERVER_PORT = json.data["GAME_SERVER_PORT"]
		MAX_GAME_CLIENTS = json.data["MAX_GAME_CLIENTS"]
		CHAT_SERVER_URL = json.data["CHAT_SERVER_URL"]
		#CHAT_SERVER_PORT = json.data["CHAT_SERVER_PORT"]
		
