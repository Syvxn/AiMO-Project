extends Node

# these signals can be emitted from anywhere and connected to from anywhere.
# they're not used in this script tho, so we surpress the warning
# because i don't wanna hear that shit.
@warning_ignore_start("unused_signal")
signal started_loading
signal finished_loading()
signal new_player_info_received(username: String, role: String)
signal player_clicked_join_room(room_name: String)
signal activity_launched
signal activity_ended
signal item_autolooted(id: String, type: String, looter: Node)
signal chat_opened
signal chat_closed
signal global_chat_toggled
signal global_chat_input_focused
signal global_chat_input_unfocused
signal arcade_game_launched
signal arcade_game_closed
signal oops_pressed
