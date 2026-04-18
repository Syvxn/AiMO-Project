extends Node2D



func _ready() -> void:
	randomize_colors()


func apply_clothes_and_colors(data: Dictionary):
	# $HairSprite.sprite_frames = load(ClothesBus.Hair[data["hair_item"]])
	# $HairSprite.self_modulate = Color(data["hair_color"])
	pass


func play_animation(anim_name: String):
	for child in get_children():
		if child is AnimatedSprite2D:
			child.play(anim_name)


func randomize_colors():
	for child in get_children():
		if child is AnimatedSprite2D:
			print(child.name)
			var colors = [
				Color("RED"),
				Color("ORANGE_RED"),
				Color("ORANGE"),
				Color("BLUE"),
				Color("GREEN"),
				Color("WHITE"),
				Color("PINK"),
				Color("PURPLE"),
				Color("FUCHSIA"),
				Color("YELLOW"),
				Color("GOLD"),
				Color("WEB_GREEN"),
				Color("MINT_CREAM"),
				Color("ROYAL_BLUE"),
				Color("OLIVE"),
				Color("CRIMSON"),
				Color("YELLOW_GREEN"),
				Color("LIGHT_SKY_BLUE"),
				Color("NAVY_BLUE"),
				Color("MOCCASIN"),
				Color("SLATE_BLUE"),
				Color("MAROON"),
				Color("REBECCA_PURPLE"),
				Color("SEA_GREEN"),
				Color("INDIGO"),
				Color("DARK_OLIVE_GREEN"),
				Color("TEAL"),
				Color("KHAKI"),
				Color("DARK_ORANGE"),
				Color("WEB_MAROON"),
				Color("GHOST_WHITE"),
				Color("HOT_PINK"),
			]
			child.self_modulate = colors.pick_random()


func _on_debug_rand_timer_timeout() -> void:
	randomize_colors()
