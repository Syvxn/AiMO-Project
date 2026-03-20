extends Area2D


var pushed = false


func _ready() -> void:
	$Control/DialogueBox.hide()


func interact():
	push()


func push():
	if not pushed:
		pushed = true
		$AnimatedSprite2D.play("push")
		$Control/DialogueBox.show()
		request_chicken()
	else:
		pushed = false
		$AnimatedSprite2D.play("push")
		$Control/DialogueBox/MarginContainer/RichTextLabel.text = "Requesting..."
		$Control/DialogueBox.hide()


func request_chicken() -> void:
	var http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(self._chicken_request_completed)
	http_request.request("https://oispa.kievinkanaa.com/")


func _chicken_request_completed(_result, _response_code, _headers, body) -> void:
	var body_text = body.get_string_from_utf8()
	$Control/DialogueBox/MarginContainer/RichTextLabel.text = body_text
	
	
