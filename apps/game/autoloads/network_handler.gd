extends Node

const WEBSOCKET_BUFFER_SIZE := 4 * 1024 * 1024


func _configure_peer(peer: WebSocketMultiplayerPeer) -> void:
	peer.inbound_buffer_size = WEBSOCKET_BUFFER_SIZE
	peer.outbound_buffer_size = WEBSOCKET_BUFFER_SIZE


# should only be called by one instance of the game, i.e. the dedicated server
func start_server() -> void:
	var peer = WebSocketMultiplayerPeer.new()
	_configure_peer(peer)
	print("Create server: ", error_string( peer.create_server(Env.GAME_SERVER_PORT) ))
	multiplayer.multiplayer_peer = peer


# should be called by each player's game, connecting them to the server
# note: the server has to be running before you can connect to it
func start_client() -> void:
	var peer = WebSocketMultiplayerPeer.new()
	_configure_peer(peer)
	print("Create client: ", error_string( peer.create_client(Env.GAME_SERVER_URL) ))
	multiplayer.multiplayer_peer = peer


func terminate_networking() -> void:
	multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
