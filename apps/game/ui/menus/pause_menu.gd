extends CanvasLayer


@onready var join_list = %JoinList
@onready var room_join_item = load("res://ui/menus/room_join_item.tscn")


func _ready() -> void:
	hide()
	update_room_list()


func close_menu():
	hide()
	


@rpc("authority", "call_remote")
func update_room_list():
	for child in join_list.get_children():
		child.queue_free()
	for room in get_tree().get_nodes_in_group("rooms"):
		var room_name = room.name
		var label_text = room_name
		if not room.get("display_name") == null:
			label_text = room.get("display_name")
		if room.is_in_group("personal_rooms"):
			label_text = room.owner_username + "'s Room"
		var room_join_item_instance = room_join_item.instantiate()
		room_join_item_instance.pause_menu = self
		room_join_item_instance.room_name = room_name
		room_join_item_instance.set_room_label_text(label_text)
		join_list.add_child(room_join_item_instance)
	


func _on_launch_activity_button_pressed() -> void:
	SignalBus.activity_launched.emit()
	hide()
