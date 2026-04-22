extends CanvasLayer


var clothes_lookup = {
	"BodyOptions" : {"options_dict" : Clothes.body_items, "data_key" : "body_item"},
	"EyesOptions" : {"options_dict" : Clothes.eyes_items, "data_key" : "eyes_item"},
	"HairOptions" : {"options_dict" : Clothes.hair_items, "data_key" : "hair_item"},
	"ShirtOptions" : {"options_dict" : Clothes.shirt_items, "data_key" : "shirt_item"},
	"PantsOptions" : {"options_dict" : Clothes.pants_items, "data_key" : "pants_item"},
	"JacketOptions" : {"options_dict" : Clothes.jacket_items, "data_key" : "jacket_item"},
	"ShoesOptions" : {"options_dict" : Clothes.shoes_items, "data_key" : "shoes_item"},
	"Accessory1Options" : {"options_dict" : Clothes.accessory_items, "data_key" : "accessory1_item"},
	"Accessory2Options" : {"options_dict" : Clothes.accessory_items, "data_key" : "accessory2_item"},
	"Accessory3Options" : {"options_dict" : Clothes.accessory_items, "data_key" : "accessory3_item"},
	"CostumeOptions" : {"options_dict" : Clothes.costume_items, "data_key" : "costume_item"},
}
var colors_lookup = {
	"BodyColor" : {"data_key" : "body_color"},
	"EyesColor" : {"data_key" : "eyes_color"},
	"HairColor" : {"data_key" : "hair_color"},
	"ShirtColor" : {"data_key" : "shirt_color"},
	"PantsColor" : {"data_key" : "pants_color"},
	"JacketColor" : {"data_key" : "jacket_color"},
	"ShoesColor" : {"data_key" : "shoes_color"},
	"Accessory1Color" : {"data_key" : "accessory1_color"},
	"Accessory2Color" : {"data_key" : "accessory2_color"},
	"Accessory3Color" : {"data_key" : "accessory3_color"},
}



func _ready() -> void:
	load_options()


func close_menu():
	get_parent().toggle_customize_menu()

func load_options():
	for key in clothes_lookup:
		for item_key in clothes_lookup[key]["options_dict"]:
			get_node("%" + key).add_item(clothes_lookup[key]["options_dict"][item_key]["name"])


# whoops, i made it less readable
func select_current_options():
	var current_data = get_parent().get_applied_visuals_data()
	for key in clothes_lookup:
		for i in range(get_node("%" + key).item_count):
			for item_key in clothes_lookup[key]["options_dict"]:
				if clothes_lookup[key]["options_dict"][item_key]["name"] == get_node("%" + key).get_item_text(i):
					if item_key == current_data["items"][clothes_lookup[key]["data_key"]]:
						get_node("%" + key).select(i)
	for key in colors_lookup:
		get_node("%" + key).color = current_data["colors"][colors_lookup[key]["data_key"]]


# this, mercifully, does not trigger when select_current_options() is called
func _on_options_item_selected(index: int, source: OptionButton) -> void:
	var current_data = get_parent().get_applied_visuals_data()
	for item_key in clothes_lookup[source.name]["options_dict"]:
		if clothes_lookup[source.name]["options_dict"][item_key]["name"] == source.get_item_text(index):
			current_data["items"][clothes_lookup[source.name]["data_key"]] = item_key
	if source.name == "CostumeOptions":
		current_data["use_costume"] = true
	else:
		current_data["use_costume"] = false
	get_parent().apply_visuals.rpc(current_data)


func _on_color_popup_closed(source: ColorPickerButton) -> void:
	var current_data = get_parent().get_applied_visuals_data()
	for key in colors_lookup:
		if source.name == key:
			current_data["colors"][colors_lookup[key]["data_key"]] = source.color.to_html()
	current_data["use_costume"] = false
	get_parent().apply_visuals.rpc(current_data)
