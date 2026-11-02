"""Launch RebooterX Studio."""
import sys
import tkinter as tk
from tkinter import messagebox


def main():
    from bootstrap import ensure_admin
    launch_status = ensure_admin()
    if launch_status is not None:
        return launch_status
    if '--runner' in sys.argv:
        from bootstrap import dispatch_runner
        return dispatch_runner()
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        from bootstrap import self_test
        return self_test(sys.argv[2])
    try:
        from ui import StudioApp
    except ImportError as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('RebooterX Studio',
            'Run Setup.cmd to install dependencies, then open Start.cmd.\n'
            'Chạy Setup.cmd để cài thư viện, sau đó mở Start.cmd.\n\n' + str(error))
        root.destroy()
        return 1
    StudioApp().mainloop()
    return 0


if __name__ == '__main__':
    sys.exit(main())
