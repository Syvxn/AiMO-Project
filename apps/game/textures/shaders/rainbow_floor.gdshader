shader_type canvas_item;
uniform vec2 player_locs[100];

//void vertex() {
	// Called for every vertex the material is visible on.
//}

void fragment() {
	for (int i=0; i<player_locs.length(); i++) {
		float dist = distance(player_locs[i].xy, VERTEX);
		if (dist > 16.0 && dist < 80.0 ) {
			//discard;
			COLOR.rgb = COLOR.rgb *  vec3(
				0.5 * sin(0.1*dist) + 1.0,
				0.5 * sin(0.1*dist + (2.0*PI)*0.33) + 1.0,
				0.5 * sin(0.1*dist+ (2.0*PI)*0.66) + 1.0
			);
		}
	}
}

//void light() {
//	// Called for every pixel for every light affecting the CanvasItem.
//	// Uncomment to replace the default light processing function with this one.
//}
