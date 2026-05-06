extends Area2D

func interact():
	talk()
	

func talk():
	SignalBus.chat_opened.emit()
