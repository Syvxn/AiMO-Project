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
}


func _ready() -> void:
	load_options()



func load_options():
	for item_key in Clothes.body_items.keys():
		%BodyOptions.add_item(Clothes.body_items[item_key]["name"])
	for item_key in Clothes.eyes_items.keys():
		%EyesOptions.add_item(Clothes.eyes_items[item_key]["name"])
	for item_key in Clothes.hair_items.keys():
		%HairOptions.add_item(Clothes.hair_items[item_key]["name"])
	for item_key in Clothes.shirt_items.keys():
		%ShirtOptions.add_item(Clothes.shirt_items[item_key]["name"])
	for item_key in Clothes.pants_items.keys():
		%PantsOptions.add_item(Clothes.pants_items[item_key]["name"])
	for item_key in Clothes.jacket_items.keys():
		%JacketOptions.add_item(Clothes.jacket_items[item_key]["name"])
	for item_key in Clothes.shoes_items.keys():
		%ShoesOptions.add_item(Clothes.shoes_items[item_key]["name"])
	for item_key in Clothes.accessory_items.keys():
		%Accessory1Options.add_item(Clothes.accessory_items[item_key]["name"])
	for item_key in Clothes.accessory_items.keys():
		%Accessory2Options.add_item(Clothes.accessory_items[item_key]["name"])
	for item_key in Clothes.accessory_items.keys():
		%Accessory3Options.add_item(Clothes.accessory_items[item_key]["name"])
	for item_key in Clothes.costumes.keys():
		%CostumeOptions.add_item(Clothes.costumes[item_key]["name"])


# everything about this sucks. I should rebuild this whole menu
func select_current_options():
	var current_data = get_parent().get_applied_visuals_data()
	#region miserable fuckfest
	for i in range(%BodyOptions.item_count):
		for item_key in Clothes.body_items.keys():
			if Clothes.body_items[item_key]["name"] == %BodyOptions.get_item_text(i):
				if item_key == current_data["items"]["body_item"]:
					%BodyOptions.select(i)
	for i in range(%EyesOptions.item_count):
		for item_key in Clothes.eyes_items.keys():
			if Clothes.eyes_items[item_key]["name"] == %EyesOptions.get_item_text(i):
				if item_key == current_data["items"]["eyes_item"]:
					%EyesOptions.select(i)
	for i in range(%HairOptions.item_count):
		for item_key in Clothes.hair_items.keys():
			if Clothes.hair_items[item_key]["name"] == %HairOptions.get_item_text(i):
				if item_key == current_data["items"]["hair_item"]:
					%HairOptions.select(i)
	for i in range(%ShirtOptions.item_count):
		for item_key in Clothes.shirt_items.keys():
			if Clothes.shirt_items[item_key]["name"] == %ShirtOptions.get_item_text(i):
				if item_key == current_data["items"]["shirt_item"]:
					%ShirtOptions.select(i)
	for i in range(%PantsOptions.item_count):
		for item_key in Clothes.pants_items.keys():
			if Clothes.pants_items[item_key]["name"] == %PantsOptions.get_item_text(i):
				if item_key == current_data["items"]["pants_item"]:
					%PantsOptions.select(i)
	for i in range(%JacketOptions.item_count):
		for item_key in Clothes.jacket_items.keys():
			if Clothes.jacket_items[item_key]["name"] == %JacketOptions.get_item_text(i):
				if item_key == current_data["items"]["jacket_item"]:
					%JacketOptions.select(i)
	for i in range(%ShoesOptions.item_count):
		for item_key in Clothes.shoes_items.keys():
			if Clothes.shoes_items[item_key]["name"] == %ShoesOptions.get_item_text(i):
				if item_key == current_data["items"]["shoes_item"]:
					%ShoesOptions.select(i)
	for i in range(%Accessory1Options.item_count):
		for item_key in Clothes.accessory_items.keys():
			if Clothes.accessory_items[item_key]["name"] == %Accessory1Options.get_item_text(i):
				if item_key == current_data["items"]["accessory1_item"]:
					%Accessory1Options.select(i)
	for i in range(%Accessory2Options.item_count):
		for item_key in Clothes.accessory_items.keys():
			if Clothes.accessory_items[item_key]["name"] == %Accessory2Options.get_item_text(i):
				if item_key == current_data["items"]["accessory2_item"]:
					%Accessory2Options.select(i)
	for i in range(%Accessory3Options.item_count):
		for item_key in Clothes.accessory_items.keys():
			if Clothes.accessory_items[item_key]["name"] == %Accessory3Options.get_item_text(i):
				if item_key == current_data["items"]["accessory3_item"]:
					%Accessory3Options.select(i)
	for i in range(%CostumeOptions.item_count):
		for item_key in Clothes.costumes.keys():
			if Clothes.costumes[item_key]["name"] == %CostumeOptions.get_item_text(i):
				if item_key == current_data["costume_name"]:
					%CostumeOptions.select(i)
	#endregion
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
	if source.name == "CostumeOptions":
		for item_key in Clothes.costumes.keys():
			if Clothes.costumes[item_key]["name"] == source.get_item_text(index):
				current_data["costume_name"] = item_key
				current_data["use_costume"] = true
	else:
		for item_key in bandaid[source.name]["options_dict"]:
			if bandaid[source.name]["options_dict"][item_key]["name"] == source.get_item_text(index):
				current_data["items"][bandaid[source.name]["data_key"]] = item_key
				current_data["use_costume"] = false
	print(current_data)
	get_parent().apply_visuals.rpc(current_data)
