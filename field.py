import pyglet
import clipboard

from element import Element
from utils import x_y_pan_scale
from draw import *


class Field(Element):
    ''' Field is a white box where you can put values
    '''

    def __init__(self, x, y, code=None, connects=None, size=None):
        Element.__init__(self, x, y, (230, 230, 230))
        self.init_processor()

        if not size is None:
            self.w = size[0]
            self.h = size[1]

        if not connects is None:
            self.connectedTo = connects

        if code is None:
            self.code = '0'
        else:
            self.code = code

        self.document = pyglet.text.document.FormattedDocument(self.code)
        self.document.set_style(0, len(self.document.text),
                                dict(font_name='Consolas',
                                font_size=12, color=(0, 0, 0, 255)))
        self.layout = pyglet.text.layout.IncrementalTextLayout(self.document,
                                                     self.w - 30, self.h - 3,
                                                     multiline=True)
        self.caret = pyglet.text.caret.Caret(self.layout)
        self.caret.color = (0, 0, 0)
        self.caret.visible = False

        self.incr = False
        self.resize = False

        self.inputs = ('input',)
        self.outputs = ('output',)
        self.insert_inouts({'inputs': self.inputs, 'outputs': self.outputs})

        self.pan_scale = [[0.0, 0.0], 1]
        self.screen_size = (800, 600)

        self.style(new=True)

    def init_processor(self):
        ''' Processor manages calculation side of pyno
        '''
        self.proc_result = None

        self.value = None
        self.is_number = True

        self.need_update = True
        self.problem = False
        self.gen_output = {'output': None}

    def processor(self, space):
        ''' Processor called every frame
        '''
        if self.proc_result:
            return self.proc_result

        self.problem = False

        # if field is a child
        if self.connectedTo:
            connection = self.connectedTo[0]
            try:
                inputs = connection['output']['node'].processor(space)
                data = inputs[connection['output']['put']['name']]
            except:
                self.er_label.text = 'Cant read input'
                self.problem = True
            else:
                self.document.text = repr(data)
                self.is_number = False
                self.gen_output['output'] = data

        # update value carefully and check some stuff
        elif self.need_update:
            try:
                self.value = eval(self.document.text, space)
            except Exception as ex:
                self.problem = True
                self.er_label.text = str(ex)
                self.is_number = False
                try:
                    exec(self.document.text, space)
                except Exception as ex:
                    self.problem = True
                    self.er_label.text = str(ex)
                else:
                    self.problem = False
            else:
                self.is_number = (isinstance(self.value, (int, float))
                                  and not self.connectedTo)

            self.gen_output['output'] = self.value
            self.need_update = False

        # run-time mode
        else:
            self.gen_output['output'] = self.value

        self.proc_result = self.gen_output
        return self.gen_output

    def render_base(self, batch):
        super().render_base(batch)
        if self.is_number:
            quad(self.x - self.cw + 10, self.y, 10, self.ch,
                          (172, 150, 83), batch)
        if self.hover:
            quad(self.x + self.cw - 5, self.y - self.ch + 5, 5, 5,
                 (50, 50, 50), batch)

    def render(self):
        super().render()

        self.layout.draw()

    def style(self, new=False):
        ''' Vary how represent value, for numbers there is inc/decrement slider
        '''
        l = self.layout
        if new:
            self.document.set_style(0, len(self.document.text),
                                    {'align': 'center'})
            l.x = self.x - self.cw + 15
            l.y = self.y - self.ch + 5
            l.width = self.w - 30
            l.height = self.h - 10
            return

        if self.is_number:
            self.document.set_style(0, len(self.document.text),
                                    {'align': 'right'})
            l.x = self.x - self.cw + 30
            l.y = self.y - self.ch + 5
            l.width = self.w - 45
            l.height = self.h - 10

        else:
            self.document.set_style(0, len(self.document.text),
                                    {'align': 'left'})
            l.x = self.x - self.cw + 15
            l.y = self.y - self.ch + 5
            l.width = self.w - 30
            l.height = self.h - 10

    def resize_field(self):
        self.w += self.layout.view_x
        self.h -= self.layout.view_y
        self.cw, self.ch = self.w // 2, self.h // 2

    def intersect_point(self, point, visual=True):
        self.style()
        if self.is_number:
            self.intersect_incr(point)
        self.intersect_corner(point)
        return super().intersect_point(point, visual)

    def intersect_incr(self, point):
        ''' Intersect with inc/decrement slider, to fast value change
        '''
        intersect = (0 < point[0] - (self.x - self.cw) < 20 and
                     0 < point[1] - (self.y - self.ch) < self.h)
        self.incr = intersect
        return intersect

    def intersect_corner(self, point):
        ''' Intersect bottom right corner to resize
        '''
        intersect = (0 < point[0] - (self.x + self.cw - 10) < 10 and
                     0 < point[1] - (self.y - self.ch) < 10)
        self.resize = intersect
        return intersect

    # --- Input events ---

    def on_mouse_press(self, x, y, button, modifiers):
        x, y = x_y_pan_scale(x, y, self.pan_scale, self.screen_size)

        if button == 1:
            if self.hover:
                self.set_focus()
                self.caret.on_mouse_press(x, y, button, modifiers)
            else:
                self.lost_focus()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        x, y = x_y_pan_scale(x, y, self.pan_scale, self.screen_size)
        dx, dy = int(dx / self.pan_scale[1]), int(dy / self.pan_scale[1])

        if buttons == 1:
            if self.incr:
                t = self.document.text
                n = float(t) if '.' in t else int(t)
                i = dy / 10 if (modifiers == 1 or modifiers == 17) else dy
                r = n + i
                s = str(r) if isinstance(r, int) else "%.2f" % r
                self.document.text = s
                self.caret.visible = False
                self.caret.position = self.caret.mark = len(self.document.text)
                self.resize_field()
                self.x -= dx
                self.y -= dy
                self.need_update = True
            elif self.resize:
                self.w = max(self.w + dx * 2, 70)
                self.h = max(self.h - dy * 2, 30)
                self.x -= dx
                self.y -= dy
            elif self.hover and self.caret.visible:
                self.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
                self.x -= dx
                self.y -= dy
        self.style()

    def on_text(self, text):
        self.caret.on_text(text)
        self.resize_field()

    def on_text_motion(self, motion):
        self.caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        self.caret.on_text_motion_select(motion)

    def on_key_press(self, symbol, modifiers):
        self.style()
        self.problem = False
        self.need_update = True
        key = pyglet.window.key

        if symbol == key.TAB:
            self.document.insert_text(self.caret.position, '    ')
            self.caret.position += 4

        elif modifiers & key.MOD_CTRL:
            if symbol == key.C:
                start = min(self.caret.position, self.caret.mark)
                end = max(self.caret.position, self.caret.mark)
                text = self.document.text[start:end]
                clipboard.copy(text)
            elif symbol == key.V:
                text = clipboard.paste()
                self.document.insert_text(self.caret.position, text)
                self.caret.position += len(text)

    def set_focus(self):
        self.caret.visible = True
        self.caret.mark = 0
        self.caret.position = len(self.document.text)

    def lost_focus(self):
        self.caret.visible = False
        self.caret.mark = self.caret.position = 0
