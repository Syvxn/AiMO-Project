extends Node2D

var current_data := {}



func play_animation(anim_name: String):
	for child in get_children():
		if child is AnimatedSprite2D:
			child.play(anim_name)


@rpc("any_peer", "call_local")
func apply_visuals(data) -> void:
	if data["use_costume"]:
		$CostumeSprite.sprite_frames = load(Clothes.costumes[data["costume_name"]])
		for child in get_children():
			child.hide()
		$CostumeSprite.show()
	else:
		if not data["items"].is_empty():
			$BodySprite.sprite_frames = load(Clothes.body_items[data["items"]["body_item"]]["path"])
			$EyesSprite.sprite_frames = load(Clothes.eyes_items[data["items"]["eyes_item"]]["path"])
			$HairSprite.sprite_frames = load(Clothes.hair_items[data["items"]["hair_item"]]["path"])
			$ShirtSprite.sprite_frames = load(Clothes.shirt_items[data["items"]["shirt_item"]]["path"])
			$PantsSprite.sprite_frames = load(Clothes.pants_items[data["items"]["pants_item"]]["path"])
			#$JacketSprite.sprite_frames = load(Clothes.jacket_items[data["items"]["jacket_item"]]["path"])
			$ShoesSprite.sprite_frames = load(Clothes.shoes_items[data["items"]["shoes_item"]]["path"])
			#$AccessorySprite1.sprite_frames = load(Clothes.accessory_items[data["items"]["accessory1_item"]]["path"])
			#$AccessorySprite2.sprite_frames = load(Clothes.accessory_items[data["items"]["accessory2_item"]]["path"])
			#$AccessorySprite3.sprite_frames = load(Clothes.accessory_items[data["items"]["accessory3_item"]]["path"])
		if not data["colors"].is_empty():
			$BodySprite.self_modulate = Color(data["colors"]["body_color"])
			$EyesSprite.self_modulate = Color(data["colors"]["eyes_color"])
			$HairSprite.self_modulate = Color(data["colors"]["hair_color"])
			$ShirtSprite.self_modulate = Color(data["colors"]["shirt_color"])
			$PantsSprite.self_modulate = Color(data["colors"]["pants_color"])
			#$JacketSprite.self_modulate = Color(data["colors"]["jacket_color"])
			$ShoesSprite.self_modulate = Color(data["colors"]["shoes_color"])
			#$AccessorySprite1.self_modulate = Color(data["colors"]["accessory1_color"])
			#$AccessorySprite2.self_modulate = Color(data["colors"]["accessory2_color"])
			#$AccessorySprite3.self_modulate = Color(data["colors"]["accessory3_color"])
		for child in get_children():
			child.show()
		$CostumeSprite.hide()


func randomize_colors():
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
	var data = {
		"items" : {},
		"colors" : {},
		"use_costume" : false,
		"costume_name" : ""
	}
	data["colors"]["body_color"] = colors.pick_random()
	data["colors"]["eyes_color"] = colors.pick_random()
	data["colors"]["hair_color"] = colors.pick_random()
	data["colors"]["shirt_color"] = colors.pick_random()
	data["colors"]["pants_color"] = colors.pick_random()
	data["colors"]["shoes_color"] = colors.pick_random()
	apply_visuals.rpc(data)
