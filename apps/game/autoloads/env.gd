extends Node

# read from json file, but pretend they're constants i guess
var GAME_SERVER_URL : String = "ws://localhost:8910"
var GAME_SERVER_PORT : int = 8910
#var MAX_GAME_CLIENTS : int  # not used yet
var CHAT_SERVER_URL : String = "http://127.0.0.1:8000/chat"
var SCORE_SERVER_URL : String = "http://127.0.0.1:8000/score"



func _ready() -> void:
	var file = FileAccess.open("res://.env.json", FileAccess.READ)
	if file == null:
		# Keep defaults when .env.json is not present in exported builds.
		return

	var json = JSON.new()
	var error = json.parse(file.get_as_text())
	if error == OK:
		if json.data.has("GAME_SERVER_URL"):
			GAME_SERVER_URL = json.data["GAME_SERVER_URL"]
		if json.data.has("GAME_SERVER_PORT"):
			GAME_SERVER_PORT = json.data["GAME_SERVER_PORT"]
		#MAX_GAME_CLIENTS = json.data["MAX_GAME_CLIENTS"]
		if json.data.has("CHAT_SERVER_URL"):
			CHAT_SERVER_URL = json.data["CHAT_SERVER_URL"]
		if json.data.has("SCORE_SERVER_URL"):
			SCORE_SERVER_URL = json.data["SCORE_SERVER_URL"]
		
