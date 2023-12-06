# This file is part of DagAmendment, the reference implementation of:
#
#   Michel, Élie and Boubekeur, Tamy (2021).
#   DAG Amendment for Inverse Control of Parametric Shapes
#   ACM Transactions on Graphics (Proc. SIGGRAPH 2021), 173:1-173:14.
#
# Copyright (c) 2020-2021 -- Télécom Paris (Élie Michel <elie.michel@telecom-paris.fr>)
# 
# DagAmendment is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# DagAmendment is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with DagAmendment.  If not, see <https://www.gnu.org/licenses/>.

import bpy
if not bpy.app.background:
    import gpu
    make_shader = gpu.types.GPUShader
else:
    make_shader = lambda frag, vert: None

# point_shader = make_shader('''
#     uniform mat4 viewProjectionMatrix;

#     in vec3 position;

#     void main()
#     {
#         gl_Position = viewProjectionMatrix * vec4(position, 1.0f);
#     }
# ''',

# '''
#     uniform vec4 color;
#     out vec4 fragColor;

#     void main()
#     {
#         fragColor = color;
#     }
# '''
# )

# vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
# vert_out.smooth('FLOAT4', "gl_Position")

point_shader_info = gpu.types.GPUShaderCreateInfo()
point_shader_info.push_constant("MAT4", "viewProjectionMatrix")
point_shader_info.vertex_in(0, "VEC3", "position")
# point_shader_info.vertex_out(0, "VEC4", "gl_Position")
# point_shader_info.vertex_out(vert_out)

point_shader_info.vertex_source(
    """
    void main()
    {
        gl_Position = viewProjectionMatrix * vec4(position, 1.0f);
    }
    """
)

# point_shader_info.fragment_in(0, "VEC4", "color")
point_shader_info.push_constant("VEC4", "color")
point_shader_info.fragment_out(0, "VEC4", "fragColor")
point_shader_info.fragment_source(
    """
    void main()
    {
        fragColor = color;
    }
    """
)

point_shader = gpu.shader.create_from_info(point_shader_info)

# del vert_out
del point_shader_info

# line_shader = make_shader('''
#     uniform mat4 viewProjectionMatrix;
#     uniform vec3 offsetDirection;
#     uniform float offsetFactor;

#     in vec3 position;

#     void main()
#     {
#         vec3 offset = offsetDirection * offsetFactor;
#         gl_Position = viewProjectionMatrix * vec4(position + offset, 1.0f);
#     }
# ''',

# '''
#     uniform vec4 color;
#     out vec4 fragColor;

#     vec4 linear_to_srgb(vec4 linear) {
#         return mix(
#             1.055 * pow(linear, vec4(1.0 / 2.4)) - 0.055,
#             12.92 * linear,
#             step(linear, vec4(0.00031308))
#         );
#     }

#     vec4 srgb_to_linear(vec4 srgb) {
#         return mix(
#             pow((srgb + 0.055) / 1.055, vec4(2.4)),
#             srgb / 12.92,
#             step(srgb, vec4(0.04045))
#         );
#     }

#     void main()
#     {
#         fragColor = srgb_to_linear(color);
#     }
# '''
# )

line_shader_info = gpu.types.GPUShaderCreateInfo()
line_shader_info.push_constant("MAT4", "viewProjectionMatrix")
line_shader_info.push_constant("VEC3", "offsetDirection")
line_shader_info.push_constant("FLOAT", "offsetFactor")

line_shader_info.vertex_in(0, "VEC3", "position")
# line_shader_info.vertex_out(0, "VEC4", "gl_Position")
# line_shader_info.vertex_out(vert_out)

line_shader_info.vertex_source(
    """
    void main()
    {
        vec3 offset = offsetDirection * offsetFactor;
        gl_Position = viewProjectionMatrix * vec4(position + offset, 1.0f);
    }
    """
)

line_shader_info.push_constant( "VEC4", "color")
line_shader_info.fragment_out(0, "VEC4", "fragColor")

line_shader_info.fragment_source(
    '''
    vec4 linear_to_srgb(vec4 linear) {
        return mix(
            1.055 * pow(linear, vec4(1.0 / 2.4)) - 0.055,
            12.92 * linear,
            step(linear, vec4(0.00031308))
        );
    }

    vec4 srgb_to_linear(vec4 srgb) {
        return mix(
            pow((srgb + 0.055) / 1.055, vec4(2.4)),
            srgb / 12.92,
            step(srgb, vec4(0.04045))
        );
    }

    void main()
    {
        fragColor = srgb_to_linear(color);
    }
'''
)

line_shader = gpu.shader.create_from_info(line_shader_info)

