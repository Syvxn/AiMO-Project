extends CanvasLayer

func _ready() -> void:
	# show() and hide() are existing methods
	SignalBus.started_loading.connect(show)
	SignalBus.finished_loading.connect(hide_after_a_moment)
	

func hide_after_a_moment():
	await get_tree().create_timer(0.75).timeout
	hide()

func set_label_text(text: String) -> void:
	$Control/MarginContainer/Label.text = text

func reset_label_text() -> void:
	$Control/MarginContainer/Label.text = "this is a cool loading screen..."
