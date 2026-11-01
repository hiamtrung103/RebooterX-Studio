"""Small native widget helpers and vendored Lucide icon rendering."""
from functools import lru_cache
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk
from PIL import Image

BG = ('#F5F6F8', '#17181C')
RAIL = ('#EFF1F5', '#1C1D22')
SURFACE = ('#FFFFFF', '#232429')
FIELD = ('#EBEEF3', '#2B2C33')
INK = ('#20242C', '#F1F2F5')
MUTED = ('#687180', '#A1A6B2')
EDGE = ('#E2E5EB', '#34363F')
BLUE = '#0081F6'
SELECTED = ('#E3EFFF', '#19344F')
GREEN = ('#167A5B', '#62CC9E')
RED = ('#B44749', '#F09192')
AMBER = ('#9A6B20', '#DBB469')
ICON_DIR = Path(__file__).resolve().parent / 'assets' / 'icons'


@lru_cache(maxsize=128)
def icon(name, size=18, accent=False, white=False):
    light = 'white' if white else 'accent' if accent else 'light'
    dark = 'white' if white else 'accent' if accent else 'dark'
    with Image.open(ICON_DIR / f'{name}-{light}.png') as source:
        light_image = source.copy()
    with Image.open(ICON_DIR / f'{name}-{dark}.png') as source:
        dark_image = source.copy()
    return ctk.CTkImage(light_image=light_image, dark_image=dark_image, size=(size, size))


def font(root, size=13, bold=False):
    families = getattr(root, '_font_families', None)
    if families is None:
        root._font_families = families = set(tkfont.families(root))
    for family in ('SF Pro Text', 'Inter', 'Segoe UI Variable Text', 'Segoe UI'):
        if family in families:
            return ctk.CTkFont(family=family, size=size, weight='bold' if bold else 'normal')
    return ctk.CTkFont(size=size, weight='bold' if bold else 'normal')


class ToolTip:
    def __init__(self, widget, text):
        self.widget, self.text = widget, text
        self.job = self.popup = None
        widget.bind('<Enter>', self.enter, add='+')
        widget.bind('<Leave>', self.leave, add='+')
        widget.bind('<Button-1>', self.leave, add='+')

    def enter(self, _event=None):
        self.job = self.widget.after(600, self.show)

    def show(self):
        self.job = None
        if not self.widget.winfo_exists():
            return
        self.popup = ctk.CTkToplevel(self.widget)
        self.popup.overrideredirect(True)
        self.popup.attributes('-topmost', True)
        self.popup.geometry(f'+{self.widget.winfo_rootx()}+{self.widget.winfo_rooty() + self.widget.winfo_height() + 6}')
        ctk.CTkLabel(self.popup, text=self.text(), fg_color=SURFACE,
                     text_color=INK, corner_radius=6, padx=12, pady=6).pack()

    def leave(self, _event=None):
        if self.job:
            self.widget.after_cancel(self.job)
            self.job = None
        if self.popup:
            self.popup.destroy()
            self.popup = None


def wrap(label, physical_width, inset=0):
    logical_width = max(80, int(label._reverse_widget_scaling(physical_width)) - inset)
    if label.cget('wraplength') != logical_width:
        label.configure(wraplength=logical_width)


def two_lines(text, measure, width):
    lines = ['']
    words = text.split()
    for index, word in enumerate(words):
        candidate = (lines[-1] + ' ' + word).strip()
        if measure(candidate) <= width:
            lines[-1] = candidate
        elif len(lines) == 1:
            lines.append(word)
        else:
            while lines[-1] and measure(lines[-1] + '…') > width:
                lines[-1] = lines[-1][:-1]
            lines[-1] = lines[-1].rstrip() + '…'
            break
    return '\n'.join(lines)


def line(parent):
    return ctk.CTkFrame(parent, height=1, corner_radius=0, fg_color=EDGE)
