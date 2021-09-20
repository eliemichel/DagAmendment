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

point_shader = make_shader('''
    uniform mat4 viewProjectionMatrix;

    in vec3 position;

    void main()
    {
        gl_Position = viewProjectionMatrix * vec4(position, 1.0f);
    }
''',

'''
    uniform vec4 color;

    void main()
    {
        gl_FragColor = color;
    }
'''
)

line_shader = make_shader('''
    uniform mat4 viewProjectionMatrix;
    uniform vec3 offsetDirection;
    uniform float offsetFactor;

    in vec3 position;

    void main()
    {
        vec3 offset = offsetDirection * offsetFactor;
        gl_Position = viewProjectionMatrix * vec4(position + offset, 1.0f);
    }
''',

'''
    uniform vec4 color;

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
        gl_FragColor = srgb_to_linear(color);
    }
'''
)

line_shader_2d = make_shader('''
    uniform vec2 resolution;
    uniform vec2 offset = vec2(0.0, 0.0);
    uniform vec2 scale = vec2(1.0, 1.0);

    in vec2 position;

    void main()
    {
        vec2 p = position * scale + offset;
        gl_Position = vec4(p / resolution * 2.0f - 1.0f, 0.0f, 1.0f);
    }
''',

'''
    uniform vec4 color;

    void main()
    {
        gl_FragColor = color;
    }
'''
)

jbuffermap_shader = make_shader('''
    uniform mat4 viewProjectionMatrix;
    uniform mat4 modelMatrix;

    in vec3 pos;
    in vec3 origin;
    in vec3 j0;
    in vec3 j1;
    in vec3 j2;
    in vec3 j3;

    out float l0;
    out float l1;
    out vec3 vj0;
    out vec3 vj1;
    out vec3 vj2;
    out vec3 vj3;

    void main()
    {
        l0 = length(j0 - origin);
        l1 = length(j1 - origin);
        vj0 = j0;
        vj1 = j1;
        vj2 = j2;
        vj3 = j3;
        gl_Position = viewProjectionMatrix * modelMatrix * vec4(pos, 1.0f);
    }
''',

'''
    const vec3[] palette = vec3[](
        vec3(0.9764705882352941, 0.2549019607843137, 0.26666666666666666),
        vec3(0.9725490196078431, 0.5882352941176471, 0.11764705882352941),
        vec3(0.9764705882352941, 0.7803921568627451, 0.30980392156862746),
        vec3(0.5647058823529412, 0.7450980392156863, 0.42745098039215684),
        vec3(0.2627450980392157, 0.6666666666666666, 0.5450980392156862),
        vec3(0.3411764705882353, 0.4588235294117647, 0.5647058823529412),
        vec3(0.4666666666666667, 0.3254901960784314, 0.6352941176470588)
    );
    const float threshold = 1e-2;

    uniform vec2 mouse;
    uniform int has_mouse;
    uniform float radius;

    in float l0;
    in float l1;
    in vec3 vj0;
    in vec3 vj1;
    in vec3 vj2;
    in vec3 vj3;

    layout (location = 0) out vec4 frag_color0;
    layout (location = 1) out vec4 frag_color1;
    layout (location = 2) out vec4 frag_color2;
    layout (location = 3) out vec4 frag_color3;

    void main()
    {
        vec3 c = vec3(0.0);
        float lmax = threshold;
        if (l0 > lmax) {
            c = palette[0];
            lmax = l0;
        }
        if (l1 > lmax) {
            c = palette[1];
            lmax = l1;
        }
        frag_color0 = vec4(vj0, 1.0);
        frag_color1 = vec4(vj1, 1.0);
        frag_color2 = vec4(vj2, 1.0);
        frag_color3 = vec4(vj3, 1.0);

        if (has_mouse == 1) {
            float distance = length(gl_FragCoord.xy - mouse);
            float mask = smoothstep(radius * 1.05, radius * 0.95, distance);;
            frag_color0.a = mask;
            frag_color1.a = mask;
            frag_color2.a = mask;
            frag_color3.a = mask;
        }
    }
'''
)

tex2points_shader = gpu.types.GPUShader('''
    const vec4[] palette = vec4[](
        vec4(0.9764705882352941, 0.2549019607843137, 0.26666666666666666, 1.0),
        vec4(0.9725490196078431, 0.5882352941176471, 0.11764705882352941, 1.0),
        vec4(0.9764705882352941, 0.7803921568627451, 0.30980392156862746, 1.0),
        vec4(0.5647058823529412, 0.7450980392156863, 0.42745098039215684, 1.0),
        vec4(0.2627450980392157, 0.6666666666666666, 0.5450980392156862, 1.0),
        vec4(0.3411764705882353, 0.4588235294117647, 0.5647058823529412, 1.0),
        vec4(0.4666666666666667, 0.3254901960784314, 0.6352941176470588, 1.0)
    );

    uniform sampler2D image;
    uniform int width;
    uniform vec2 resolution;

    out vec4 vColor;

    void main()
    {
        ivec2 coord = ivec2(gl_VertexID % width, gl_VertexID / width);
        vec2 fcoord = (vec2(coord) + vec2(0.5)) / resolution;
        vColor = vec4(fcoord, 0.0, 1.0);
        vec4 color = texelFetch(image, coord, 0);
        vColor = color;
        if (length(color - palette[0]) < 1e-4) {
        //if (color.a > 0.1) {
            gl_Position = vec4(0.0f, 0.0f, 0.0f, 1.0f);
        }
        else {
            gl_Position = vec4(1.0f, 0.0f, 0.0f, 1.0f);
        }
        gl_Position = vec4(fcoord.x * 2.0 - 1.0, fcoord.y * 2.0 - 1.0, 0.0f, 1.0f);
    }
''',

'''
    uniform float one;

    in vec4 vColor;

    layout (location = 0) out vec4 out_color0;
    layout (location = 1) out vec4 out_color1;

    void main()
    {
        out_color0 = vColor;
        out_color1 = vec4(0.6, 0.4, 1.0, 1.0);
    }
'''
)

jbuffer_reduce_shader = gpu.types.GPUShader('''
    uniform sampler2D jbuffermaps[4];
    uniform int width;
    uniform vec2 resolution;
    uniform int param_count;

    out vec4 vColor;

    void main()
    {
        int param = gl_VertexID % param_count;
        int pixelIndex = gl_VertexID / param_count;
        ivec2 coord = ivec2(pixelIndex % width, pixelIndex / width);
        
        vec2 fcoord = (vec2(param, 0) + vec2(0.5)) / resolution;
        
        vec4 color = texelFetch(jbuffermaps[param], coord, 0);
        vColor = color;

        //gl_Position = vec4(fcoord.x * 2.0 - 1.0, fcoord.y * 2.0 - 1.0, 0.0f, 1.0f);
        gl_Position = vec4((float(param) + 0.5)/float(param_count) * 2.0 - 1.0f, 0.0f, 0.0f, 1.0f);
        
        //0, 1, 2, 3
        //0.5, 1.5, 2.5, 3.5
        //-0.5, 0.0, 0.5, 1.0
    }
''',

'''
    in vec4 vColor;

    out vec4 frag_color;

    void main()
    {
        frag_color = vec4(vColor.rgb * vColor.a, vColor.a);
    }
'''
)
