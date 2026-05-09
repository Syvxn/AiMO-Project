extends Area2D

func interact():
	talk()
	

func talk():
	Env.CURRENT_CHAT_NPC_ID = "quiz_llehc"
	SignalBus.chat_opened.emit()
