extends Node


func _ready() -> void:
	
	if OS.has_feature("dedicated_server"):
		NetworkHandler.start_server()
	elif OS.has_feature("web"):
		NetworkHandler.start_client()
	else:
		# lets us pick between server/client
		$DebugMenu.show_sub_menu($DebugMenu.SubMenu.SERVERCLIENT)
	
	
