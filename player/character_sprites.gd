extends Node2D

var current_mode := "clothes"



func play_animation(anim_name: String):
	for child in get_children():
		if child is AnimatedSprite2D:
			child.play(anim_name)
			


func switch_mode(mode: String):
	if mode == "costume":
		for child in get_children():
			if child is AnimatedSprite2D:
				child.hide()
		$CostumeSprite.show()
	elif mode == "clothes":
		for child in get_children():
			if child is AnimatedSprite2D:
				child.show()
		$CostumeSprite.hide()
	current_mode = mode


func apply_sprites_and_colors(data: Dictionary):
	$BodySprite.sprite_frames = load(Clothes.body_items[data["body_item"]])
	$BodySprite.self_modulate = Color(data["body_color"])
	$EyesSprite.sprite_frames = load(Clothes.eyes_items[data["eyes_item"]])
	$EyesSprite.self_modulate = Color(data["eyes_color"])
	$HairSprite.sprite_frames = load(Clothes.hair_items[data["hair_item"]])
	$HairSprite.self_modulate = Color(data["hair_color"])
	$ShirtSprite.sprite_frames = load(Clothes.shirt_items[data["shirt_item"]])
	$ShirtSprite.self_modulate = Color(data["shirt_color"])
	$PantsSprite.sprite_frames = load(Clothes.pants_items[data["pants_item"]])
	$PantsSprite.self_modulate = Color(data["pants_color"])
	$ShoesSprite.sprite_frames = load(Clothes.shoes_items[data["shoes_item"]])
	$ShoesSprite.self_modulate = Color(data["shoes_color"])


func apply_costume(costume: String):
	$CostumeSprite.sprite_frames = load(Clothes.costumes[costume])


func randomize_colors():
	for child in get_children():
		if child is AnimatedSprite2D:
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
