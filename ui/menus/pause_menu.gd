extends CanvasLayer


@onready var join_list = $ColorRect/VBoxContainer/PanelContainer/MarginContainer/ScrollContainer/JoinList
@onready var room_join_item = load("res://ui/menus/room_join_item.tscn")


func _ready() -> void:
	hide()
	update_room_list()

func _physics_process(_delta: float) -> void:
	if Input.is_action_just_pressed("ui_cancel"):
		if visible:
			hide()
		else: 
			update_room_list()
			show()


@rpc
func update_room_list():
	for child in join_list.get_children():
		child.queue_free()
	for room in get_tree().get_nodes_in_group("rooms"):
		var room_name = room.name
		var label_text = room_name
		if room.is_in_group("personal_rooms"):
			label_text = room.owner_username + "'s Room"
		var room_join_item_instance = room_join_item.instantiate()
		room_join_item_instance.room_name = room_name
		room_join_item_instance.set_room_label_text(label_text)
		join_list.add_child(room_join_item_instance)
	
