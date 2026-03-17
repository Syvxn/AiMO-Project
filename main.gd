extends Node


func _ready() -> void:
	multiplayer.connected_to_server.connect(print.bind("Connected to server (as client)"))
	multiplayer.connected_to_server.connect($DebugMenu.show_sub_menu.bind("TEACHERSTUDENT"))
	SignalBus.player_info_received.connect(request_spawn_from_server)
	
	if OS.has_feature("dedicated_server"):
		NetworkHandler.start_server()
	elif OS.has_feature("web"):
		NetworkHandler.start_client()
	else:
		$DebugMenu.show_sub_menu("SERVERCLIENT")


# called only on clients, requesting that server add their player to the game
func request_spawn_from_server(username: String, role: String):
	assert(not multiplayer.is_server(), "spawn requested by server somehow what the hell")
	print("Requesting spawn as: ", username, ", ", role)
	add_player_and_personal_room.rpc_id(1, [username, role, multiplayer.get_unique_id()])


# called only on server, by clients.
# also i apologize -robin.
@rpc("any_peer")
func add_player_and_personal_room(player_info: Array):
	assert(multiplayer.is_server(), "add_player() somehow called from client what the hell")
	var username = player_info[0]
	var role = player_info[1]
	var player_peer_id = player_info[2]
	print("I'm the server, and I'm gonna add ", username, " as a ", role)
	#region  our house in the middle of our house
	var plot_marker : Marker2D
	for child in $MultiplayerSpawner/GameWorld/PersonalRoomPlotMarkers.get_children():
		if child.plot_available:
			child.plot_available = false
			child.inhabitant_username = username
			child.inhabitant_peer_id = player_peer_id
			plot_marker = child
			break
	if plot_marker == null:
		print("damn, no space somehow")
		return
	var personal_room_instance = load("res://rooms/personal_room.tscn").instantiate()
	personal_room_instance.name = "PROOM-" + str(player_peer_id)
	personal_room_instance.set_global_position(plot_marker.get_global_position())
	$MultiplayerSpawner/GameWorld.call_deferred("add_child", personal_room_instance)
	print("Personal room " + personal_room_instance.name + " has spawned for ", username)
	#endregion
	#region  okay adding the player character this time
	var player_instance = load("res://player/player.tscn").instantiate()
	# this was a clever trick to easily ferry the id when synching between peers
	player_instance.name = str(player_peer_id)
	player_instance.set_global_position(personal_room_instance.get_node("SpawnPoint").get_global_position())
	$MultiplayerSpawner/GameWorld.call_deferred("add_child", player_instance)
	print("Player " + str(player_peer_id) + " (" + username + ") " + " has spawned")
	#endregion


func remove_personal_room():
	# done only when player disconnects
	pass


func add_public_room():
	#prolly just spawn the fucken thing right at (0,0)
	pass


func remove_public_room():
	#when we're done with it i dunno?
	#there should probably be a seprate lobby that's always loaded
	pass


func join_room():
	pass
