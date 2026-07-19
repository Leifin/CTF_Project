import tkinter as tk
import os
import sys
from gui.app import GridGameApp

if __name__ == "__main__":
    root = tk.Tk()

    # Set window icon for taskbar and title bar
    if getattr(sys, 'frozen', False):
        # Running as compiled exe — icon is embedded by PyInstaller
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(base_path, "assets", "grid_explorer_icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    app = GridGameApp(root)
    root.mainloop()