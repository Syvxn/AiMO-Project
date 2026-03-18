extends Node

# these signals can be emitted from anywhere and connected to from anywhere.
# they're not used in this script tho, so we surpress the warning
# because i don't wanna hear that shit.
@warning_ignore("unused_signal")
signal started_loading
@warning_ignore("unused_signal")
signal finished_loading
@warning_ignore("unused_signal")
signal new_player_info_received(username: String, role: String)
@warning_ignore("unused_signal")
signal activity_launched
@warning_ignore("unused_signal")
signal activity_ended
@warning_ignore("unused_signal")
signal player_clicked_join_room(room_name: String)
