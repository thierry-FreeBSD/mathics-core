# -*- coding: utf-8 -*-

"""
Format a Mathics object as an Aymptote string
"""

from mathics.builtin.graphics import (
    _Color,
    _ArcBox,
    ArrowBox,
    BezierCurveBox,
    FilledCurveBox,
    GraphicsBox,
    GraphicsElements,
    InsetBox,
    LineBox,
    PointBox,
    PolygonBox,
    RGBColor,
    RectangleBox,
    _RoundBox,
)

from mathics.builtin.drawing.graphics3d import (
    Graphics3DElements,
    Line3DBox,
    Point3DBox,
    Polygon3DBox,
    Sphere3DBox,
)

from mathics.core.formatter import lookup_method, add_conversion_fn
from mathics.formatter.asy_fns import asy_bezier, asy_color as _color, asy_create_pens, asy_number


class _ASYTransform:
    _template = """
    add(%s * (new picture() {
        picture saved = currentpicture;
        picture transformed = new picture;
        currentpicture = transformed;
        %s
        currentpicture = saved;
        return transformed;
    })());
    """

    def __init__(self):
        self.transforms = []

    def matrix(self, a, b, c, d, e, f):
        # a c e
        # b d f
        # 0 0 1
        # see http://asymptote.sourceforge.net/doc/Transforms.html#Transforms
        self.transforms.append("(%f, %f, %f, %f, %f, %f)" % (e, f, a, c, b, d))

    def translate(self, x, y):
        self.transforms.append("shift(%f, %f)" % (x, y))

    def scale(self, x, y):
        self.transforms.append("scale(%f, %f)" % (x, y))

    def rotate(self, x):
        self.transforms.append("rotate(%f)" % x)

    def apply(self, asy):
        return self._template % (" * ".join(self.transforms), asy)


def arrowbox(self) -> str:
    width = self.style.get_line_width(face_element=False)
    pen = asy_create_pens(edge_color=self.edge_color, stroke_width=width)
    polyline = self.curve.make_draw_asy(pen)

    arrow_pen = asy_create_pens(face_color=self.edge_color, stroke_width=width)

    def polygon(points):
        yield "filldraw("
        yield "--".join(["(%.5g,%5g)" % xy for xy in points])
        yield "--cycle, % s);" % arrow_pen

    extent = self.graphics.view_width or 0
    default_arrow = self._default_arrow(polygon)
    custom_arrow = self._custom_arrow("asy", _ASYTransform)
    return "".join(self._draw(polyline, default_arrow, custom_arrow, extent))


add_conversion_fn(ArrowBox)


def beziercurvebox(self) -> str:
    line_width = self.style.get_line_width(face_element=False)
    pen = asy_create_pens(edge_color=self.edge_color, stroke_width=line_width)

    asy = ""
    for line in self.lines:
        for path in asy_bezier((self.spline_degree, [xy.pos() for xy in line])):
            if path[:2] == "..":
                path = "(0.,0.)" + path
            asy += "draw(%s, %s);" % (path, pen)
    return asy
    if self.arc is None:
        return _roundbox(self)

    x, y, rx, ry, sx, sy, ex, ey, large_arc = self._arc_params()


add_conversion_fn(BezierCurveBox)


def filledcurvebox(self) -> str:
    line_width = self.style.get_line_width(face_element=False)
    pen = asy_create_pens(edge_color=self.edge_color, stroke_width=line_width)

    if not pen:
        pen = "currentpen"

    def components():
        for component in self.components:
            transformed = [(k, [xy.pos() for xy in p]) for k, p in component]
            yield "fill(%s--cycle, %s);" % ("".join(asy_bezier(*transformed)), pen)

    return "".join(components())


add_conversion_fn(FilledCurveBox)

# FIXME figure out how we can add this.
def graphicsbox(self, leaves=None, **options) -> str:
    if not leaves:
        leaves = self._leaves

    data = options.get("data", None)
    if data:
        elements, xmin, xmax, ymin, ymax, w, h, width, height = data
    else:
        elements, calc_dimensions = self._prepare_elements(leaves, options, neg_y=True)
        xmin, xmax, ymin, ymax, w, h, width, height = calc_dimensions()

    elements.view_width = w

    format_fn = lookup_method(elements, "svg")
    if format_fn is not None:
        svg_body = format_fn(elements, offset=options.get("offset", None))
    else:
        svg_body = elements.to_svg(offset=options.get("offset", None))

    if self.background_color is not None:
        # Wrap svg_elements in a rectangle
        svg_body = '<rect x="%f" y="%f" width="%f" height="%f" style="fill:%s"/>%s' % (
            xmin,
            ymin,
            w,
            h,
            self.background_color.to_css()[0],
            svg_body,
        )

    xmin -= 1
    ymin -= 1
    w += 2
    h += 2

    if options.get("noheader", False):
        return svg_body
    svg_main = """
            <svg xmlns:svg="http://www.w3.org/2000/svg"
                xmlns="http://www.w3.org/2000/svg"
                version="1.1"
                viewBox="%s">
                %s
            </svg>
        """ % (
        " ".join("%f" % t for t in (xmin, ymin, w, h)),
        svg_body,
    )
    return svg_main  # , width, height


add_conversion_fn(GraphicsBox)


def graphicselements(self) -> str:
    result = []
    for element in self.elements:
        format_fn = lookup_method(element, "asy")
        if format_fn is None:
            result.append(element.to_asy(offset))
        else:
            result.append(format_fn(element))

    return "\n".join(result)


add_conversion_fn(GraphicsElements)
graphics3delements = graphicselements


add_conversion_fn(Graphics3DElements)


def insetbox(self) -> str:
    x, y = self.pos.pos()
    content = self.content.boxes_to_tex(evaluation=self.graphics.evaluation)
    pen = asy_create_pens(edge_color=self.color)
    asy = 'label("$%s$", (%s,%s), (%s,%s), %s);' % (
        content,
        x,
        y,
        -self.opos[0],
        -self.opos[1],
        pen,
    )
    return asy


add_conversion_fn(InsetBox)


def line3dbox(self):
    # l = self.style.get_line_width(face_element=False)
    pen = asy_create_pens(edge_color=self.edge_color, stroke_width=1)

    return "".join(
        "draw({0}, {1});".format(
            "--".join("({0},{1},{2})".format(*coords.pos()[0]) for coords in line),
            pen,
        )
        for line in self.lines
    )


add_conversion_fn(Line3DBox)


def linebox(self) -> str:
    line_width = self.style.get_line_width(face_element=False)
    pen = asy_create_pens(edge_color=self.edge_color, stroke_width=line_width)
    asy = ""
    for line in self.lines:
        path = "--".join(["(%.5g,%5g)" % coords.pos() for coords in line])
        asy += "draw(%s, %s);" % (path, pen)
    # print("### linebox", asy)
    return asy


add_conversion_fn(LineBox)


def point3dbox(self) -> str:
    face_color = self.face_color

    # Tempoary bug fix: default Point color should be black not white
    if list(face_color.to_rgba()[:3]) == [1, 1, 1]:
        face_color = RGBColor(components=(0, 0, 0, face_color.to_rgba()[3]))

    pen = asy_create_pens(face_color=face_color, is_face_element=False)

    return "".join(
        "path3 g={0}--cycle;dot(g, {1});".format(
            "--".join("(%.5g,%.5g,%.5g)" % coords.pos()[0] for coords in line), pen
        )
        for line in self.lines
    )


add_conversion_fn(Point3DBox)


def pointbox(self) -> str:
    pen = asy_create_pens(face_color=self.face_color, is_face_element=False)

    asy = ""
    for line in self.lines:
        for coords in line:
            asy += "dot(%s, %s);" % (coords.pos(), pen)

    # print("### pointbox", asy)
    return asy


add_conversion_fn(PointBox)


def polygon3dbox(self) -> str:
    l = self.style.get_line_width(face_element=True)
    if self.vertex_colors is None:
        face_color = self.face_color
    else:
        face_color = None
    pen = asy_create_pens(
        edge_color=self.edge_color,
        face_color=face_color,
        stroke_width=l,
        is_face_element=True,
    )

    asy = ""
    for line in self.lines:
        asy += (
            "path3 g="
            + "--".join(["(%.5g,%.5g,%.5g)" % coords.pos()[0] for coords in line])
            + "--cycle;"
        )
        asy += "draw(surface(g), %s);" % (pen)

    # print("### polygon3dbox", asy)
    return asy


add_conversion_fn(Polygon3DBox)


def polygonbox(self):
    line_width = self.style.get_line_width(face_element=True)
    if self.vertex_colors is None:
        face_color = self.face_color
    else:
        face_color = None
    pens = asy_create_pens(
        edge_color=self.edge_color,
        face_color=face_color,
        stroke_width=line_width,
        is_face_element=True,
    )
    asy = ""
    if self.vertex_colors is not None:
        paths = []
        colors = []
        edges = []
        for index, line in enumerate(self.lines):
            paths.append(
                "--".join(["(%.5g,%.5g)" % coords.pos() for coords in line]) + "--cycle"
            )

            # ignore opacity
            colors.append(
                ",".join([_color(color)[0] for color in self.vertex_colors[index]])
            )

            edges.append(",".join(["0"] + ["1"] * (len(self.vertex_colors[index]) - 1)))

        asy += "gouraudshade(%s, new pen[] {%s}, new int[] {%s});" % (
            "^^".join(paths),
            ",".join(colors),
            ",".join(edges),
        )
    if pens and pens != "nullpen":
        for line in self.lines:
            path = (
                "--".join(["(%.5g,%.5g)" % coords.pos() for coords in line]) + "--cycle"
            )
            asy += "filldraw(%s, %s);" % (path, pens)

    # print("### polygonbox", asy)
    return asy


add_conversion_fn(PolygonBox)


def rectanglebox(self) -> str:
    line_width = self.style.get_line_width(face_element=True)
    x1, y1 = self.p1.pos()
    x2, y2 = self.p2.pos()
    pens = asy_create_pens(
        self.edge_color, self.face_color, line_width, is_face_element=True
    )
    x1, x2, y1, y2 = asy_number(x1), asy_number(x2), asy_number(y1), asy_number(y2)
    return "filldraw((%s,%s)--(%s,%s)--(%s,%s)--(%s,%s)--cycle, %s);" % (
        x1,
        y1,
        x2,
        y1,
        x2,
        y2,
        x1,
        y2,
        pens,
    )


add_conversion_fn(RectangleBox)


def _roundbox(self):
    x, y = self.c.pos()
    rx, ry = self.r.pos()
    rx -= x
    ry -= y
    line_width = self.style.get_line_width(face_element=self.face_element)
    pen = asy_create_pens(
        edge_color=self.edge_color,
        face_color=self.face_color,
        stroke_width=line_width,
        is_face_element=self.face_element,
    )
    cmd = "filldraw" if self.face_element else "draw"
    return "%s(ellipse((%s,%s),%s,%s), %s);" % (
        cmd,
        asy_number(x),
        asy_number(y),
        asy_number(rx),
        asy_number(ry),
        pen,
    )


add_conversion_fn(_RoundBox)


def sphere3dbox(self) -> str:
    # l = self.style.get_line_width(face_element=True)

    if self.face_color is None:
        face_color = (1, 1, 1)
    else:
        face_color = self.face_color.to_js()

    return "".join(
        "draw(surface(sphere({0}, {1})), rgb({2},{3},{4}));".format(
            tuple(coord.pos()[0]), self.radius, *face_color[:3]
        )
        for coord in self.points
    )


add_conversion_fn(Sphere3DBox)
