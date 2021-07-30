# This file is part of DagAmendment, the reference implementation of:
#
#   Michel, Élie and Boubekeur, Tamy (2021).
#   DAG Amendment for Inverse Control of Parametric Shapes
#   ACM Transactions on Graphics (Proc. SIGGRAPH 2021), 173:1-173:14.
#
# Copyright (c) 2020-2021 -- Télécom Paris (Élie Michel <elie.michel@telecom-paris.fr>)
# 
# The MIT license:
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# The Software is provided “as is”, without warranty of any kind, express or
# implied, including but not limited to the warranties of merchantability,
# fitness for a particular purpose and non-infringement. In no event shall the
# authors or copyright holders be liable for any claim, damages or other
# liability, whether in an action of contract, tort or otherwise, arising
# from, out of or in connection with the software or the use or other dealings
# in the Software.

# no bpy here

palette0 = [
       '#f94144', # red
#       '#f3722c',
       '#f8961e',
       '#f9c74f', # cream
       '#90be6d',
       '#43aa8b',
       '#577590', # blue
       '#7753a2',
]

# (0.9764705882352941, 0.2549019607843137, 0.26666666666666666)
# (0.9725490196078431, 0.5882352941176471, 0.11764705882352941)
# (0.9764705882352941, 0.7803921568627451, 0.30980392156862746)
# (0.5647058823529412, 0.7450980392156863, 0.42745098039215684)
# (0.2627450980392157, 0.6666666666666666, 0.5450980392156862)
# (0.3411764705882353, 0.4588235294117647, 0.5647058823529412)
# (0.4666666666666667, 0.3254901960784314, 0.6352941176470588)

def from_html_color(html_color):
    r = int(html_color[1:3], 16) / 255.0
    g = int(html_color[3:5], 16) / 255.0
    b = int(html_color[5:7], 16) / 255.0
    return (r, g, b, 0.5)
