extends Area2D

@export var turned_on := false
@export var autolooter_id := ""
@export var type_to_loot := ""
@export var looter_to_report : Node


func configure(radius: float, id: String, type: String, looter=self):
	$CollisionShape2D.shape.radius = radius
	autolooter_id = id
	type_to_loot = type
	looter_to_report = looter


func turn_on():
	turned_on = true

func turn_off():
	turned_on = false


func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("lootables"):
		if body.get("lootable"):
			if body.get("lootable_type") == type_to_loot:
				SignalBus.item_autolooted.emit(autolooter_id, type_to_loot, looter_to_report)
				body.queue_free()
