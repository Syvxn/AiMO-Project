extends Node


func _ready() -> void:
	multiplayer.connected_to_server.connect(print.bind("Connected to server"))
	multiplayer.connected_to_server.connect($DebugMenu.show_sub_menu.bind("TEACHERSTUDENT"))
	SignalBus.player_info_received.connect(request_spawn_from_server)
	
	if OS.has_feature("dedicated_server"):
		NetworkHandler.start_server()
	elif OS.has_feature("web"):
		NetworkHandler.start_client()
	else:
		$DebugMenu.show_sub_menu("SERVERCLIENT")
		
	
func request_spawn_from_server(username: String, role: String):
	print(username, ": ", role)
	

@rpc("any_peer")
func add_player(username: String, role: String):
	if not multiplayer.is_server():
		return
	
