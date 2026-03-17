extends Node

# signals that can be emitted from anywhere and connected to from anywhere
@warning_ignore("unused_signal")
signal started_loading
@warning_ignore("unused_signal")
signal finished_loading
@warning_ignore("unused_signal")
signal player_info_received(username: String, role: String)
