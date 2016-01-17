import pygame
from .container import Panel, Container
from .slider import Slider
from .util import clamp
from tingbot.graphics import _xy_subtract, _xy_add


class VirtualPanel(Panel):

    """This class implements a virtual panel"""

    def __init__(self, size, parent):
        super(VirtualPanel, self).__init__((0, 0), size, "topleft", parent)
        self.init_size = size

    def _create_surface(self):
        return pygame.Surface(self.init_size, 0, self.parent.surface)

    def get_abs_position(self):
        if hasattr(self.parent, "position"):
            return _xy_subtract(self.parent.get_abs_position(), self.parent.position)
        else:
            super(VirtualPanel, self).get_abs_position()


class ViewPort(Container):

    """the viewport is a container that only has one child, a VirtualPanel"""

    def __init__(self, xy, size, align="center", parent=None,
                 canvas_size=None, vslider=None, hslider=None):
        super(ViewPort, self).__init__(xy, size, align, parent)
        self.panel = VirtualPanel(canvas_size, self)
        self.position = [0, 0]
        self.max_position = [
            max(0, canvas_size[0] - size[0]), max(0, canvas_size[1] - size[1])]
        self.vslider = vslider
        self.hslider = hslider
        if self.vslider:
            self.vslider.max_val = self.max_position[1]
            self.vslider.value = self.max_position[1]
            self.vslider.change_callback = self.vslider_cb
        if self.hslider:
            self.hslider.max_val = self.max_position[0]
            self.hslider.change_callback = self.set_x

    def set_x(self, value):
        value = clamp(0, self.max_position[0], int(value))
        self.position[0] = value
        if self.hslider:
            self.hslider.value = value
        self.update()

    def set_y(self, value, inverted=False):
        value = clamp(0, self.max_position[1], int(value))
        self.position[1] = int(value)
        if self.vslider:
            self.vslider.value = self.max_position[1] - value
        self.update()

    def vslider_cb(self, value):
        value = self.max_position[1] - value
        self.set_y(value)

    def on_touch(self, xy, action):
        # translate xy positions to account for panel position, and pass on to
        # the panel for processing
        self.panel.on_touch(_xy_add(xy, self.position), action)

    def draw(self):
        self.surface.blit(self.panel.surface, (
            0, 0), pygame.Rect(self.position, self.size))


class ScrollArea(Container):

    """Use this class to specify a sub-window with (optional) scrollbars
    style: specify the style of your sliders
    canvas_size: specify the size of the underlying window

    Style Attributes:
        scrollbar_width: width of the scrollbars
        slider_line_color: color of the line
        slider_handle_color: color of the handle
    """

    def __init__(self, xy, size, align="center",
                 parent=None, style=None, canvas_size=None):
        if canvas_size is None:
            raise ValueError("canvas_size must be specified")
        super(ScrollArea, self).__init__(xy, size, align, parent, style)
        rect = pygame.Rect((0, 0), size)
        self.top_surface = self.surface
        self.vslider = None
        self.hslider = None
        vscrollbar = False
        hscrollbar = False
        if canvas_size[0] > rect.right:
            rect.height -= self.style.scrollbar_width
            hscrollbar = True
        if canvas_size[1] > rect.bottom:
            rect.width -= self.style.scrollbar_width
            vscrollbar = True
        if canvas_size[0] > rect.right and not hscrollbar:
            rect.height -= self.style.scrollbar_width
            hscrollbar = True
        if vscrollbar:
            self.vslider = Slider(
                xy=rect.topright,
                size=(
                    self.style.scrollbar_width,
                    rect.bottom),
                align = 'topleft',
                parent=self,
                style=style)
        if hscrollbar:
            self.hslider = Slider(
                xy=rect.bottomleft,
                size=(rect.right,
                      self.style.scrollbar_width),
                align = 'topleft',
                parent=self,
                style=style)
        self.viewport = ViewPort((0, 0), rect.bottomright,
                                 align=align,
                                 parent=self,
                                 canvas_size=canvas_size,
                                 vslider=self.vslider,
                                 hslider=self.hslider)

    def update(self, upwards=True, downwards=False):
        """Call this method to redraw the widget. The widget will only be drawn if visible
        upwards: set to True to ask any parents (and their parents) to redraw themselves
        downwards: set to True to make any children  redraw themselves
        """
        super(ScrollArea, self).update(upwards, downwards)
        if self.visible:
            if self.vslider:
                self.vslider.update(upwards=False)
            if self.hslider:
                self.hslider.update(upwards=False)

    def draw(self):
        # all drawing functions are provided by this classes children
        pass

    @property
    def scrolled_area(self):
        return self.viewport.panel
