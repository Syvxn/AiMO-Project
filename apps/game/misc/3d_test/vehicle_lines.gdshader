shader_type spatial;
uniform vec4 emission : source_color;
uniform float emission_energy : hint_range(0.0, 10.0, 0.01);
uniform vec2 vehicle_coords;

void vertex() {
	// Called for every vertex the material is visible on.
}

void fragment() {
	if(distance(VERTEX.x, vehicle_coords.x) > 0.1) {
		if(distance(VERTEX.y, vehicle_coords.y) > 0.1) {
			discard;
		}
	}
	if(distance(VERTEX.x, vehicle_coords.x) < 5.0 && distance(VERTEX.y, vehicle_coords.y) < 2.0) {
		discard;
	}
	if(VERTEX.y > (vehicle_coords.y + 1.0)) discard;
	EMISSION = (emission.rgb) * emission_energy;
}

//void light() {
//	// Called for every pixel for every light affecting the material.
//	// Uncomment to replace the default light processing function with this one.
//}
