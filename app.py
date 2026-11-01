"""Launch OptimizerNXT Studio."""
import sys
import tkinter as tk
from tkinter import messagebox


def main():
    try:
        from ui import StudioApp
    except ImportError as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('OptimizerNXT Studio',
            'Run Setup.cmd to install dependencies, then open Start.cmd.\n'
            'Chạy Setup.cmd để cài thư viện, sau đó mở Start.cmd.\n\n' + str(error))
        root.destroy()
        return 1
    StudioApp().mainloop()
    return 0


if __name__ == '__main__':
    sys.exit(main())
