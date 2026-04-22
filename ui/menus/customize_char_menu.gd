extends CanvasLayer


var bandaid = {
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



func _ready() -> void:
	load_options()



func load_options():
	for key in bandaid.keys():
		for item_key in bandaid[key]["options_dict"]:
			get_node("%" + key).add_item(bandaid[key]["options_dict"][item_key]["name"])


# everything about this sucks. I should rebuild this whole menu
func select_current_options():
	var current_data = get_parent().get_applied_visuals_data()
	for key in bandaid.keys():
		for i in range(get_node("%" + key).item_count):
			for item_key in bandaid[key]["options_dict"].keys():
				if bandaid[key]["options_dict"][item_key]["name"] == get_node("%" + key).get_item_text(i):
					if item_key == current_data["items"][bandaid[key]["data_key"]]:
						get_node("%" + key).select(i)
	#region colors
	%BodyColor.color = current_data["colors"]["body_color"]
	%EyesColor.color = current_data["colors"]["eyes_color"]
	%HairColor.color = current_data["colors"]["hair_color"]
	%ShirtColor.color = current_data["colors"]["shirt_color"]
	%PantsColor.color = current_data["colors"]["pants_color"]
	%JacketColor.color = current_data["colors"]["jacket_color"]
	%ShoesColor.color = current_data["colors"]["shoes_color"]
	%Accessory1Color.color = current_data["colors"]["accessory1_color"]
	%Accessory2Color.color = current_data["colors"]["accessory2_color"]
	%Accessory3Color.color = current_data["colors"]["accessory3_color"]
	#endregion
	


# this, mercifully, does not trigger when select_current_options() is called
func _on_options_item_selected(index: int, source: OptionButton) -> void:
	var current_data = get_parent().get_applied_visuals_data()
	for item_key in bandaid[source.name]["options_dict"]:
		if bandaid[source.name]["options_dict"][item_key]["name"] == source.get_item_text(index):
			current_data["items"][bandaid[source.name]["data_key"]] = item_key
	if source.name == "CostumeOptions":
		current_data["use_costume"] = true
	else:
		current_data["use_costume"] = false
	print(current_data)
	get_parent().apply_visuals.rpc(current_data)
