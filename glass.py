"""Raster glass controls with crisp canvas text, icons and damped tap feedback."""
import math
import time
import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

from painting import AnimationTimer
from theme import BLUE, INK, RAIL, font, icon


def blend(a, b, amount):
    a, b = a.lstrip('#'), b.lstrip('#')
    return '#' + ''.join(f'{round(int(a[i:i+2], 16)*(1-amount)+int(b[i:i+2], 16)*amount):02x}' for i in (0, 2, 4))


class GlassButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        self._glass_ready = False
        self._glass_job = None
        self._glass_hover = self._glass_target = 0.
        self._glass_tap = None
        self._glass_timer = AnimationTimer()
        self._glass_photo = self._glass_icon = None
        self._declared_width = kwargs.get('width', 124)
        super().__init__(*args, **kwargs)
        self._canvas.configure(takefocus=1)
        self._canvas.bind('<space>', lambda _: self.invoke())
        self._canvas.bind('<Return>', lambda _: self.invoke())
        self._glass_ready = True
        self.fit()
        self._draw()

    def fit(self):
        measured = tkfont.Font(root=self, font=self._apply_font_scaling(self._font))
        text = measured.measure(self._text or '')
        image_width = self._image.cget('size')[0] + 8 if self._image else 0
        width = max(self._declared_width, math.ceil(self._reverse_widget_scaling(text)) + image_width + 26)
        if self._desired_width != width:
            super().configure(width=width)

    def configure(self, require_redraw=False, **kwargs):
        if 'width' in kwargs:
            self._declared_width = kwargs['width']
        super().configure(require_redraw=require_redraw, **kwargs)
        if self._glass_ready:
            if any(key in kwargs for key in ('text', 'font', 'image')):
                self.fit()
            self.paint()

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)
        if self._glass_ready:
            self.paint()

    def paint(self):
        width = max(2, round(self._apply_widget_scaling(self._current_width)))
        height = max(2, round(self._apply_widget_scaling(self._current_height)))
        if width < 10 or height < 10:
            return
        disabled = self._state == 'disabled'
        hover = 0. if disabled else self._glass_hover
        dark = self._get_appearance_mode() == 'dark'
        background = self._apply_appearance_mode(self._bg_color)
        clear = self._fg_color == 'transparent'
        base = background if clear else self._apply_appearance_mode(self._fg_color)
        base = blend(base, '#A8D9FF', hover * (.13 if dark else .16))
        elapsed = time.perf_counter() - self._glass_tap if self._glass_tap else 1.
        press = math.exp(-elapsed * 13) * math.cos(elapsed * 22) if elapsed < .4 else 0.
        inset = max(0., press * 1.6)
        radius = min(height / 2, self._apply_widget_scaling(self._corner_radius))
        key = (width, height, base, hover, inset, dark, clear, disabled)
        if key != getattr(self, '_surface_key', None):
            scale = 2
            image = Image.new('RGBA', (width * scale, height * scale))
            if not clear or hover > .005 or press > .005:
                gradient = Image.new('RGBA', image.size)
                draw = ImageDraw.Draw(gradient)
                for y in range(height * scale):
                    t = y / max(1, height * scale - 1)
                    sheen = (.10 if dark else .22) * (1-t)**3 + hover * .03
                    color = blend(base, '#FFFFFF', sheen)
                    draw.line((0, y, width * scale, y), fill=color)
                box = (inset*scale, inset*scale, (width-1-inset)*scale, (height-1-inset)*scale)
                mask = Image.new('L', image.size)
                ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius*scale, fill=255)
                gradient.putalpha(mask)
                image = Image.alpha_composite(image, gradient)
                edge = blend(base, '#FFFFFF' if dark else '#75879E', .28 if dark else .18)
                ImageDraw.Draw(image).rounded_rectangle(box, radius=radius*scale, outline=edge, width=2)
                ImageDraw.Draw(image).arc((box[0]+2, box[1]+2, box[2]-2, box[3]-2),
                                         190, 300, fill=blend(base, '#FFFFFF', .48), width=2)
            self._glass_photo = ImageTk.PhotoImage(image.resize((width, height), Image.Resampling.LANCZOS), master=self)
            self._surface_key = key
        canvas = self._canvas
        if not canvas.find_withtag('glass_surface'):
            canvas.create_image(0, 0, anchor='nw', tags='glass_surface')
            canvas.create_image(0, 0, tags='glass_icon')
            canvas.create_text(0, 0, tags='glass_caption')
        canvas.itemconfigure('glass_surface', image=self._glass_photo)
        canvas.tag_raise('glass_surface')
        for label in (self._text_label, self._image_label):
            if label is not None and label.winfo_manager():
                label.grid_remove()
        measured = tkfont.Font(root=self, font=self._apply_font_scaling(self._font))
        text_width = measured.measure(self._text or '')
        image_width = self._apply_widget_scaling(self._image.cget('size')[0]) if self._image else 0
        gap = self._apply_widget_scaling(8) if self._image and self._text else 0
        start = self._apply_widget_scaling(15) if self._anchor == 'w' else (width - text_width - image_width - gap) / 2
        y = height / 2 + press
        if self._image:
            self._glass_icon = self._image.create_scaled_photo_image(self._get_widget_scaling(), self._get_appearance_mode())
            canvas.itemconfigure('glass_icon', image=self._glass_icon, state='normal')
            canvas.coords('glass_icon', start + image_width / 2, y)
            canvas.tag_raise('glass_icon')
        else:
            canvas.itemconfigure('glass_icon', state='hidden')
        canvas.itemconfigure('glass_caption', text=self._text or '', anchor='w',
            font=self._apply_font_scaling(self._font),
            fill=self._apply_appearance_mode(self._text_color_disabled if disabled else self._text_color))
        canvas.coords('glass_caption', start + image_width + gap, y)
        canvas.tag_raise('glass_caption')

    def animate(self):
        self._glass_job = None
        self._glass_hover += (self._glass_target - self._glass_hover) * .30
        tapping = self._glass_tap and time.perf_counter() - self._glass_tap < .4
        self.paint()
        if tapping or abs(self._glass_hover - self._glass_target) > .005:
            self._glass_job = self._glass_timer.schedule(self, 16, self.animate)
        else:
            self._glass_tap = None
            self._glass_timer.stop()

    def start_animation(self):
        if self._glass_ready and self._glass_job is None:
            self._glass_job = self._glass_timer.schedule(self, 16, self.animate)

    def _on_enter(self, event=None):
        if self._state != 'disabled':
            self._glass_target = 1.
            self.start_animation()

    def _on_leave(self, event=None):
        self._glass_target = 0.
        self.start_animation()

    def _clicked(self, event=None):
        if self._state == 'disabled':
            return
        self._glass_tap = time.perf_counter()
        self.start_animation()
        if self._command:
            return self._command()

    def invoke(self):
        return self._clicked()

    def destroy(self):
        if self._glass_job is not None:
            self.after_cancel(self._glass_job)
        self._glass_timer.stop()
        super().destroy()


class RailItem:
    def __init__(self, rail, index):
        self.rail, self.index = rail, index
        self.options = {}

    def configure(self, **kwargs):
        self.options.update(kwargs)
        if kwargs.get('fg_color', 'transparent') != 'transparent':
            self.rail.select(self.index)
        self.rail.draw()


class GlassRail(ctk.CTkFrame):
    """One composited surface lets a spring-driven lens move between destinations."""
    def __init__(self, parent, app, keys, glyphs):
        self.ready = False
        super().__init__(parent, height=len(keys)*54, fg_color=RAIL, corner_radius=0)
        self.app, self.keys, self.glyphs = app, keys, glyphs
        self.fonts = (font(app, 16), font(app, 16, True))
        self.position = self.target = self.velocity = 0.
        self.hovered = None
        self.job = None
        self.timer = AnimationTimer()
        self.items = {key: RailItem(self, i) for i, key in enumerate(keys)}
        self.photos = []
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, takefocus=1)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda _: self.draw())
        self.canvas.bind('<Motion>', self.motion)
        self.canvas.bind('<Leave>', self.leave)
        self.canvas.bind('<Button-1>', self.click)
        self.canvas.bind('<Up>', lambda _: self.move(-1))
        self.canvas.bind('<Down>', lambda _: self.move(1))
        self.canvas.bind('<Return>', lambda _: self.app.navigate(self.keys[round(self.target)]))
        self.canvas.bind('<space>', lambda _: self.app.navigate(self.keys[round(self.target)]))
        self.ready = True

    def move(self, delta):
        self.app.navigate(self.keys[max(0, min(len(self.keys)-1, round(self.target)+delta))])

    def motion(self, event):
        index = int(event.y / max(1, self._apply_widget_scaling(54)))
        if index != self.hovered:
            self.hovered = index
            self.draw()

    def leave(self, _event):
        self.hovered = None
        self.draw()

    def click(self, event):
        self.canvas.focus_set()
        index = int(event.y / max(1, self._apply_widget_scaling(54)))
        if 0 <= index < len(self.keys):
            self.app.navigate(self.keys[index])

    def select(self, index):
        if self.target == index:
            return
        self.target = float(index)
        self.last_tick = time.perf_counter()
        if self.job is None:
            self.job = self.timer.schedule(self, 1, self.animate)

    def animate(self):
        self.job = None
        now = time.perf_counter()
        dt = min(.032, now-self.last_tick)
        self.last_tick = now
        self.velocity += ((self.target-self.position)*190 - self.velocity*23)*dt
        self.position += self.velocity*dt
        if abs(self.position-self.target) < .001 and abs(self.velocity) < .01:
            self.position = self.target
            self.velocity = 0.
            self.timer.stop()
        else:
            self.job = self.timer.schedule(self, 16, self.animate)
        self.draw()

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        if self.ready:
            self.draw()

    def draw(self):
        if not self.ready:
            return
        canvas = self.canvas
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 16 or height < 16:
            return
        scale = self._get_widget_scaling()
        step = 54*scale
        dark = self._get_appearance_mode() == 'dark'
        background = self._apply_appearance_mode(RAIL)
        canvas.configure(bg=background)
        canvas.delete('all')
        lens_width = max(12, width-4*scale)
        stretch = min(10, abs(self.velocity)*1.1)*scale
        lens_height = 46*scale + stretch
        base = '#25445A' if dark else '#DDEEFF'
        size = (round(lens_width*2), round(lens_height*2))
        surface = Image.new('RGBA', size)
        gradient = Image.new('RGBA', size)
        d = ImageDraw.Draw(gradient)
        for y in range(size[1]):
            t = y/max(1, size[1]-1)
            d.line((0, y, size[0], y), fill=blend(base, '#FFFFFF', (.16 if dark else .48)*(1-t)**3))
        mask = Image.new('L', size)
        box = (1, 1, size[0]-2, size[1]-2)
        ImageDraw.Draw(mask).rounded_rectangle(box, radius=16*scale, fill=255)
        gradient.putalpha(mask)
        surface = Image.alpha_composite(surface, gradient)
        edge = ImageDraw.Draw(surface)
        edge.rounded_rectangle(box, radius=16*scale, outline=blend(base, '#FFFFFF' if dark else '#7EADD3', .30), width=2)
        edge.arc((3, 3, size[0]-4, size[1]-4), 190, 300, fill=blend(base, '#FFFFFF', .65), width=2)
        self.photos = [ImageTk.PhotoImage(surface.resize((round(lens_width), round(lens_height)), Image.Resampling.LANCZOS), master=self)]
        canvas.create_image(width/2, self.position*step+step/2, image=self.photos[0])
        for i, key in enumerate(self.keys):
            active = i == round(self.target)
            color = BLUE if active else self._apply_appearance_mode(INK)
            if self.hovered == i and not active:
                canvas.create_line(16*scale, i*step+step-5*scale, width-16*scale, i*step+step-5*scale, fill=blend(background, BLUE, .23))
            glyph = icon(self.glyphs[key], 21, accent=active)
            photo = glyph.create_scaled_photo_image(scale, self._get_appearance_mode())
            self.photos.append(photo)
            canvas.create_image(24*scale, i*step+step/2, image=photo)
            item = self.items[key]
            canvas.create_text(48*scale, i*step+step/2, text=item.options.get('text', self.app.tr(key)),
                anchor='w', fill=color, font=self._apply_font_scaling(self.fonts[active]))

    def destroy(self):
        if self.job is not None:
            self.after_cancel(self.job)
        self.timer.stop()
        super().destroy()
