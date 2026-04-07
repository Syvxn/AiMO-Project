extends MarginContainer

var correct_key : String

@onready var label = $VBoxContainer/MarginContainer/Label
@onready var item_list = $VBoxContainer/MarginContainer2/ItemList



func fill_out_qustion(question_text: String, correct_answer_key: String, answers: Dictionary):
	label.text = question_text
	correct_key = correct_answer_key
	for answer_key in answers:
		var answer_text = answer_key + ": " + answers[answer_key]
		item_list.add_item(answer_text)
	item_list.sort_items_by_text()


func check_answer() -> bool:
	var selected_answer_index = item_list.get_selected_items()[0] # should only be one
	if item_list.get_item_text(selected_answer_index).begins_with(correct_key):
		item_list.set_item_custom_bg_color(selected_answer_index, Color("YELLOW_GREEN"))
		return true
	else:
		item_list.set_item_custom_bg_color(selected_answer_index, Color("ORANGE_RED"))
		return false
