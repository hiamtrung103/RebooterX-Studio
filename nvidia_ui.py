"""Bilingual profile editor; all driver calls stay off Tk's event loop."""
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

import nvidia
from painting import SmoothScrollFrame, DeferredOptionMenu
from theme import BG, SURFACE, FIELD, INK, MUTED, BLUE, EDGE, GREEN, font, wrap


class NvidiaPage(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app.body, fg_color='transparent', corner_radius=0)
        self.app = app
        self.vi = app.lang == 'vi'
        self.service = nvidia.Profiles(app.data / 'nvidia-backups')
        self.plan = None
        self.busy = False
        self.events = queue.Queue()
        self.controls = []
        self.built = False

    def ensure_built(self):
        if self.built:
            return
        self.built = True
        app = self.app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.grid(row=0, column=0, sticky='ew', pady=(0, 14))
        self.label(header, 'NVIDIA', size=12, color=BLUE).pack(anchor='w')
        self.label(header, self.t('Tune your game profile', 'Tinh chỉnh cấu hình game'), size=24, bold=True).pack(anchor='w')
        self.label(header, self.t('Read → review → apply. Backups stay on this PC.',
                   'Đọc → xem lại → áp dụng. Bản sao lưu được giữ trên máy.'), color=MUTED).pack(anchor='w', pady=(4, 0))
        launchers = ctk.CTkFrame(header, fg_color='transparent')
        launchers.pack(fill='x', pady=(10, 0))
        self.button(launchers, 'NVIDIA Control Panel ↗', lambda: app.open_nvidia('panel')).pack(side='left', padx=(0, 8))
        self.button(launchers, 'NVIDIA App ↗', lambda: app.open_nvidia('app')).pack(side='left')
        scroll = self.scroll = SmoothScrollFrame(self, fg_color='transparent', corner_radius=0)
        scroll.grid(row=1, column=0, sticky='nsew')
        scroll.grid_columnconfigure(0, weight=1)
        target = self.card(scroll, 0)
        self.label(target, self.t('01  ·  Target', '01  ·  Phạm vi'), bold=True).pack(anchor='w', padx=16, pady=(14, 8))
        self.scope = DeferredOptionMenu(target, values=[self.t('Selected game', 'Game được chọn'),
                   self.t('Global · all applications', 'Toàn cục · mọi ứng dụng')],
                   command=lambda _: self.changed(), height=36, fg_color=FIELD, button_color=FIELD,
                   text_color=INK, font=font(self, 14))
        self.scope.pack(fill='x', padx=16, pady=(0, 10))
        self.controls.append(self.scope)
        path_row = ctk.CTkFrame(target, fg_color='transparent')
        path_row.pack(fill='x', padx=16, pady=(0, 10))
        self.path = tk.StringVar()
        self.path_entry = ctk.CTkEntry(path_row, textvariable=self.path,
            placeholder_text=self.t('Select the game executable', 'Chọn file .exe của game'),
            fg_color=FIELD, border_width=0, height=36, font=font(self))
        self.path_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        self.controls.append(self.path_entry)
        self.button(path_row, self.t('Browse…', 'Chọn file…'), self.browse).pack(side='right')
        self.path.trace_add('write', lambda *_: self.changed())
        self.label(target, self.t('NVIDIA matches executable names. Existing profiles can be shared by several games; read the preview first.',
                   'NVIDIA nhận diện theo tên file chạy. Profile có thể dùng chung cho nhiều game; hãy đọc phần xem trước.'),
                   color=MUTED).pack(fill='x', padx=16, pady=(0, 14))
        settings = self.card(scroll, 1)
        heading = ctk.CTkFrame(settings, fg_color='transparent')
        heading.pack(fill='x', padx=16, pady=(14, 12))
        self.label(heading, self.t('02  ·  Driver settings', '02  ·  Thiết lập driver'), bold=True).pack(side='left')
        self.button(heading, self.t('Performance preset', 'Điền preset hiệu năng'), self.preset).pack(side='right')
        self.values, self.checks = {}, {}
        notes = {
            nvidia.POWER: self.t('Higher power use and heat while the game runs.', 'Có thể tăng điện năng và nhiệt độ khi chạy game.'),
            nvidia.CACHE: self.t('Global setting, including in game mode. Unlimited uses disk space; it is not VRAM.',
                                 'Luôn áp dụng toàn cục, kể cả khi chọn game. Unlimited dùng ổ đĩa, không phải VRAM.'),
            nvidia.QUALITY: self.t('High performance can reduce texture quality / increase shimmering.',
                                   'High performance có thể giảm chất lượng texture / tăng nhấp nháy bề mặt.'),
            nvidia.VSYNC: self.t('Off can remove the refresh-rate cap, with possible screen tearing. Review separately for G-SYNC.',
                                 'Off có thể bỏ giới hạn theo Hz màn hình, đổi lại có thể xé hình. Cân nhắc riêng nếu dùng G-SYNC.'),
            nvidia.FPS_LIMIT: self.t('Off removes this driver cap; game/other limits remain. A cap can improve frame pacing or reduce heat.',
                                     'Off bỏ giới hạn FPS của driver; giới hạn trong game vẫn còn. Có thể giới hạn để đều khung hình hoặc giảm nhiệt.'),
            nvidia.ANISO_SAMPLE: self.t('DirectX texture-sampling optimization; may trade image quality for performance.',
                                        'Tối ưu lấy mẫu texture cho DirectX; có thể giảm chất lượng để ưu tiên hiệu năng.'),
            nvidia.TRILINEAR: self.t('DirectX filtering optimization. High quality texture mode can ignore this setting.',
                                     'Tối ưu lọc texture cho DirectX. Chế độ texture High quality có thể bỏ qua mục này.'),
            nvidia.THREADED: self.t('OpenGL only. Auto lets the driver decide; forcing On can regress some games.',
                                    'Chỉ OpenGL. Auto để driver quyết định; ép On có thể làm một số game chậm hơn.'),
            nvidia.FXAA: self.t('Off removes driver FXAA if active; edges may look more jagged. In-game antialiasing is separate.',
                                'Off tắt FXAA của driver nếu đang bật; cạnh có thể răng cưa hơn. Khử răng cưa trong game là mục riêng.'),
            nvidia.REFRESH: self.t('Requests the highest supported refresh rate. This does not increase rendered FPS and may be unavailable with VRR.',
                                   'Ưu tiên Hz cao nhất được hỗ trợ. Không tự tăng FPS dựng hình; có thể không áp dụng khi dùng VRR.'),
        }
        for identifier, options in nvidia.OPTIONS.items():
            row = ctk.CTkFrame(settings, fg_color='transparent')
            row.pack(fill='x', padx=16, pady=(0, 12))
            checked = tk.BooleanVar(value=False)
            check = ctk.CTkCheckBox(row, text=nvidia.NAMES[identifier], variable=checked,
                                  command=self.changed, font=font(self, 14, True), text_color=INK,
                                  checkbox_width=18, checkbox_height=18, fg_color=BLUE)
            check.pack(anchor='w', pady=(0, 7))
            menu = DeferredOptionMenu(row, values=list(options), command=lambda _: self.changed(),
                fg_color=FIELD, button_color=FIELD, text_color=INK, height=34, font=font(self))
            menu.pack(fill='x', padx=(28, 0))
            self.label(row, notes[identifier], color=MUTED, size=12).pack(fill='x', padx=(28, 0), pady=(4, 0))
            self.values[identifier], self.checks[identifier] = menu, checked
            self.controls.extend((check, menu))
        preview = self.card(scroll, 2)
        self.label(preview, self.t('03  ·  Preview & backup', '03  ·  Xem trước & sao lưu'), bold=True).pack(anchor='w', padx=16, pady=(14, 8))
        self.preview = ctk.CTkTextbox(preview, height=170, fg_color=FIELD, text_color=INK,
                                    font=font(self, 13), wrap='word', state='disabled')
        self.preview.pack(fill='x', padx=16, pady=(0, 14))
        self.show(self.t('Nothing has been changed. Select settings or fill the performance preset, then read the current profile.',
                         'Chưa thay đổi thiết lập. Tích các mục cần dùng hoặc điền preset hiệu năng, rồi đọc profile hiện tại.'))
        display = self.card(scroll, 3)
        self.label(display, self.t('Display · Full-screen scaling', 'Màn hình · Full-screen scaling'), bold=True).pack(anchor='w', padx=16, pady=(14, 8))
        self.label(display, self.t(
            'Set manually in NVIDIA Control Panel → Adjust desktop size and position:\n'
            '1. Select the monitor.\n2. Scaling mode: Full-screen.\n3. Perform scaling on: GPU.\n'
            '4. Enable “Override the scaling mode set by games and programs” if desired, then Apply.\n\n'
            'This stretches non-matching aspect ratios. The game’s Fullscreen mode is set inside the game. '
            'This editor does not apply display scaling or the old image-preview slider; use advanced 3D settings for profiles.',
            'Đặt thủ công trong NVIDIA Control Panel → Adjust desktop size and position:\n'
            '1. Chọn màn hình.\n2. Scaling mode: Full-screen.\n3. Perform scaling on: GPU.\n'
            '4. Tích “Override the scaling mode set by games and programs” nếu muốn ép chế độ, rồi Apply.\n\n'
            'Ảnh có thể bị kéo giãn khi khác tỉ lệ. Chế độ Fullscreen của game chỉnh trong game. '
            'Trình này chưa tự ghi scaling màn hình hay thanh trượt preview cũ; dùng advanced 3D settings cho profile.'),
            color=MUTED).pack(fill='x', padx=16, pady=(0, 12))
        self.button(display, 'NVIDIA Control Panel ↗', lambda: app.open_nvidia('panel')).pack(anchor='w', padx=16, pady=(0, 14))
        latency = self.card(scroll, 4)
        self.label(latency, self.t('More performance & latency options', 'Thêm lựa chọn hiệu năng & độ trễ'), bold=True).pack(anchor='w', padx=16, pady=(14, 8))
        self.label(latency, self.t(
            'Low Latency Mode: set in Control Panel for games without Reflex. This targets input latency; Ultra is not a universal FPS boost. '
            'If the game has NVIDIA Reflex, enable it in-game; Reflex overrides the driver low-latency mode.\n\n'
            'Image Scaling (NIS): enable in Control Panel, then use a lower in-game resolution. This can raise FPS with reduced detail. '
            'Prefer the game’s DLSS Super Resolution option when supported. These options require game/display-specific setup and are not written by this preset.\n\n'
            'The performance preset fills the ten settings above. Nothing is applied until you read, review and confirm. FPS gains depend on the game and hardware.',
            'Low Latency Mode: chỉnh trong Control Panel cho game không có Reflex. Mục này giảm độ trễ đầu vào; Ultra không luôn tăng FPS. '
            'Nếu game có NVIDIA Reflex, bật trong game; Reflex ưu tiên hơn chế độ giảm độ trễ của driver.\n\n'
            'Image Scaling (NIS): bật trong Control Panel rồi chọn độ phân giải thấp hơn trong game. Có thể tăng FPS nhưng giảm độ chi tiết. '
            'Ưu tiên DLSS Super Resolution trong game nếu được hỗ trợ. Các mục này cần cấu hình theo game/màn hình và không được preset tự ghi.\n\n'
            'Preset hiệu năng điền mười mục phía trên. Chỉ áp dụng sau khi đọc, xem trước và xác nhận. Mức tăng FPS phụ thuộc game và phần cứng.'), color=MUTED).pack(fill='x', padx=16, pady=(0, 16))
        footer = ctk.CTkFrame(self, fg_color=BG)
        footer.grid(row=2, column=0, sticky='ew', pady=(14, 0))
        self.read_button = self.button(footer, self.t('Read / preview', 'Đọc / xem trước'), self.read)
        self.read_button.pack(side='left', padx=(0, 8))
        self.apply_button = self.button(footer, self.t('Apply', 'Áp dụng'), self.apply, primary=True)
        self.apply_button.pack(side='left', padx=(0, 8))
        self.apply_button.configure(state='disabled')
        self.button(footer, self.t('Restore last change', 'Khôi phục lần gần nhất'), self.restore).pack(side='right')
        self.poll_job = self.after(80, self.poll)

    def refresh_language_if_needed(self):
        if not self.busy and self.vi != (self.app.lang == 'vi'):
            self.translate()

    def t(self, en, vi):
        return vi if self.vi else en

    def label(self, parent, text, size=14, bold=False, color=INK):
        label = ctk.CTkLabel(parent, text=text, font=font(self, size, bold), text_color=color,
                             anchor='w', justify='left', wraplength=690)
        # Only stretch-filled paragraphs need reflow. Rewrapping a naturally
        # sized heading to its own width repeatedly shrinks it to one word.
        def reflow(event):
            width = label.winfo_width()
            if label.winfo_ismapped() and width > 200 and label.winfo_manager() == 'pack' and label.pack_info().get('fill') in ('x', 'both'):
                wrap(label, width, 2)
        tk.Misc.bind(label, '<Configure>', reflow, add='+')
        tk.Misc.bind(label, '<Map>', reflow, add='+')
        return label

    def card(self, parent, row):
        card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=EDGE)
        card.grid(row=row, column=0, sticky='ew', pady=(0, 14), padx=(0, 4))
        return card

    def button(self, parent, text, command, primary=False):
        button = ctk.CTkButton(parent, text=text, command=command, font=font(self, 13, primary),
            fg_color=BLUE if primary else FIELD, text_color='white' if primary else INK,
            hover_color='#006FE0' if primary else EDGE, height=36, corner_radius=8)
        self.controls.append(button)
        return button

    def browse(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[('Game executable', '*.exe')])
        if path:
            self.path.set(path)

    def changed(self):
        self.plan = None
        if hasattr(self, 'apply_button'):
            self.apply_button.configure(state='disabled')
            self.show(self.t('Selection changed. Read the profile again to refresh the preview.',
                             'Lựa chọn đã đổi. Đọc lại profile để cập nhật phần xem trước.'))

    def preset(self):
        for identifier, menu in self.values.items():
            menu.set(next(iter(nvidia.OPTIONS[identifier])))
            self.checks[identifier].set(True)
        self.changed()

    def show(self, text):
        self.preview.configure(state='normal')
        self.preview.delete('1.0', 'end')
        self.preview.insert('1.0', text)
        self.preview.configure(state='disabled')

    def run(self, kind, operation):
        if self.busy:
            return
        self.busy = True
        for control in self.controls:
            control.configure(state='disabled')
        self.show(self.t('Working…', 'Đang xử lý…'))
        def task():
            try:
                self.events.put((kind, operation()))
            except Exception as error:
                self.events.put(('error', str(error)))
        threading.Thread(target=task, daemon=True).start()

    def read(self):
        path = self.path.get() if self.scope.get() == self.t('Selected game', 'Game được chọn') else ''
        if not path and self.scope.get() == self.t('Selected game', 'Game được chọn'):
            messagebox.showinfo('NVIDIA', self.t('Select the game .exe first.', 'Hãy chọn file .exe của game trước.'), parent=self)
            return
        choices = {i: nvidia.OPTIONS[i][menu.get()] for i, menu in self.values.items() if self.checks[i].get()}
        self.plan = None
        self.run('plan', lambda: self.service.plan(path, choices))

    def apply(self):
        if self.busy or not self.plan:
            return
        if messagebox.askyesno('NVIDIA', self.t('Apply the previewed changes? Close the game first. A backup will be saved before writing.',
                              'Áp dụng các thay đổi đã xem trước? Hãy đóng game trước. Tool lưu bản sao trước khi ghi.'), parent=self):
            plan, self.plan = self.plan, None
            self.run('applied', lambda: self.service.apply(plan))

    def restore(self):
        if self.busy:
            return
        try:
            path, receipt = self.service.latest()
        except Exception as error:
            self.show(str(error))
            return
        summary = '\n'.join(f"{c['profile']} · {nvidia.NAMES[c['id']]}" for c in receipt['changes'])
        if messagebox.askyesno('NVIDIA', self.t('Restore this backup? Newer driver changes will block restore.',
                              'Khôi phục bản sao này? Nếu driver có thay đổi mới, tool sẽ chặn khôi phục.') + '\n\n' + summary, parent=self):
            self.plan = None
            self.run('restored', lambda: self.service.restore(path))

    def poll(self):
        try:
            kind, value = self.events.get_nowait()
        except queue.Empty:
            self.poll_job = self.after(80, self.poll)
            return
        self.busy = False
        for control in self.controls:
            control.configure(state='normal')
        self.apply_button.configure(state='disabled')
        if kind == 'plan':
            self.plan = value
            info = value['profile']
            text = self.t('Profile', 'Profile') + ': ' + info['name']
            text += self.t(f"\nApplications sharing this profile: {info['apps']}", f"\nSố ứng dụng dùng chung profile: {info['apps']}")
            if value['executable'] is None:
                text += self.t('\nGLOBAL: affects all applications.', '\nTOÀN CỤC: ảnh hưởng mọi ứng dụng.')
            for change in value['changes']:
                text += '\n\n' + nvidia.NAMES[change['id']]
                text += '\n' + nvidia.describe(change['id'], change['before']) + ' → ' + nvidia.describe(change['id'], change['after'])
            self.show(text)
            self.apply_button.configure(state='normal')
        elif kind == 'error':
            self.plan = None
            self.show(self.t('Could not complete the operation.\n', 'Không hoàn tất được thao tác.\n') + value)
        else:
            self.show(self.t('Driver values verified. Backup: ', 'Đã đọc lại và xác minh driver. Bản sao: ') + str(value))
            self.app.add_log(None, raw=f'NVIDIA · {kind} · {value}')
        self.poll_job = self.after(80, self.poll)
        self.refresh_language_if_needed()

    def close(self):
        if self.busy:
            return
        self.app.navigate('windows_nav')

    def destroy(self):
        if self.built:
            self.after_cancel(self.poll_job)
        super().destroy()

    def translate(self):
        """Rebuild static copy on language changes, preserving selections."""
        if not self.built:
            self.vi = self.app.lang == 'vi'
            return
        # In-flight jobs keep their original language until finished.
        if self.busy or self.vi == (self.app.lang == 'vi'):
            return
        path = self.path.get()
        global_scope = self.scope.get() == self.t('Global · all applications', 'Toàn cục · mọi ứng dụng')
        values = {i: (self.values[i].get(), self.checks[i].get()) for i in self.values}
        parent = self.app
        active = parent.page == 'nvidia'
        self.destroy()
        parent.nvidia_page = replacement = NvidiaPage(parent)
        replacement.ensure_built()
        replacement.path.set(path)
        if global_scope:
            replacement.scope.set(replacement.t('Global · all applications', 'Toàn cục · mọi ứng dụng'))
        for i, (value, checked) in values.items():
            replacement.values[i].set(value)
            replacement.checks[i].set(checked)
        if active:
            replacement.grid(row=0, column=0, sticky='nsew')
