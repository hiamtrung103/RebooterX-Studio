"""CustomTkinter desktop UI. Only the original upstream CLI applies changes."""
from __future__ import annotations

from collections import deque
import json
import os
from pathlib import Path
import platform
import queue
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox
import unicodedata
import webbrowser

import customtkinter as ctk

import core
from catalog import PACKAGES, TEXT
from theme import (AMBER, BG, BLUE, EDGE, FIELD, GREEN, INK, MUTED, RAIL, RED,
                   SELECTED, SURFACE, ToolTip, font, icon, line, two_lines, wrap)


EXTRA = {
    'all_options': ('All options', 'Tất cả tùy chọn'),
    'performance': ('Performance', 'Hiệu năng'),
    'privacy': ('Privacy', 'Quyền riêng tư'),
    'system': ('Windows & apps', 'Windows & ứng dụng'),
    'protection': ('Security', 'Bảo mật'),
    'selection': ('Selected', 'Đã chọn'),
    'activity': ('Activity', 'Nhật ký'),
    'settings': ('Settings', 'Cài đặt'),
    'library': ('LIBRARY', 'THƯ VIỆN'),
    'preferences': ('WORKSPACE', 'KHÔNG GIAN LÀM VIỆC'),
    'catalog_title': ('Windows tweaks', 'Tùy chỉnh Windows'),
    'catalog_meta': ('{total} packages  ·  Official YAML hub', '{total} gói  ·  Kho YAML chính thức'),
    'search_hint': ('Search options…', 'Tìm tùy chọn…'),
    'all_windows': ('All Windows', 'Mọi Windows'),
    'empty_selection': ('No packages selected', 'Chưa chọn gói nào'),
    'empty_search': ('No matching options', 'Không có tùy chọn phù hợp'),
    'select_package': ('Select package', 'Chọn gói'),
    'deselect_package': ('Deselect package', 'Bỏ chọn gói'),
    'nothing_focused': ('Package details', 'Thông tin gói'),
    'availability': ('Compatibility', 'Tương thích'),
    'signature': ('Signature file', 'File chữ ký'),
    'paired': ('Included · CLI verifies', 'Đi kèm · CLI xác minh'),
    'revision': ('Revision', 'Phiên bản nguồn'),
    'official_source': ('View on GitHub', 'Xem trên GitHub'),
    'appearance': ('Appearance', 'Giao diện'),
    'light': ('Light', 'Sáng'),
    'dark': ('Dark', 'Tối'),
    'cli_ready': ('CLI ready', 'CLI sẵn sàng'),
    'cli_missing': ('CLI not installed', 'Chưa có CLI'),
    'engine_section': ('Execution engine', 'Công cụ thực thi'),
    'personalization': ('Personalization', 'Cá nhân hóa'),
    'project_section': ('Project', 'Dự án'),
    'official_project': ('Official OptimizerNXT', 'OptimizerNXT chính thức'),
    'version': ('OptimizerNXT Studio · 1.0.0', 'OptimizerNXT Studio · 1.0.0'),
    'downloaded': ('Downloaded {name}', 'Đã tải {name}'),
    'downloading': ('Downloading packages…', 'Đang tải các gói…'),
    'running': ('CLI running in its own console', 'CLI đang chạy ở cửa sổ riêng'),
    'catalog_loaded': ('Loaded {count} signed packages', 'Đã nạp {count} gói có chữ ký'),
    'progress_download': ('{done}/{total} packages downloaded', 'Đã tải {done}/{total} gói'),
    'ready_count': ('{count} selected', 'Đã chọn {count}'),
    'download_short': ('Download', 'Tải xuống'),
    'run_short': ('Run selected', 'Chạy đã chọn'),
    'review_title': ('Review selected packages', 'Xem lại các gói đã chọn'),
    'review_meta': ('{count} packages · Administrator', '{count} gói · Quyền quản trị'),
    'review_note': ('Changes can require a restart. Automatic undo is unavailable.', 'Thay đổi có thể cần khởi động lại. Không có hoàn tác tự động.'),
    'cancel': ('Cancel', 'Hủy'),
    'confirm_run': ('Apply packages', 'Áp dụng các gói'),
    'download_success': ('Saved {count} packages', 'Đã lưu {count} gói'),
    'cli_finished': ('CLI closed · exit code {code}', 'CLI đã đóng · mã thoát {code}'),
    'cli_output': ('Check the CLI console/logs for each operation’s result.', 'Xem cửa sổ/log CLI để biết kết quả từng thao tác.'),
    'selection_changed': ('Selection saved', 'Đã lưu lựa chọn'),
    'clear_logs': ('Clear log', 'Xóa nhật ký'),
    'startup': ('Studio started', 'Studio đã khởi động'),
    'no_activity': ('No activity yet', 'Chưa có hoạt động'),
    'log_count': ('{count} events', '{count} sự kiện'),
    'cli_pick_title': ('Select optimizerNXT.exe', 'Chọn optimizerNXT.exe'),
    'cli_hint': ('optimizerNXT.exe', 'optimizerNXT.exe'),
    'data_folder': ('Data folder', 'Thư mục dữ liệu'),
    'privacy_impact': ('Location, ads & personalization', 'Vị trí, quảng cáo và cá nhân hóa'),
    'basic_impact': ('System settings', 'Thiết lập hệ thống'),
}

CATEGORIES = ('all_options', 'performance', 'privacy', 'system', 'protection', 'selection')
NAV_ICONS = {'all_options': 'layers', 'performance': 'gauge', 'privacy': 'lock-keyhole',
             'system': 'settings-2', 'protection': 'shield-check', 'selection': 'check-check',
             'activity': 'history', 'settings': 'sliders-horizontal'}


def normalize(text):
    return ''.join(char for char in unicodedata.normalize('NFD', text.casefold().replace('đ', 'd'))
                   if unicodedata.category(char) != 'Mn')


def category_for(name):
    stem = Path(name).stem
    if stem in ('disable-windows-defender', 'disable-windows-security', 'disable-smartscreen',
                'disable-vbs', 'disable-tpm-enforce', 'disable-system-restore'):
        return 'protection'
    if stem in ('enable-game-mode', 'enable-performance-tweaks', 'disable-superfetch', 'disable-modern-standby'):
        return 'performance'
    if 'telemetry' in stem or stem in ('enhance-privacy', 'disable-copilot'):
        return 'privacy'
    return 'system'


class ReviewDialog(ctk.CTkToplevel):
    def __init__(self, parent, packages):
        super().__init__(parent)
        self.result = False
        self.title(parent.tr('review_title'))
        self.configure(fg_color=BG)
        width, height = 600, min(660, parent.winfo_screenheight() - 130)
        self.geometry(f'{width}x{height}+{parent.winfo_rootx()+80}+{parent.winfo_rooty()+40}')
        self.minsize(520, 460)
        self.transient(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(self, text=parent.tr('review_title'), font=font(parent, 22, True),
                     text_color=INK).grid(row=0, column=0, sticky='w', padx=26, pady=(22, 4))
        ctk.CTkLabel(self, text=parent.tr('review_meta', count=len(packages)), text_color=MUTED,
                     font=font(parent)).grid(row=1, column=0, sticky='w', padx=26, pady=(0, 16))
        scroll = ctk.CTkScrollableFrame(self, fg_color='transparent')
        scroll.grid(row=2, column=0, sticky='nsew', padx=20)
        for package in packages:
            meta = parent.meta(package)
            row = ctk.CTkFrame(scroll, fg_color=SURFACE, corner_radius=8)
            row.pack(fill='x', pady=(0, 8))
            ctk.CTkLabel(row, text=parent.title_for(package), anchor='w', justify='left',
                         wraplength=480, text_color=INK, font=font(parent, 13, True)).pack(fill='x', padx=14, pady=(10, 3))
            if meta[5]:
                ctk.CTkLabel(row, text=parent.tr('sensitive', impact=parent.tr(meta[5])),
                             text_color=RED if meta[5] in ('security', 'restore') else AMBER,
                             wraplength=480, justify='left', font=font(parent, 12)).pack(anchor='w', padx=14, pady=(0, 10))
            else:
                ctk.CTkFrame(row, height=6, fg_color='transparent').pack()
        ctk.CTkLabel(self, text=parent.tr('review_note'), text_color=MUTED, wraplength=540,
                     justify='left', font=font(parent, 12)).grid(row=3, column=0, sticky='w', padx=26, pady=12)
        buttons = ctk.CTkFrame(self, fg_color='transparent')
        buttons.grid(row=4, column=0, sticky='e', padx=26, pady=(0, 22))
        parent.make_button(buttons, 'cancel', self.destroy).pack(side='left', padx=(0, 10))
        parent.make_button(buttons, 'confirm_run', self.accept, 'play', primary=True).pack(side='left')
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.after(100, self.grab_set)

    def accept(self):
        self.result = True
        self.destroy()


class PackageRow(ctk.CTkFrame):
    def __init__(self, parent, app, package):
        super().__init__(parent, height=104, corner_radius=8, border_width=1,
                         fg_color=SURFACE, border_color=EDGE)
        self.app, self.package = app, package
        self.name = package['name']
        self.grid_columnconfigure(2, weight=1)
        self.grid_propagate(False)
        self.value = tk.BooleanVar(value=self.name in app.checked)
        self.check = ctk.CTkCheckBox(self, text='', width=22, checkbox_width=19, checkbox_height=19,
                                   corner_radius=5, border_width=2, border_color=('#BFC6D0', '#646B79'),
                                   fg_color=BLUE, hover_color='#006FDB', variable=self.value,
                                   command=lambda: app.toggle(self.name))
        self.check.grid(row=0, column=0, rowspan=2, padx=(14, 13), pady=12)
        category = category_for(self.name)
        self.symbol = ctk.CTkLabel(self, image=icon(NAV_ICONS[category], 21), text='',
                                   width=30, fg_color='transparent')
        self.symbol.grid(row=0, column=1, rowspan=2, padx=(0, 10))
        self.copy = ctk.CTkFrame(self, fg_color='transparent')
        self.copy.grid(row=0, column=2, rowspan=2, sticky='nsew', pady=12)
        self.title_label = ctk.CTkLabel(self.copy, text=app.title_for(package), anchor='w',
                                      justify='left', font=font(app, 14, True), text_color=INK,
                                      height=24, wraplength=340)
        self.title_label.pack(fill='x')
        self.description = ctk.CTkLabel(self.copy, text=app.description_for(package), anchor='w',
                                        justify='left', font=font(app, 12), text_color=MUTED,
                                        height=34, wraplength=340)
        self.description.pack(fill='x', pady=(3, 0))
        tk.Misc.bind(self.copy, '<Configure>', self.reflow, add='+')
        meta = app.meta(package)
        self.compatibility = ctk.CTkLabel(self, text='Win ' + meta[4] if meta[4] != 'All' else 'Windows',
                                          font=font(app, 11), text_color=MUTED, width=66)
        self.compatibility.grid(row=0, column=3, sticky='ne', padx=(6, 12), pady=(14, 0))
        risk = meta[5]
        if risk:
            self.risk = ctk.CTkLabel(self, image=icon('shield-alert' if risk == 'security' else 'circle-alert', 16),
                                    text='', width=22)
            self.risk.grid(row=1, column=3, sticky='e', padx=15, pady=(0, 14))
            ToolTip(self.risk, lambda: app.tr(risk))
        self.details = [self, self.symbol, self.copy, self.title_label, self.description, self.compatibility]
        for widget in self.details:
            widget.bind('<Button-1>', lambda _event: app.focus_package(self.name), add='+')
        self.sync()

    def reflow(self, event):
        wrap(self.title_label, event.width, 4)
        wrap(self.description, event.width, 4)
        rendered_font = tkfont.Font(root=self, font=self.description._apply_font_scaling(self.description.cget('font')))
        text = two_lines(self.app.description_for(self.package), rendered_font.measure, max(80, event.width - 8))
        if self.description.cget('text') != text:
            self.description.configure(text=text)

    def sync(self):
        checked = self.name in self.app.checked
        self.value.set(checked)
        self.configure(border_color=BLUE if self.app.current == self.name else EDGE,
                       fg_color=SELECTED if checked else SURFACE)
        self.check.configure(state='disabled' if self.app.busy else 'normal')


class StudioApp(ctk.CTk):
    def __init__(self, data=core.DATA, autoload=True):
        ctk.set_default_color_theme('blue')
        self.data = Path(data)
        self.settings_file = self.data / 'settings.json'
        try:
            self.settings = json.loads(self.settings_file.read_text(encoding='utf-8'))
            if not isinstance(self.settings, dict):
                self.settings = {}
        except (ValueError, OSError):
            self.settings = {}
        self.lang = 'en' if self.settings.get('language') == 'en' else 'vi'
        self.appearance = 'Dark' if self.settings.get('appearance') == 'Dark' else 'Light'
        ctk.set_appearance_mode(self.appearance)
        super().__init__()
        # CTkImage caches PhotoImages, which belong to a single Tcl interpreter.
        icon.cache_clear()
        self.title('OptimizerNXT Studio')
        self.configure(fg_color=BG)
        self.geometry(f'{min(1380, self.winfo_screenwidth()-70)}x{min(880, self.winfo_screenheight()-90)}')
        self.minsize(1100, 680)
        self.repo = core.Repository(self.data)
        self.packages = []
        selected = self.settings.get('selected', [])
        self.checked = {name for name in selected if isinstance(name, str)} if isinstance(selected, list) else set()
        self.current = None
        self.category = 'all_options'
        self.page = 'library'
        self.inspector_mode = 'overview'
        self.preview_serial = 0
        self.preview_content = ''
        self.events = queue.Queue()
        self.busy = False
        self.status_key = 'idle'
        self.rows = {}
        self.logs = deque(maxlen=2000)
        self.last_folder = None
        self.download_count = self.download_total = 0
        self.controls = []
        self.translations = []
        self.query = tk.StringVar()
        self.exe = tk.StringVar(value=self.settings.get('exe', str(self.data / 'bin' / 'optimizerNXT.exe')))
        self.exe.trace_add('write', lambda *_: self.update_cli_status())
        self.build()
        self.translate()
        self.query.trace_add('write', self.query_changed)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.poll_id = self.after(100, self.poll)
        self.add_log('startup')
        if autoload:
            self.after(150, self.refresh)

    def tr(self, key, **values):
        return (EXTRA if key in EXTRA else TEXT)[key][self.lang == 'vi'].format(**values)

    def meta(self, package):
        stem = Path(package['name']).stem
        return PACKAGES.get(stem, (stem.replace('-', ' ').title(), stem.replace('-', ' ').title(),
                                   package['name'], package['name'], '?', 'review'))

    def title_for(self, package):
        return self.meta(package)[self.lang == 'vi']

    def description_for(self, package):
        return self.meta(package)[3 if self.lang == 'vi' else 2]

    def label(self, parent, key, **kwargs):
        kwargs.setdefault('font', font(self))
        kwargs.setdefault('text_color', INK)
        label = ctk.CTkLabel(parent, text=self.tr(key), **kwargs)
        self.translations.append((label, key))
        return label

    def make_button(self, parent, key, command, glyph=None, primary=False, small=False, track=False):
        button = ctk.CTkButton(parent, text=self.tr(key) if key else '', command=command,
                               image=icon(glyph, 17, white=primary) if glyph else None,
                               width=36 if small else 124, height=36 if small else 40,
                               corner_radius=18 if small else 8, border_width=0,
                               fg_color=BLUE if primary else FIELD, text_color='white' if primary else INK,
                               hover_color='#006FE0' if primary else ('#DDE4EF', '#373A45'),
                               font=font(self, 13, primary), border_spacing=10)
        if key:
            self.translations.append((button, key))
        if track:
            self.controls.append(button)
        return button

    def icon_button(self, parent, glyph, command, tooltip, track=False):
        button = self.make_button(parent, None, command, glyph, small=True, track=track)
        ToolTip(button, lambda: self.tr(tooltip))
        return button

    def build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=RAIL)
        self.sidebar.grid(row=0, column=0, sticky='ns')
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(4, weight=1)
        brand = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        brand.grid(row=0, column=0, sticky='ew', padx=20, pady=(28, 30))
        ctk.CTkLabel(brand, text='', image=icon('zap', 23, white=True), width=40, height=40,
                     fg_color=BLUE, corner_radius=12).pack(side='left', padx=(0, 10))
        names = ctk.CTkFrame(brand, fg_color='transparent')
        names.pack(side='left')
        ctk.CTkLabel(names, text='OptimizerNXT', font=font(self, 16, True), text_color=INK,
                     anchor='w').pack(fill='x')
        ctk.CTkLabel(names, text='STUDIO', font=font(self, 10, True), text_color=MUTED,
                     anchor='w', height=14).pack(fill='x')
        self.label(self.sidebar, 'library', text_color=MUTED, font=font(self, 10, True)).grid(row=1, column=0, sticky='w', padx=25, pady=(0, 10))
        nav = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        nav.grid(row=2, column=0, sticky='ew', padx=12)
        self.nav = {}
        for key in CATEGORIES:
            button = ctk.CTkButton(nav, text=self.tr(key), image=icon(NAV_ICONS[key], 18),
                                   command=lambda key=key: self.navigate(key), anchor='w',
                                   height=42, corner_radius=21, fg_color='transparent',
                                   text_color=INK, hover_color=('#E3E7EE', '#2D3038'),
                                   font=font(self, 13), border_spacing=13)
            button.pack(fill='x', pady=2)
            self.nav[key] = button
        self.label(self.sidebar, 'preferences', text_color=MUTED, font=font(self, 10, True)).grid(row=3, column=0, sticky='w', padx=25, pady=(30, 10))
        secondary = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        secondary.grid(row=4, column=0, sticky='new', padx=12)
        for key in ('activity', 'settings'):
            button = ctk.CTkButton(secondary, text=self.tr(key), image=icon(NAV_ICONS[key], 18),
                                   command=lambda key=key: self.navigate(key), anchor='w', height=42,
                                   corner_radius=21, fg_color='transparent', text_color=INK,
                                   hover_color=('#E3E7EE', '#2D3038'), font=font(self), border_spacing=13)
            button.pack(fill='x', pady=2)
            self.nav[key] = button
        bottom = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        bottom.grid(row=5, column=0, sticky='sew', padx=20, pady=22)
        self.cli_badge = ctk.CTkLabel(bottom, text='', anchor='w', font=font(self, 12), text_color=GREEN)
        self.cli_badge.pack(fill='x', pady=(0, 14))
        tools = ctk.CTkFrame(bottom, fg_color='transparent')
        tools.pack(fill='x')
        self.theme_button = self.icon_button(tools, 'moon', self.toggle_appearance, 'appearance')
        self.theme_button.pack(side='left')
        self.language = ctk.CTkOptionMenu(tools, values=['Tiếng Việt', 'English'], command=self.change_language,
                                         width=116, height=34, corner_radius=17, fg_color=FIELD,
                                         button_color=FIELD, text_color=INK, button_hover_color=EDGE,
                                         dropdown_fg_color=SURFACE, dropdown_text_color=INK,
                                         font=font(self, 12), dropdown_font=font(self, 12))
        self.language.set('Tiếng Việt' if self.lang == 'vi' else 'English')
        self.language.pack(side='right')
        self.main = ctk.CTkFrame(self, fg_color='transparent', corner_radius=0)
        self.main.grid(row=0, column=1, sticky='nsew', padx=26, pady=24)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)
        self.header = ctk.CTkFrame(self.main, fg_color='transparent')
        self.header.grid(row=0, column=0, sticky='ew', pady=(0, 22))
        title_group = ctk.CTkFrame(self.header, fg_color='transparent')
        title_group.pack(side='left')
        self.heading = ctk.CTkLabel(title_group, text='', font=font(self, 27, True), text_color=INK, anchor='w')
        self.heading.pack(fill='x')
        self.subtitle = ctk.CTkLabel(title_group, text='', font=font(self, 12), text_color=MUTED, anchor='w')
        self.subtitle.pack(fill='x', pady=(4, 0))
        self.refresh_button = self.icon_button(self.header, 'refresh-cw', self.refresh, 'refresh', track=True)
        self.refresh_button.pack(side='right', pady=8)
        self.body = ctk.CTkFrame(self.main, fg_color='transparent')
        self.body.grid(row=1, column=0, sticky='nsew')
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(0, weight=1)
        self.build_library()
        self.build_activity()
        self.build_settings()
        self.build_footer()
        self.library_page.grid(row=0, column=0, sticky='nsew')

    def build_library(self):
        self.library_page = ctk.CTkFrame(self.body, fg_color='transparent')
        self.library_page.grid_columnconfigure(0, weight=1)
        self.library_page.grid_columnconfigure(2, minsize=300)
        self.library_page.grid_rowconfigure(1, weight=1)
        toolbar = ctk.CTkFrame(self.library_page, fg_color='transparent')
        toolbar.grid(row=0, column=0, sticky='ew', pady=(0, 16))
        search = ctk.CTkFrame(toolbar, fg_color=FIELD, corner_radius=8, height=40)
        search.pack(side='left', fill='x', expand=True, padx=(0, 8))
        ctk.CTkLabel(search, text='', image=icon('search', 17), width=34).pack(side='left', padx=(4, 0))
        self.search = ctk.CTkEntry(search, border_width=0, fg_color=FIELD,
                                  height=40, text_color=INK, font=font(self, 13), corner_radius=8,
                                  placeholder_text=self.tr('search_hint'))
        self.search.pack(side='left', fill='x', expand=True, padx=(0, 8))
        self.search.bind('<KeyRelease>', lambda _event: self.query.set(self.search.get()), add='+')
        self.select_all_button = self.icon_button(toolbar, 'check-check', self.select_visible, 'select_all', track=True)
        self.select_all_button.pack(side='left', padx=(0, 6))
        self.clear_button = self.icon_button(toolbar, 'x', self.clear_selection, 'clear', track=True)
        self.clear_button.pack(side='left')
        self.option_list = ctk.CTkScrollableFrame(self.library_page, fg_color='transparent', corner_radius=0,
                                                scrollbar_button_color=('#C4CBD6', '#4C515D'),
                                                scrollbar_button_hover_color=('#A9B3C2', '#69717F'))
        self.option_list.grid(row=1, column=0, sticky='nsew')
        self.option_list.grid_columnconfigure(0, weight=1)
        self.empty_label = ctk.CTkLabel(self.option_list, text='', text_color=MUTED, font=font(self, 15), height=180)
        ctk.CTkFrame(self.library_page, width=1, height=1, corner_radius=0, fg_color=EDGE).grid(row=0, column=1, rowspan=2, sticky='ns', padx=(20, 20))
        self.inspector = ctk.CTkFrame(self.library_page, fg_color='transparent', width=300)
        self.inspector.grid(row=0, column=2, rowspan=2, sticky='nsew')
        self.inspector.grid_columnconfigure(0, weight=1)
        self.inspector.grid_rowconfigure(2, weight=1)
        self.detail_title = ctk.CTkLabel(self.inspector, text='', text_color=INK, font=font(self, 18, True),
                                        justify='left', anchor='w', wraplength=286, height=60)
        self.detail_title.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        self.detail_tabs = ctk.CTkSegmentedButton(self.inspector, values=['Details', 'YAML'],
                                                command=self.select_inspector, height=34, corner_radius=8,
                                                fg_color=FIELD, selected_color=SURFACE,
                                                selected_hover_color=SURFACE, text_color=INK,
                                                unselected_color=FIELD, unselected_hover_color=EDGE,
                                                font=font(self, 12))
        self.detail_tabs.grid(row=1, column=0, sticky='ew', pady=(0, 18))
        self.detail_tabs.set('Details')
        self.detail_scroll = ctk.CTkScrollableFrame(self.inspector, fg_color='transparent', corner_radius=0, width=280)
        self.detail_scroll.grid(row=2, column=0, sticky='nsew')
        self.detail_scroll.grid_columnconfigure(0, weight=1)
        self.detail_description = ctk.CTkLabel(self.detail_scroll, text='', text_color=MUTED,
                                              font=font(self, 13), justify='left', anchor='nw', wraplength=266)
        self.detail_description.grid(row=0, column=0, sticky='ew', pady=(0, 20))
        self.impact_label = ctk.CTkLabel(self.detail_scroll, text='', text_color=AMBER,
                                        font=font(self, 12), wraplength=266, justify='left', anchor='w')
        self.impact_label.grid(row=1, column=0, sticky='ew', pady=(0, 20))
        self.detail_meta = ctk.CTkFrame(self.detail_scroll, fg_color='transparent')
        self.detail_meta.grid(row=2, column=0, sticky='ew')
        self.meta_values = {}
        for index, key in enumerate(('availability', 'signature', 'revision')):
            label = self.label(self.detail_meta, key, text_color=MUTED, anchor='w')
            label.grid(row=index * 2, column=0, sticky='w', pady=(0, 3))
            value = ctk.CTkLabel(self.detail_meta, text='', text_color=INK, font=font(self, 12), anchor='w')
            value.grid(row=index * 2 + 1, column=0, sticky='w', pady=(0, 20))
            self.meta_values[key] = value
        self.source_button = self.make_button(self.detail_scroll, 'official_source', self.open_source, 'arrow-up-right')
        self.source_button.grid(row=3, column=0, sticky='ew', pady=(8, 18))
        self.yaml_host = ctk.CTkFrame(self.inspector, fg_color='transparent')
        self.yaml_host.grid_columnconfigure(0, weight=1)
        self.yaml_host.grid_rowconfigure(0, weight=1)
        self.yaml = ctk.CTkTextbox(self.yaml_host, wrap='none', font=('Consolas', 11),
                                   fg_color=SURFACE, text_color=INK, corner_radius=8, border_width=1,
                                   border_color=EDGE, width=280, state='disabled')
        self.yaml.grid(row=0, column=0, sticky='nsew')
        self.yaml_x = ctk.CTkScrollbar(self.yaml_host, orientation='horizontal', command=self.yaml._textbox.xview)
        self.yaml_x.grid(row=1, column=0, sticky='ew')
        self.yaml._textbox.configure(xscrollcommand=self.yaml_x.set)
        self.detail_select = self.make_button(self.inspector, 'select_package', self.toggle_current, 'check-check', track=True)
        self.detail_select.grid(row=3, column=0, sticky='ew', pady=(18, 0))
        for label in (self.detail_title, self.detail_description, self.impact_label):
            tk.Misc.bind(label, '<Configure>', lambda event, label=label: wrap(label, event.width, 8), add='+')

    def build_activity(self):
        self.activity_page = ctk.CTkFrame(self.body, fg_color='transparent')
        self.activity_page.grid_rowconfigure(1, weight=1)
        self.activity_page.grid_columnconfigure(0, weight=1)
        actions = ctk.CTkFrame(self.activity_page, fg_color='transparent')
        actions.grid(row=0, column=0, sticky='ew', pady=(0, 18))
        self.folder_button = self.make_button(actions, 'folder', self.open_last_folder, 'folder-open')
        self.folder_button.pack(side='left')
        self.folder_button.configure(state='disabled')
        self.icon_button(actions, 'x', self.clear_logs, 'clear_logs').pack(side='right')
        self.log = ctk.CTkTextbox(self.activity_page, fg_color=SURFACE, text_color=INK,
                                 font=('Consolas', 12), corner_radius=8, border_color=EDGE,
                                 border_width=1, state='disabled', wrap='word')
        self.log.grid(row=1, column=0, sticky='nsew')

    def build_settings(self):
        self.settings_page = ctk.CTkScrollableFrame(self.body, fg_color='transparent', corner_radius=0)
        self.settings_page.grid_columnconfigure(0, weight=1)
        self.label(self.settings_page, 'engine_section', font=font(self, 17, True), anchor='w').grid(row=0, column=0, sticky='ew', pady=(4, 16))
        self.label(self.settings_page, 'exe', text_color=MUTED, anchor='w').grid(row=1, column=0, sticky='ew', pady=(0, 8))
        path_row = ctk.CTkFrame(self.settings_page, fg_color='transparent')
        path_row.grid(row=2, column=0, sticky='ew')
        path_row.grid_columnconfigure(0, weight=1)
        self.exe_entry = ctk.CTkEntry(path_row, textvariable=self.exe, height=40, corner_radius=8,
                                     border_color=EDGE, fg_color=SURFACE, text_color=INK, font=font(self))
        self.exe_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        self.controls.append(self.exe_entry)
        self.icon_button(path_row, 'folder-open', self.browse, 'browse', track=True).grid(row=0, column=1)
        self.make_button(self.settings_page, 'get_cli', self.get_cli, 'download', primary=True, track=True).grid(row=3, column=0, sticky='w', pady=(16, 28))
        line(self.settings_page).grid(row=4, column=0, sticky='ew', pady=(0, 26))
        self.label(self.settings_page, 'personalization', font=font(self, 17, True), anchor='w').grid(row=5, column=0, sticky='ew', pady=(0, 18))
        appearance = ctk.CTkFrame(self.settings_page, fg_color='transparent')
        appearance.grid(row=6, column=0, sticky='ew', pady=(0, 24))
        self.label(appearance, 'appearance').pack(side='left')
        self.appearance_control = ctk.CTkSegmentedButton(appearance, values=['Light', 'Dark'],
            command=self.change_appearance, width=220, height=36, corner_radius=18,
            fg_color=FIELD, selected_color=SELECTED, selected_hover_color=SELECTED,
            unselected_color=FIELD, text_color=INK, font=font(self))
        self.appearance_control.pack(side='right')
        self.appearance_control.set(self.appearance)
        language = ctk.CTkFrame(self.settings_page, fg_color='transparent')
        language.grid(row=7, column=0, sticky='ew', pady=(0, 26))
        self.label(language, 'language').pack(side='left')
        self.settings_language = ctk.CTkOptionMenu(language, values=['Tiếng Việt', 'English'],
            command=self.change_language, width=220, height=36, corner_radius=8,
            fg_color=FIELD, button_color=FIELD, text_color=INK, dropdown_fg_color=SURFACE,
            dropdown_text_color=INK, font=font(self))
        self.settings_language.pack(side='right')
        line(self.settings_page).grid(row=8, column=0, sticky='ew', pady=(0, 26))
        self.label(self.settings_page, 'project_section', font=font(self, 17, True), anchor='w').grid(row=9, column=0, sticky='ew', pady=(0, 18))
        self.label(self.settings_page, 'version', text_color=MUTED, anchor='w').grid(row=10, column=0, sticky='w', pady=(0, 14))
        self.make_button(self.settings_page, 'official_project', lambda: webbrowser.open(core.PROJECT_URL), 'arrow-up-right').grid(row=11, column=0, sticky='w', pady=(0, 14))
        self.make_button(self.settings_page, 'data_folder', lambda: self.open_folder(self.data), 'folder-open').grid(row=12, column=0, sticky='w', pady=(0, 24))

    def build_footer(self):
        self.footer = ctk.CTkFrame(self.main, fg_color='transparent')
        self.footer.grid(row=2, column=0, sticky='ew', pady=(22, 0))
        line(self.footer).pack(fill='x', pady=(0, 16))
        row = ctk.CTkFrame(self.footer, fg_color='transparent')
        row.pack(fill='x')
        self.selection_count = ctk.CTkLabel(row, text='', font=font(self, 14, True), text_color=INK)
        self.selection_count.pack(side='left')
        self.run_button = self.make_button(row, 'run_short', lambda: self.prepare(True), 'play', primary=True, track=True)
        self.run_button.pack(side='right')
        self.download_button = self.make_button(row, 'download_short', lambda: self.prepare(False), 'download', track=True)
        self.download_button.pack(side='right', padx=(0, 10))
        status_row = ctk.CTkFrame(self.footer, fg_color='transparent')
        status_row.pack(fill='x', pady=(12, 0))
        self.status = ctk.CTkLabel(status_row, text='', text_color=MUTED, font=font(self, 11), anchor='w', height=18)
        self.status.pack(side='left', fill='x', expand=True)
        self.progress = ctk.CTkProgressBar(status_row, width=120, height=3, corner_radius=2, progress_color=BLUE,
                                         fg_color=FIELD, mode='indeterminate')
        self.progress.pack(side='right')
        self.progress.set(0)

    def translate(self):
        alive = []
        for widget, key in self.translations:
            if widget.winfo_exists():
                widget.configure(text=self.tr(key))
                alive.append((widget, key))
        self.translations = alive
        self.search.configure(placeholder_text=self.tr('search_hint'))
        values = [self.tr('overview'), 'YAML']
        self.detail_tabs.configure(values=values)
        self.detail_tabs.set(values[self.inspector_mode == 'source'])
        language = 'Tiếng Việt' if self.lang == 'vi' else 'English'
        self.language.set(language)
        self.settings_language.set(language)
        appearance_values = [self.tr('light'), self.tr('dark')]
        self.appearance_control.configure(values=appearance_values)
        self.appearance_control.set(appearance_values[self.appearance == 'Dark'])
        self.theme_button.configure(image=icon('sun' if self.appearance == 'Dark' else 'moon', 18))
        self.update_cli_status()
        self.update_heading()
        self.render()
        self.show_detail()
        self.render_logs()

    def update_heading(self):
        if self.page == 'library':
            self.heading.configure(text=self.tr('catalog_title') if self.category == 'all_options' else self.tr(self.category))
            self.subtitle.configure(text=self.tr('catalog_meta', total=len(self.packages)))
        else:
            self.heading.configure(text=self.tr(self.page))
            self.subtitle.configure(text=self.tr('version') if self.page == 'settings' else self.tr('log_count', count=len(self.logs)))
        for key, button in self.nav.items():
            active = key == (self.category if self.page == 'library' else self.page)
            count = len(self.checked) if key == 'selection' else None
            caption = self.tr(key) + (f'   {count}' if count else '')
            button.configure(text=caption, fg_color=SELECTED if active else 'transparent',
                             text_color=BLUE if active else INK,
                             image=icon(NAV_ICONS[key], 18, accent=active))

    def navigate(self, key):
        for page in (self.library_page, self.activity_page, self.settings_page):
            page.grid_remove()
        if key in CATEGORIES:
            self.category = key
            self.page = 'library'
            self.library_page.grid(row=0, column=0, sticky='nsew')
            self.render(reset_scroll=True)
        else:
            self.page = key
            (self.activity_page if key == 'activity' else self.settings_page).grid(row=0, column=0, sticky='nsew')
        self.update_heading()

    def visible_packages(self):
        query = normalize(self.query.get().strip())
        return [p for p in self.packages
                if (self.category == 'all_options' or
                    self.category == 'selection' and p['name'] in self.checked or
                    self.category == category_for(p['name']))
                and (not query or query in normalize(' '.join((p['name'], *self.meta(p)[:4]))))]

    def query_changed(self, *_args):
        if self.search.get() != self.query.get():
            self.search.delete(0, 'end')
            self.search.insert(0, self.query.get())
        self.render(reset_scroll=True)

    def render(self, reset_scroll=False):
        if not hasattr(self, 'option_list'):
            return
        canvas = self.option_list._parent_canvas
        scroll = 0.0 if reset_scroll else canvas.yview()[0]
        visible = self.visible_packages()
        for row in self.rows.values():
            row.destroy()
        self.rows.clear()
        self.empty_label.grid_remove()
        for index, package in enumerate(visible):
            row = PackageRow(self.option_list, self, package)
            row.grid(row=index, column=0, sticky='ew', pady=(0, 10), padx=(0, 5))
            self.rows[package['name']] = row
        if not visible:
            self.empty_label.configure(text=self.tr('empty_selection' if self.category == 'selection' else 'empty_search'))
            self.empty_label.grid(row=0, column=0, sticky='ew')
        self.option_list.update_idletasks()
        canvas.yview_moveto(scroll)
        self.update_selection()

    def update_selection(self):
        self.selection_count.configure(text=self.tr('ready_count', count=len(self.checked)))
        self.run_button.configure(state='normal' if self.checked and not self.busy else 'disabled')
        self.download_button.configure(state='normal' if self.checked and not self.busy else 'disabled')
        selected = self.current in self.checked
        self.detail_select.configure(text=self.tr('deselect_package' if selected else 'select_package'),
                                     state='normal' if self.current and not self.busy else 'disabled')
        self.status.configure(text=self.tr(self.status_key))
        self.update_heading()

    def focus_package(self, name):
        if self.current == name:
            return
        self.current = name
        self.preview_content = self.tr('preview_loading')
        self.preview_serial += 1
        serial = self.preview_serial
        package = next(p for p in self.packages if p['name'] == name)
        self.show_detail()
        for row in self.rows.values():
            row.sync()

        def work():
            try:
                content = self.repo.blob(package).decode('utf-8-sig')
            except Exception as error:
                content = str(error)
            self.events.put(('preview', (serial, content)))
        threading.Thread(target=work, daemon=True).start()

    def select_inspector(self, value):
        self.inspector_mode = 'source' if value == 'YAML' else 'overview'
        self.show_detail()

    def show_detail(self):
        package = next((p for p in self.packages if p['name'] == self.current), None)
        self.detail_title.configure(text=self.title_for(package) if package else self.tr('nothing_focused'))
        if self.inspector_mode == 'source':
            self.detail_scroll.grid_remove()
            self.yaml_host.grid(row=2, column=0, sticky='nsew')
            self.set_text(self.yaml, self.preview_content)
        else:
            self.yaml_host.grid_remove()
            self.detail_scroll.grid(row=2, column=0, sticky='nsew')
        if package:
            meta = self.meta(package)
            self.detail_description.configure(text=self.description_for(package))
            self.impact_label.configure(text=self.tr('sensitive', impact=self.tr(meta[5])) if meta[5] else '',
                                        text_color=RED if meta[5] in ('security', 'restore') else AMBER)
            self.meta_values['availability'].configure(text='Windows ' + meta[4] if meta[4] != 'All' else self.tr('all_windows'))
            self.meta_values['signature'].configure(text=self.tr('paired'))
            self.meta_values['revision'].configure(text=package['revision'][:12])
            self.detail_meta.grid()
            self.source_button.grid()
        else:
            self.detail_description.configure(text='')
            self.impact_label.configure(text='')
            self.detail_meta.grid_remove()
            self.source_button.grid_remove()
        self.update_selection()

    def toggle(self, name):
        if self.busy:
            return
        self.checked.symmetric_difference_update({name})
        self.focus_package(name)
        if self.category == 'selection':
            self.render()
        else:
            for row in self.rows.values():
                row.sync()
        self.update_selection()
        self.save()

    def toggle_current(self):
        if self.current:
            self.toggle(self.current)

    def select_visible(self):
        if not self.busy:
            self.checked.update(p['name'] for p in self.visible_packages())
            for row in self.rows.values():
                row.sync()
            self.update_selection()
            self.save()

    def clear_selection(self):
        if not self.busy:
            self.checked.clear()
            if self.category == 'selection':
                self.render()
            else:
                for row in self.rows.values():
                    row.sync()
            self.update_selection()
            self.save()

    def change_language(self, language):
        self.lang = 'en' if language == 'English' else 'vi'
        self.translate()
        self.save()

    def toggle_appearance(self):
        self.change_appearance(self.tr('light') if self.appearance == 'Dark' else self.tr('dark'))

    def change_appearance(self, value):
        self.appearance = 'Dark' if value in ('Dark', self.tr('dark')) else 'Light'
        ctk.set_appearance_mode(self.appearance)
        self.appearance_control.set(self.tr('dark') if self.appearance == 'Dark' else self.tr('light'))
        self.theme_button.configure(image=icon('sun' if self.appearance == 'Dark' else 'moon', 18))
        self.save()

    def update_cli_status(self):
        if hasattr(self, 'cli_badge'):
            exists = Path(self.exe.get()).is_file()
            self.cli_badge.configure(text='●  ' + self.tr('cli_ready' if exists else 'cli_missing'),
                                     text_color=GREEN if exists else MUTED)

    def save(self):
        try:
            core.atomic_write(self.settings_file, json.dumps({
                'language': self.lang, 'appearance': self.appearance, 'selected': sorted(self.checked),
                'exe': self.exe.get(),
            }, ensure_ascii=False, indent=2).encode('utf-8'))
        except OSError as error:
            self.add_log(None, raw=str(error))

    def add_log(self, key, raw=None, **values):
        self.logs.append((time.strftime('%H:%M:%S'), key, values, raw))
        self.render_logs()
        self.update_heading()

    def render_logs(self):
        if hasattr(self, 'log'):
            text = '\n\n'.join(f'{stamp}   {raw if raw is not None else self.tr(key, **values)}'
                                 for stamp, key, values, raw in self.logs)
            self.set_text(self.log, text)
            self.log.see('end')

    def clear_logs(self):
        self.logs.clear()
        self.render_logs()
        self.update_heading()

    @staticmethod
    def set_text(widget, text):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        widget.configure(state='disabled')

    def set_busy(self, busy, status='working'):
        self.busy = busy
        self.status_key = status if busy else 'idle'
        for widget in self.controls:
            widget.configure(state='disabled' if busy else 'normal')
        for row in self.rows.values():
            row.sync()
        if busy:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)
        self.update_selection()

    def start_worker(self, task, status='working'):
        if self.busy:
            return
        self.set_busy(True, status)

        def work():
            try:
                task()
            except Exception as error:
                self.events.put(('error', str(error)))
            finally:
                self.events.put(('finished', None))
        threading.Thread(target=work, daemon=True).start()

    def refresh(self):
        def task():
            self.events.put(('catalog', self.repo.catalog()))
        self.start_worker(task, 'loading')

    def browse(self):
        path = filedialog.askopenfilename(parent=self, title=self.tr('cli_pick_title'),
                                          filetypes=[('OptimizerNXT', '*.exe')])
        if path:
            self.exe.set(path)
            self.save()

    def get_cli(self):
        def task():
            self.events.put(('exe', str(self.repo.download_cli())))
        self.start_worker(task)

    def confirm_run(self, packages):
        dialog = ReviewDialog(self, packages)
        self.wait_window(dialog)
        return dialog.result

    def prepare(self, apply):
        if self.busy:
            return
        selected = [p.copy() for p in self.packages if p['name'] in self.checked]
        if not selected:
            return
        executable = Path(self.exe.get()).expanduser()
        acquire_cli = False
        if apply:
            if os.name != 'nt':
                messagebox.showerror(self.tr('error'), self.tr('not_windows'), parent=self)
                return
            if not self.confirm_run(selected):
                return
            if not executable.is_file():
                if not messagebox.askyesno('OptimizerNXT CLI', self.tr('cli_needed'), parent=self):
                    return
                acquire_cli = True
        self.save()
        self.download_count = 0
        self.download_total = len(selected)
        self.navigate('activity')

        def task():
            actual_exe = self.repo.download_cli() if acquire_cli else executable
            if acquire_cli:
                self.events.put(('exe', str(actual_exe)))
            folder = self.repo.download_packages(selected, lambda name: self.events.put(('downloaded', name)))
            self.events.put(('folder', (folder, len(selected))))
            if apply:
                code = core.run_cli(actual_exe, folder, lambda: self.events.put(('started', None)))
                self.events.put(('ended', code))
        self.start_worker(task, 'downloading')

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'finished':
                    self.set_busy(False)
                elif kind == 'catalog':
                    self.packages, warning = value
                    self.checked.intersection_update(p['name'] for p in self.packages)
                    previous = self.current
                    self.current = None
                    self.preview_serial += 1
                    self.preview_content = ''
                    self.render()
                    self.show_detail()
                    if previous and any(p['name'] == previous for p in self.packages):
                        self.focus_package(previous)
                    elif self.packages:
                        self.focus_package(self.packages[0]['name'])
                    self.add_log('catalog_loaded', count=len(self.packages))
                    if warning:
                        self.add_log('cached', error=warning)
                elif kind == 'preview':
                    serial, content = value
                    if serial == self.preview_serial:
                        self.preview_content = content
                        if self.inspector_mode == 'source':
                            self.set_text(self.yaml, content)
                elif kind == 'exe':
                    self.exe.set(value)
                    self.save()
                    self.add_log('cli_done')
                elif kind == 'downloaded':
                    self.download_count += 1
                    self.add_log('downloaded', name=value)
                    self.status.configure(text=self.tr('progress_download', done=self.download_count, total=self.download_total))
                elif kind == 'folder':
                    self.last_folder, count = value
                    self.folder_button.configure(state='normal')
                    self.add_log('download_success', count=count)
                    self.add_log(None, raw=str(self.last_folder))
                elif kind == 'started':
                    self.status_key = 'running'
                    self.status.configure(text=self.tr('running'))
                    self.add_log('cli_start')
                elif kind == 'ended':
                    self.add_log('cli_finished', code=value)
                    self.add_log('cli_output')
                elif kind == 'error':
                    self.add_log(None, raw=value)
                    messagebox.showerror(self.tr('error'), value, parent=self)
        except queue.Empty:
            pass
        self.poll_id = self.after(100, self.poll)

    def open_source(self):
        package = next((p for p in self.packages if p['name'] == self.current), None)
        if package:
            webbrowser.open(f"{core.PROJECT_URL}/blob/{package['revision']}/{package['path']}")

    @staticmethod
    def open_folder(folder):
        folder.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            os.startfile(folder)
        else:
            webbrowser.open(folder.as_uri())

    def open_last_folder(self):
        if self.last_folder:
            self.open_folder(self.last_folder)

    def close(self):
        if self.busy and not messagebox.askyesno(self.tr('working'), self.tr('busy_close'), parent=self):
            return
        self.save()
        self.after_cancel(self.poll_id)
        self.destroy()
