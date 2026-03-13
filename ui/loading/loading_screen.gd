extends CanvasLayer

func _ready() -> void:
	# show() and hide() are existing methods
	SignalBus.started_loading.connect(show)
	SignalBus.finished_loading.connect(hide)

func set_label_text(text: String) -> void:
	$Control/MarginContainer/Label.text = text

func reset_label_text() -> void:
	$Control/MarginContainer/Label.text = "this is a cool loading screen..."
