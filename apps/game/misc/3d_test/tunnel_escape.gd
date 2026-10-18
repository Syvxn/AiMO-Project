extends Node3D

var game_over = false
var grid_start_pos := Vector3(0.0, 0.0, -450.0)
var grid_speed := 85.0
var vehicle_controllable := true
var fly_speed := 15.0
var vehicle_health := 3
var vehicle_invincible := false
var firing_speed := 800.0
var target_x_coordinates = []
var equation_visible := false
enum Equation {LIN, SIN, COS, TAN, CIRCLE}
var equation = {
	"type" : Equation.LIN,
	"a" : 1.0,
	"b" : 1.0,
	"string" : "y=1*x+1"
}

@onready var vehicle_lines_material = %VehicleLines.get_active_material(0)
@onready var grid_plane_material = %GridPlane.get_active_material(0)
@onready var debris = load("res://misc/3d_test/debris.tscn")


func _ready() -> void:
	%GameOverLabel.hide()
	%GridPlane.position = grid_start_pos
	for i in range(-200, 200, 2):
		target_x_coordinates.append(i/10.0)
	equation = generate_equation() #first equation
	%EquationLabel.text = equation["string"]
	grid_plane_material.set_shader_parameter("equation_type", equation["type"])
	grid_plane_material.set_shader_parameter("equation_a", equation["a"])
	grid_plane_material.set_shader_parameter("equation_b", equation["b"])
	grid_plane_material.set_shader_parameter("equation_visible", false)
	equation_visible = false


func _process(delta: float) -> void:
	if game_over:
		return
	if %GridPlane.visible:
		%GridPlane.position.z += delta * grid_speed
		if %GridPlane.position.z >= -20.0 and not equation_visible:
			grid_plane_material.set_shader_parameter("equation_visible", true)
			equation_visible = true
		if %GridPlane.position.z >= 37.0:
			%GridPlane.hide()
			grid_speed += 10.0
			%GridSpawnTimer.start(0.5)
			#var target_x_coordinates = [-19.0, -16.0, -13.0, -10.0, -7.0, -4.0, -1.0, 2.0, 5.0, 8.0, 11.0, 14.0, 17.0, 20.0]
			var target_list = return_targets(equation, target_x_coordinates)
			%Cannon.fire(target_list, firing_speed)
			equation = generate_equation() #new one for next turn
			%EquationLabel.text = equation["string"]
			grid_plane_material.set_shader_parameter("equation_type", equation["type"])
			grid_plane_material.set_shader_parameter("equation_a", equation["a"])
			grid_plane_material.set_shader_parameter("equation_b", equation["b"])
			grid_plane_material.set_shader_parameter("equation_visible", false)
			equation_visible = false
	if vehicle_controllable:
		var fly_direction = Input.get_vector("move_left", "move_right", "move_up", "move_down")
		var new_x = %VehicleGroup.position.x + fly_direction.x * fly_speed * delta
		var new_y = %VehicleGroup.position.y - fly_direction.y * fly_speed * delta
		var new_z = 13
		%VehicleGroup.position = Vector3(clamp(new_x,-14.0,14.0),clamp(new_y,-14.0,14.0), new_z)
		%Vehicle.rotation_degrees.x = fly_direction.y * 43.0
		%Vehicle.rotation_degrees.z = fly_direction.x * 21.0
		%CoordsLabel.text = "(%.f,%.f)" % [%VehicleGroup.position.x, %VehicleGroup.position.y]
		vehicle_lines_material.set_shader_parameter("vehicle_coords", Vector2(%VehicleGroup.position.x, %VehicleGroup.position.y))


#is there a better type hint for this?
func generate_equation() -> Variant:
	var type = [
		Equation.LIN, 
		Equation.SIN,
		Equation.COS,
		Equation.TAN,
		#Equation.CIRCLE
		].pick_random()
	var a = randi_range(-5,5)
	var b = randi_range(-10,10)
	var s = "y="
	var plus = "+" if b>0 else ""
	match type:
		Equation.LIN:
			s += "%d*x%s%d" % [a, plus, b]
		Equation.SIN:
			s += "%d*sin(x)%s%d" % [a, plus, b]
		Equation.COS:
			s += "%d*cos(x)%s%d" % [a, plus, b]
		Equation.TAN:
			a = clampi(a, -2, 2) #because good luck dodging this otherwise
			s += "%d*tan(x)%s%d" % [a, plus, b]
		Equation.CIRCLE: # currently unused since two possible y values, weird for shader too
			s += "sqrt(x^2-%d^2)%s%d" % [a, plus, b]
	var new_equation = {
		"type" : type,
		"a" : float(a),
		"b" : float(b),
		"string" : s
	}
	#print(new_equation)
	return new_equation


func return_targets(target_equation: Variant, x_coords: Array) -> Array:
	var type = target_equation["type"]
	var a = target_equation["a"]
	var b = target_equation["b"]
	var y : Callable
	match type:
		Equation.LIN:
			y = func(x):
				return a * x + b
		Equation.SIN:
			y = func(x):
				return a*sin(x)+b
		Equation.COS:
			y = func(x):
				return a*cos(x)+b
		Equation.TAN:
			y = func(x):
				return a*tan(x)+b
		Equation.CIRCLE:
			y = func(x):
				return sqrt(x**2-a**2)+b
	var targets = []
	for x in x_coords:
		targets.append(Vector3(x, y.call(x), 13.0))
	return targets


func take_damage() -> void:
	if vehicle_invincible:
		return
	vehicle_invincible = true
	%VehicleDamageCooldown.start()
	vehicle_health -= 1
	if vehicle_health == 0:
		game_over = true
		print("GAME OVER")
		%VehicleLines.hide()
		%EquationLabel.hide()
		%CoordsLabel.hide()
		explode_vehicle()
		%GameOverLabel.show()
	else:
		blink_vehicle()


func blink_vehicle() -> void:
	for i in range(3):
		%Vehicle.hide()
		await get_tree().create_timer(0.3).timeout
		%Vehicle.show()
		await get_tree().create_timer(0.3).timeout


func explode_vehicle() -> void:
	%Vehicle.hide()
	var debris_instance = debris.instantiate()
	add_child(debris_instance)
	debris_instance.global_position = %Vehicle.global_position
	debris_instance.global_rotation = %Vehicle.global_rotation
	debris_instance.scale = %VehicleGroup.scale
	debris_instance.explode()


func _on_grid_spawn_timer_timeout() -> void:
	%GridPlane.position = grid_start_pos
	%GridPlane.show()


func _on_hurtbox_body_entered(_body: Node3D) -> void:
	take_damage()


func _on_vehicle_damage_cooldown_timeout() -> void:
	vehicle_invincible = false
