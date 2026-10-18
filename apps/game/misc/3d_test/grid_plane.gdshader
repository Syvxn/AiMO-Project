shader_type spatial;
uniform bool equation_visible;
uniform int equation_type; 
uniform float equation_a; 
uniform float equation_b; 
uniform vec4 emission : source_color;
uniform vec4 laser_emission : source_color;
uniform float emission_energy : hint_range(0.0, 10.0, 0.01);
uniform float laser_emission_energy : hint_range(0.0, 10.0, 0.01);


void vertex() {
	// Called for every vertex the material is visible on.
}

void fragment() {
	float equation_y;
	switch(equation_type) {
		case 0:
			equation_y = equation_a * VERTEX.x + equation_b;
			break;
		case 1:
			equation_y = equation_a * sin(VERTEX.x) + equation_b;
			break;
		case 2:
			equation_y = equation_a * cos(VERTEX.x) + equation_b;
			break;
		case 3:
			equation_y = equation_a * tan(VERTEX.x) + equation_b;
			break;
		case 4:
			equation_y = sqrt(pow(VERTEX.x, 2.0)-pow(equation_a, 2.0))+equation_b;
			break;
	};
	if(equation_visible){
		if(distance(VERTEX.y, equation_y) < 0.2) {
			EMISSION = (laser_emission.rgb) * laser_emission_energy;
		}  else {
			bool x_far = false;
			bool y_far = false;
			if(abs(mod(VERTEX.x,2)) > 0.1) x_far=true;
			if(abs(mod(VERTEX.y,2)) > 0.1) y_far=true;
			if(x_far&&y_far) discard;
			EMISSION = (emission.rgb) * emission_energy;
		}
	} else {
		bool x_far = false;
		bool y_far = false;
		if(abs(mod(VERTEX.x,2)) > 0.1) x_far=true;
		if(abs(mod(VERTEX.y,2)) > 0.1) y_far=true;
		if(x_far&&y_far) discard;
		EMISSION = (emission.rgb) * emission_energy;
	}
}

//void light() {
//	// Called for every pixel for every light affecting the material.
//	// Uncomment to replace the default light processing function with this one.
//}
