import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Frame, Label
from live import create_live_tab
from history import create_history_tab


app = ttk.Window(themename="cosmo")
app.title("czołg")
app.geometry("800x600")
app.resizable(False, False)


notebook = ttk.Notebook(app, bootstyle="info")
notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)


create_live_tab(notebook)

create_history_tab(notebook)

# Uruchomienie aplikacji
app.mainloop()
