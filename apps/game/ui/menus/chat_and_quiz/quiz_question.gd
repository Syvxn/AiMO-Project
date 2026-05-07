extends MarginContainer

var correct_key : String

@onready var label = $VBoxContainer/MarginContainer/Label
@onready var item_list = $VBoxContainer/MarginContainer2/ItemList



func fill_out_question(question_text: String, answers: Array, correct_answer_key: String):
	label.text = question_text
	item_list.clear()
	for answer in answers:
		item_list.add_item(answer)
	item_list.sort_items_by_text()
	correct_key = correct_answer_key


func check_answer(show_color=true) -> bool:
	if not item_list.is_anything_selected():
		return false
	var selected_answer_index = item_list.get_selected_items()[0] # should only be one
	if item_list.get_item_text(selected_answer_index).begins_with(correct_key):
		if show_color:
			item_list.set_item_custom_bg_color(selected_answer_index, Color("FOREST_GREEN"))
		return true
	else:
		if show_color:
			item_list.set_item_custom_bg_color(selected_answer_index, Color("DARK_RED"))
		return false


func show_correct_answer():
	for i in range(item_list.item_count):
		if item_list.get_item_text(i).begins_with(correct_key):
			item_list.set_item_custom_bg_color(i, Color("FOREST_GREEN"))
