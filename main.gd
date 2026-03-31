extends Node

var players_joined := 0



func _ready() -> void:
	multiplayer.connected_to_server.connect(print.bind("Connected to server (as client)"))
	multiplayer.connected_to_server.connect($DebugMenu.show_sub_menu.bind("TEACHERSTUDENT"))
	multiplayer.peer_disconnected.connect(remove_personal_room)
	multiplayer.peer_disconnected.connect(remove_player)
	SignalBus.new_player_info_received.connect(request_spawn_from_server)
	SignalBus.player_clicked_join_room.connect(request_join_room_from_server)
	SignalBus.activity_launched.connect(request_activity_launch_from_server)
	
	if OS.has_feature("dedicated_server"):
		NetworkHandler.start_server()
	elif OS.has_feature("web"):
		NetworkHandler.start_client()
	else:
		$DebugMenu.show_sub_menu("SERVERCLIENT")


func _physics_process(_delta: float) -> void:
	# boy this is some trash
	if Input.is_action_just_pressed("ui_cancel"):
		if $LoadingScreen.visible:
			pass
		elif $DebugMenu.visible:
			pass
		elif $ChatScreen.visible:
			$ChatScreen.hide()
			SignalBus.chat_closed.emit()
		elif $PauseMenu.visible:
			$PauseMenu.hide()
		else: 
			$PauseMenu.update_room_list()
			$PauseMenu.show()



# called only on clients, requesting that server add their player to the game
func request_spawn_from_server(username: String, role: String):
	assert(not multiplayer.is_server(), "spawn requested by server somehow what the hell")
	print("Requesting spawn as: ", username, ", ", role)
	add_player_and_personal_room.rpc_id(1, [username, role, multiplayer.get_unique_id()])


# called only on server, by clients.
# also i apologize -robin.
@rpc("any_peer")
func add_player_and_personal_room(player_info: Array):
	players_joined += 1
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
			plot_marker = child
			break
	if plot_marker == null:
		print("damn, no space somehow")
		return
	# this is just to fake customization
	var room_path : String
	if players_joined % 2 == 1:
		room_path = "res://rooms/room_color_test_1.tscn"
	else:
		room_path = "res://rooms/room_color_test_2.tscn"
	var personal_room_instance = load(room_path).instantiate()
	personal_room_instance.name = "PROOM-" + str(player_peer_id)
	personal_room_instance.owner_username = username
	personal_room_instance.owner_peer_id = player_peer_id
	personal_room_instance.plot_marker = plot_marker
	personal_room_instance.set_global_position(plot_marker.get_global_position())
	$MultiplayerSpawner/GameWorld.call_deferred("add_child", personal_room_instance)
	$PauseMenu.update_room_list.rpc()
	print(username, "'s personal room " + personal_room_instance.name + " has spawned")
	#endregion
	#region  okay adding the player character this time
	var player_instance = load("res://player/player.tscn").instantiate()
	# this was a clever trick to easily ferry the id when synching between peers
	player_instance.name = str(player_peer_id)
	player_instance.username = username
	player_instance.set_global_position(personal_room_instance.get_node("SpawnPoint").get_global_position())
	$MultiplayerSpawner/GameWorld.call_deferred("add_child", player_instance)
	print("Player " + str(player_peer_id) + " (" + username + ") " + " has spawned")
	#endregion


# called only when player disconnects
func remove_personal_room(owner_peer_id):
	# called on every remianing peer, but we only want server to do this
	if not multiplayer.is_server():
		return
	var plot_marker
	for room in get_tree().get_nodes_in_group("personal_rooms"):
		# should also move remaining players in room out, but that requires
		# that the room knows who's in there to begin with
		if room.owner_peer_id == owner_peer_id:
			print("Removing ", room.name)
			plot_marker = room.plot_marker
			room.queue_free()
			plot_marker.plot_available = true
			break
	$PauseMenu.update_room_list.rpc()


# called only when player disconnects
func remove_player(player_peer_id):
	if not multiplayer.is_server():
		return
	for player in get_tree().get_nodes_in_group("players"):
		if int(player.name) == player_peer_id:
			print("Removing ", player.name)
			print("Removing ", player.name)
			player.queue_free()
			break


#region public room add/remove (for later)
@rpc("any_peer")
func add_public_room():
	#prolly just spawn the fucken thing right at (0,0)
	assert(multiplayer.is_server())
	pass
	$PauseMenu.update_room_list.rpc()


@rpc("any_peer")
func remove_public_room():
	#when we're done with it i dunno?
	#there should probably be a seprate lobby that's always loaded
	assert(multiplayer.is_server())
	$PauseMenu.update_room_list.rpc()
#endregion


func request_activity_launch_from_server():
	assert(not multiplayer.is_server())
	launch_activity.rpc_id(1)


# called only on server.
@rpc("any_peer")
func launch_activity():
	# this would be more complicated, check role/permissions,
	# and apply to whichever room is relevant
	for player in get_tree().get_nodes_in_group("players"):
		move_player_to_room([int(player.name), "Lobby"])
		# with only one spawnpoint, this is necessary to prevent glitching
		await get_tree().create_timer(.2).timeout


# called only on clients, requesting that server move the player to the given room
func request_join_room_from_server(room_name: String):
	assert(not multiplayer.is_server(), "room join requested by server somehow what the hell")
	print("Requesting join room from server")
	move_player_to_room.rpc_id(1, [multiplayer.get_unique_id(), room_name])
	
	
# called only on server
@rpc("any_peer")
func move_player_to_room(move_info):
	# should be as simple as moving the player to the right coordinates
	assert(multiplayer.is_server())
	print("Moving ", move_info[0], " to ", move_info[1])
	var joiner_peer_id = move_info[0]
	var room_name = move_info[1]
	var room_to_join
	for room in get_tree().get_nodes_in_group("rooms"):
		if room.name == room_name:
			room_to_join = room
			break
	assert(not room_to_join == null)
	var spawn_location = room_to_join.get_node("SpawnPoint").get_global_position()
	for player in get_tree().get_nodes_in_group("players"):
		if int(player.name) == joiner_peer_id:
			player.set_global_position(spawn_location)
			break
