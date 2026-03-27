extends CanvasLayer



func _ready() -> void:
	SignalBus.chat_opened.connect(show)
	SignalBus.chat_closed.connect(hide)
