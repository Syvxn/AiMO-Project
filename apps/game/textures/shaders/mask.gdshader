shader_type canvas_item;

uniform sampler2D mask_texture;
uniform float mask_y_delta;

void fragment() {
	vec4 color = texture(TEXTURE, UV);
	vec2 mask_UV = UV;
	mask_UV.y += mask_y_delta;
	float mask = texture(mask_texture, mask_UV).r;
	color.a *= mask;
	COLOR = color;
}

//void light() {
//	// Called for every pixel for every light affecting the material.
//	// Uncomment to replace the default light processing function with this one.
//}
