extends Node2D

var display_name = "Rainbow Room"


func _process(_delta: float) -> void:
	var player_locations : Array[Vector2]
	for player in get_tree().get_nodes_in_group("players"):
		player_locations.append(player.global_position)
	$Floor.get_material().set_shader_parameter("player_locs", player_locations)
