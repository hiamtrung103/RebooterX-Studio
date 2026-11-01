"""Paced scrolling with explicit completion of Windows child-window painting."""
import ctypes
from ctypes import wintypes
import math
import sys
import time
import tkinter as tk

import customtkinter as ctk


class AnimationTimer:
    def __init__(self):
        self.active = False

    def schedule(self, widget, delay, callback):
        if sys.platform == 'win32' and not self.active:
            try:
                self.active = ctypes.windll.winmm.timeBeginPeriod(1) == 0
            except (OSError, AttributeError):
                pass
        return widget.after(delay, callback)

    def stop(self):
        if self.active:
            ctypes.windll.winmm.timeEndPeriod(1)
            self.active = False


def invalidate(widget):
    if sys.platform != 'win32' or not widget.winfo_exists() or not widget.winfo_ismapped():
        return
    redraw = ctypes.windll.user32.RedrawWindow
    redraw.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.HANDLE, wintypes.UINT]
    redraw.restype = wintypes.BOOL
    redraw(widget.winfo_id(), None, None, 0x0001 | 0x0004 | 0x0080 | 0x0100)


class DeferredScrollbar(ctk.CTkScrollbar):
    def __init__(self, *args, **kwargs):
        self._draw_job = None
        self._draw_colors = False
        self._destroying = False
        super().__init__(*args, **kwargs)

    def _draw(self, no_color_updates=False):
        if self._destroying:
            return
        self._draw_colors |= not no_color_updates
        if self._draw_job is None:
            self._draw_job = self.after(1, self.flush_draw)

    def flush_draw(self):
        self._draw_job = None
        colors, self._draw_colors = self._draw_colors, False
        super()._draw(no_color_updates=not colors)

    def destroy(self):
        self._destroying = True
        if self._draw_job is not None:
            self.after_cancel(self._draw_job)
            self._draw_job = None
        super().destroy()


class SmoothScrollFrame(ctk.CTkScrollableFrame):
    """Coalesce wheel/drag bursts, then finish WM_PAINT and queued Tk Expose."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        original = self._scrollbar
        geometry = dict(original._last_geometry_manager_call['kwargs'])
        self._scrollbar = DeferredScrollbar(self._parent_frame,
            orientation=original.cget('orientation'), width=original.cget('width'),
            height=original.cget('height'), fg_color=original.cget('fg_color'),
            button_color=original.cget('scrollbar_color'),
            button_hover_color=original.cget('scrollbar_hover_color'))
        original.destroy()
        self._scrollbar.grid(**geometry)
        self._scrollbar_geometry = geometry
        self._scroll_pending = 0
        self._scroll_target = None
        self._scroll_job = self._paint_job = self._layout_job = self._thumb_job = None
        self._wheel_remainder = 0.
        self._last_scroll_at = 0.
        self._last_view = self._last_thumb_view = None
        self._can_scroll = False
        self._timer = AnimationTimer()
        self._parent_canvas.configure(yscrollcommand=self.viewport_changed)
        self._scrollbar.configure(command=self.scrollbar_command)
        tk.Frame.bind(self, '<Configure>', self.schedule_geometry)
        tk.Frame.bind(self, '<Map>', self.schedule_geometry, add='+')
        self._parent_canvas.bind('<Configure>', self.schedule_geometry, add='+')

    def schedule_geometry(self, _event=None):
        if self._layout_job is None:
            self._layout_job = self.after_idle(self.refresh_geometry)

    def refresh_geometry(self):
        self._layout_job = None
        canvas = self._parent_canvas
        viewport = canvas.winfo_height()
        if viewport < 16 or not self.winfo_ismapped():
            return
        content = self.winfo_reqheight()
        self._can_scroll = content > viewport + 1
        if self._can_scroll:
            if not self._scrollbar.winfo_manager():
                self._scrollbar.grid(**self._scrollbar_geometry)
        else:
            if self._scrollbar.winfo_manager():
                self._scrollbar.grid_forget()
            self._scroll_pending, self._scroll_target = 0, None
        region = (0, 0, canvas.winfo_width(), max(content, viewport))
        if tuple(map(float, str(canvas.cget('scrollregion')).split())) != region:
            canvas.configure(scrollregion=region)
        if not self._can_scroll or canvas.canvasy(0) < 0:
            canvas.yview_moveto(0)

    def viewport_changed(self, first, last):
        view = (first, last)
        changed = view != self._last_view
        self._last_view = view
        if self._scroll_target is None and view != self._last_thumb_view and self._thumb_job is None:
            self._thumb_job = self.after(1, self.refresh_thumb)
        if changed and self._paint_job is None:
            self._paint_job = self._timer.schedule(self, 1, self.repaint_viewport)

    def refresh_thumb(self):
        self._thumb_job = None
        if self._scroll_target is None and self._last_view != self._last_thumb_view:
            self._last_thumb_view = self._last_view
            self._scrollbar.set(*self._last_view)

    def _mouse_wheel_all(self, event):
        target = event.widget
        try:
            target = self.winfo_toplevel().winfo_containing(event.x_root, event.y_root) or target
        except (tk.TclError, AttributeError):
            pass
        if not self.check_if_master_is_canvas(target) or not self._can_scroll:
            return
        if self._shift_pressed:
            return super()._mouse_wheel_all(event)
        self._scroll_target = None
        amount = self._wheel_remainder + (-event.delta / 6 if sys.platform == 'win32' else -event.delta)
        whole = math.trunc(round(amount, 8))
        self._wheel_remainder = amount - whole
        if whole:
            self._scroll_pending += whole
            self.schedule_scroll()

    def scrollbar_command(self, operation, value, units=None):
        if not self._can_scroll:
            return
        if operation == 'moveto':
            self._scroll_target, self._scroll_pending = float(value), 0
            self._last_thumb_view = None
        elif operation == 'scroll':
            if units != 'units':
                self._parent_canvas.yview(operation, value, units)
                return
            self._scroll_target = None
            self._scroll_pending += int(value)
        self.schedule_scroll()

    def schedule_scroll(self):
        if self._scroll_job is None and self._paint_job is None:
            elapsed = (time.perf_counter() - self._last_scroll_at) * 1000
            self._scroll_job = self._timer.schedule(self, max(1, math.ceil(17 - elapsed)), self.flush_scroll)

    def flush_scroll(self):
        self._scroll_job = None
        if not self.winfo_ismapped() or not self._can_scroll:
            self._scroll_pending, self._scroll_target = 0, None
            self._timer.stop()
            return
        if self._paint_job is not None:
            return
        target, self._scroll_target = self._scroll_target, None
        amount, self._scroll_pending = self._scroll_pending, 0
        self._last_scroll_at = time.perf_counter()
        before = self._parent_canvas.yview()
        if target is not None:
            self._parent_canvas.yview_moveto(target)
        elif amount:
            limit = max(40, self._parent_canvas.winfo_height() // 2)
            self._parent_canvas.yview_scroll(max(-limit, min(limit, amount)), 'units')
        if self._parent_canvas.yview() == before and self._paint_job is None:
            self._timer.stop()

    def repaint_viewport(self):
        self._parent_canvas.update_idletasks()
        if self._paint_job is not None:
            self.after_cancel(self._paint_job)
        self._paint_job = None
        if not self.winfo_exists() or not self.winfo_ismapped():
            self._timer.stop()
            return
        invalidate(self._parent_canvas)
        self._paint_job = self.after_idle(self.finish_repaint)

    def finish_repaint(self):
        self._parent_canvas.update_idletasks()
        self._paint_job = None
        if self._scroll_target is not None or self._scroll_pending:
            self.schedule_scroll()
        elif self._scroll_job is None:
            self._timer.stop()

    def destroy(self):
        for job in (self._scroll_job, self._paint_job, self._layout_job, self._thumb_job):
            if job is not None:
                self.after_cancel(job)
        self._timer.stop()
        self._scrollbar.destroy()
        super().destroy()
