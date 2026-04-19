extends Node2D

var current_mode := "clothes"
var current_data := {}
var current_costume : String


func _ready() -> void:
	if current_mode == "clothes":
		if not current_data.is_empty():
			apply_sprites_and_colors(current_data)



func play_animation(anim_name: String):
	for child in get_children():
		if child is AnimatedSprite2D:
			child.play(anim_name)
			


@rpc("any_peer", "call_local")
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


@rpc("any_peer", "call_local")
func apply_sprites_and_colors(data: Dictionary):
	if not data["items"].is_empty():
		$BodySprite.sprite_frames = load(Clothes.body_items[data["items"]["body_item"]])
		$EyesSprite.sprite_frames = load(Clothes.eyes_items[data["items"]["eyes_item"]])
		$HairSprite.sprite_frames = load(Clothes.hair_items[data["items"]["hair_item"]])
		$ShirtSprite.sprite_frames = load(Clothes.shirt_items[data["items"]["shirt_item"]])
		$PantsSprite.sprite_frames = load(Clothes.pants_items[data["items"]["pants_item"]])
		$ShoesSprite.sprite_frames = load(Clothes.shoes_items[data["items"]["shoes_item"]])
	if not data["colors"].is_empty():
		$BodySprite.self_modulate = Color(data["colors"]["body_color"])
		$EyesSprite.self_modulate = Color(data["colors"]["eyes_color"])
		$HairSprite.self_modulate = Color(data["colors"]["hair_color"])
		$ShirtSprite.self_modulate = Color(data["colors"]["shirt_color"])
		$PantsSprite.self_modulate = Color(data["colors"]["pants_color"])
		$ShoesSprite.self_modulate = Color(data["colors"]["shoes_color"])
	current_data = data


@rpc("any_peer", "call_local")
func apply_costume(costume: String):
	$CostumeSprite.sprite_frames = load(Clothes.costumes[costume])


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
		"colors" : {}
	}
	data["colors"]["body_color"] = colors.pick_random()
	data["colors"]["eyes_color"] = colors.pick_random()
	data["colors"]["hair_color"] = colors.pick_random()
	data["colors"]["shirt_color"] = colors.pick_random()
	data["colors"]["pants_color"] = colors.pick_random()
	data["colors"]["shoes_color"] = colors.pick_random()
	apply_sprites_and_colors.rpc(data)
