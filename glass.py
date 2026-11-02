"""Raster glass controls with crisp canvas text, icons and damped tap feedback."""
import math
import time
from functools import lru_cache
import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageTk

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


@lru_cache(maxsize=16)
def rail_lens(width, height, dark):
    """Soft capsule lighting, without a stroked outline or decorative arc."""
    scale = 2
    size = (width*scale, height*scale)
    base = '#243747' if dark else '#DEEBF8'
    surface = Image.new('RGBA', size)
    pixels = surface.load()
    for y in range(size[1]):
        ny = (y+.5)/size[1]*2-1
        for x in range(size[0]):
            nx = (x+.5)/size[0]*2-1
            crown = -.67+.18*nx*nx
            light = math.exp(-((ny-crown)/.24)**2)*math.exp(-(nx/.96)**4)
            shade = math.exp(-((ny-.75)/.28)**2)
            color = blend(base, '#FFFFFF', light*.065)
            color = blend(color, '#0D1725', shade*.035)
            pixels[x, y] = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))+(255,)
    mask = Image.new('L', size)
    ImageDraw.Draw(mask).rounded_rectangle((1, 1, size[0]-2, size[1]-2), radius=height, fill=255)
    surface.putalpha(mask)
    surface = surface.resize((width, height), Image.Resampling.LANCZOS)
    padding = max(8, round(height*.30))
    shadow_mask = Image.new('L', (width+padding*2, height+padding*2))
    shadow_mask.paste(surface.getchannel('A'), (padding, padding+2))
    shadow = Image.new('RGBA', shadow_mask.size, (5, 18, 36, 0))
    shadow.putalpha(shadow_mask.filter(ImageFilter.GaussianBlur(height*.11)).point(lambda a: round(a*(.13 if dark else .055))))
    return surface, shadow, padding


class GlassRail(ctk.CTkFrame):
    """One composited surface lets a spring-driven lens move between destinations."""
    def __init__(self, parent, app, keys, glyphs):
        self.ready = False
        super().__init__(parent, height=len(keys)*54, fg_color=RAIL, corner_radius=0)
        self.app, self.keys, self.glyphs = app, keys, glyphs
        self.fonts = (font(app, 16), font(app, 16, True))
        self.position = self.target = self.velocity = 0.
        self.selected = 0
        self.pointer_origin = None
        self.held = self.dragging = False
        self.hold_amount = self.grab_anchor = 0.
        self.hovered = None
        self.job = None
        self.timer = AnimationTimer()
        self.items = {key: RailItem(self, i) for i, key in enumerate(keys)}
        self.photos = []
        self._lens_photos = {}
        self._caption_key = None
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, takefocus=1, cursor='hand2')
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda _: self.draw())
        self.canvas.bind('<Motion>', self.motion)
        self.canvas.bind('<Leave>', self.leave)
        self.canvas.bind('<ButtonPress-1>', self.pointer_press)
        self.canvas.bind('<B1-Motion>', self.pointer_slide)
        self.canvas.bind('<ButtonRelease-1>', self.pointer_release)
        self.canvas.bind('<Escape>', self.cancel_pointer)
        self.canvas.bind('<FocusOut>', self.cancel_pointer)
        self.canvas.bind('<Up>', lambda _: self.move(-1))
        self.canvas.bind('<Down>', lambda _: self.move(1))
        self.canvas.bind('<Return>', lambda _: self.app.navigate(self.keys[self.selected]))
        self.canvas.bind('<space>', lambda _: self.app.navigate(self.keys[self.selected]))
        self.ready = True

    def move(self, delta):
        self.cancel_pointer()
        self.app.navigate(self.keys[max(0, min(len(self.keys)-1, self.selected+delta))])

    def motion(self, event):
        index = int(event.y / max(1, self._apply_widget_scaling(54)))
        if index != self.hovered:
            self.hovered = index
            self.draw()

    def leave(self, _event):
        self.hovered = None
        self.draw()

    def pointer_press(self, event):
        self.canvas.focus_set()
        self.pointer_origin = (event.x, event.y)
        x, y, width, height = getattr(self, 'lens_bounds', (0, 0, 0, 0))
        self.held = x <= event.x <= x+width and y <= event.y <= y+height
        self.dragging = False
        if self.held:
            self.grab_anchor = event.y / self._apply_widget_scaling(54) - self.position
            self.target, self.velocity = self.position, 0.
            self.canvas.grab_set()
            self.wake()
        return 'break'

    def pointer_slide(self, event):
        if not self.held or self.pointer_origin is None:
            return
        if not self.dragging and abs(event.y-self.pointer_origin[1]) < self._apply_widget_scaling(3):
            return
        self.dragging = True
        self.target = max(0., min(len(self.keys)-1., event.y/self._apply_widget_scaling(54)-self.grab_anchor))
        self.wake()
        return 'break'

    def release_pointer(self):
        self.pointer_origin = None
        self.held = self.dragging = False
        if self.canvas.grab_current() is self.canvas:
            self.canvas.grab_release()

    def pointer_release(self, event):
        if self.pointer_origin is None:
            return
        index = math.floor(self.target+.5) if self.dragging else int(event.y/self._apply_widget_scaling(54))
        inside = 0 <= event.x <= self.canvas.winfo_width() and 0 <= event.y < self.canvas.winfo_height()
        choose = self.dragging or inside
        self.release_pointer()
        try:
            if choose and 0 <= index < len(self.keys):
                self.app.navigate(self.keys[index])
        finally:
            self.target = float(self.selected)
            self.wake()
        return 'break'

    def cancel_pointer(self, _event=None):
        if self.pointer_origin is None:
            return
        self.release_pointer()
        self.target = float(self.selected)
        self.wake()
        return 'break'

    def select(self, index):
        self.selected = index
        if self.held:
            return
        if self.target == index:
            return
        self.target = float(index)
        self.wake()

    def wake(self):
        if self.job is not None:
            return
        self.last_tick = time.perf_counter()
        self.job = self.timer.schedule(self, 1, self.animate)

    def animate(self):
        self.job = None
        now = time.perf_counter()
        dt = min(.12, max(.001, now-self.last_tick))
        self.last_tick = now
        omega = 22. if self.held else 18.
        offset = self.position-self.target
        coefficient = self.velocity+omega*offset
        decay = math.exp(-omega*dt)
        self.position = self.target+(offset+coefficient*dt)*decay
        self.velocity = (self.velocity-omega*coefficient*dt)*decay
        hold_target = float(self.held)
        self.hold_amount += (hold_target-self.hold_amount)*(1-math.exp(-24*dt))
        moving = abs(self.position-self.target) >= .001 or abs(self.velocity) >= .01
        swelling = abs(self.hold_amount-hold_target) > .002
        if not moving:
            self.position = self.target
            self.velocity = 0.
        if not swelling:
            self.hold_amount = hold_target
        if moving or swelling:
            self.job = self.timer.schedule(self, 16, self.animate)
        else:
            self.timer.stop()
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
        if not canvas.find_withtag('rail_lens'):
            canvas.create_image(0, 0, tags='rail_lens')
            for i in range(len(self.keys)):
                canvas.create_image(0, 0, tags=f'rail_icon_{i}')
                canvas.create_text(0, 0, anchor='w', tags=f'rail_text_{i}')
        lens_width = max(12, round(width-22*scale))
        lens_height = max(12, round(42*scale))
        surface, shadow, padding = rail_lens(lens_width, lens_height, dark)
        travel = 1-math.exp(-abs(self.velocity)/12)
        sw = round(lens_width*(1+.025*self.hold_amount+.015*travel))
        sh = round(lens_height*(1+.12*self.hold_amount+.13*travel))
        image_key = (lens_width, lens_height, sw, sh, dark)
        if image_key not in self._lens_photos:
            stretched = surface.resize((sw, sh), Image.Resampling.BICUBIC)
            local = Image.new('RGBA', (sw+padding*2, sh+padding*2))
            local.alpha_composite(shadow.resize(local.size, Image.Resampling.BICUBIC))
            local.alpha_composite(stretched, (padding, padding))
            if len(self._lens_photos) >= 64:
                self._lens_photos.clear()
            self._lens_photos[image_key] = ImageTk.PhotoImage(local, master=self)
        center_y = self.position*step+step/2
        self.lens_bounds = ((width-sw)/2, center_y-sh/2, sw, sh)
        self._current_lens = self._lens_photos[image_key]
        canvas.itemconfigure('rail_lens', image=self._current_lens)
        canvas.coords('rail_lens', width/2, center_y)
        active_index = max(0, min(len(self.keys)-1, math.floor(self.position+.5)))
        caption_key = (scale, dark, active_index, self.hovered,
                       tuple(self.items[k].options.get('text', self.app.tr(k)) for k in self.keys))
        if caption_key == self._caption_key:
            return
        self._caption_key = caption_key
        self.photos = []
        for i, key in enumerate(self.keys):
            active = i == max(0, min(len(self.keys)-1, math.floor(self.position+.5)))
            color = BLUE if active else self._apply_appearance_mode(INK)
            if self.hovered == i and not active:
                color = blend(color, BLUE, .32)
            glyph = icon(self.glyphs[key], 21, accent=active)
            photo = glyph.create_scaled_photo_image(scale, self._get_appearance_mode())
            self.photos.append(photo)
            canvas.itemconfigure(f'rail_icon_{i}', image=photo)
            canvas.coords(f'rail_icon_{i}', 24*scale, i*step+step/2)
            item = self.items[key]
            canvas.itemconfigure(f'rail_text_{i}', text=item.options.get('text', self.app.tr(key)),
                anchor='w', fill=color, font=self._apply_font_scaling(self.fonts[active]))
            canvas.coords(f'rail_text_{i}', 48*scale, i*step+step/2)

    def destroy(self):
        self.release_pointer()
        if self.job is not None:
            self.after_cancel(self.job)
        self.timer.stop()
        super().destroy()
