import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Frame, Canvas, messagebox, Entry, Button
from pymongo import MongoClient
import numpy as np
from scipy import interpolate
import threading  # Importowanie modułu do pracy z wątkami


stop1 = False

def search_database(name):
    print(f"Searching for name: {name}")

    # URI do MongoDB
    uri = "mongodb+srv://jakub44295:<>@cluster0.x148r.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri)

    # Połączenie z odpowiednią bazą danych i kolekcją
    db = client['tank_data']  # Zamień na nazwę swojej bazy danych
    collection = db['tank_data']  # Zamień na nazwę swojej kolekcji

    # Znajdź najnowszy dokument, gdzie 'name' równa się wprowadzonej wartości
    result = collection.find({"name": name}).sort("timestamp", -1).limit(1)

    # Jeśli znaleziono dokument, zwróć go i wyświetl dane w konsoli
    for doc in result:
        print("Found document:")
        print(doc)  # Cały dokument
        print(f"Name: {doc.get('name')}")
        print(f"Timestamp: {doc.get('timestamp')}")
        return doc

    print("No document found.")
    return None


# Funkcja interpolująca 8x8 na 64x64
def bilinear_interpolation_8x8_to_64x64(table_data):
    x = np.linspace(0, 7, 8)  # Oryginalna siatka 8x8
    y = np.linspace(0, 7, 8)  # Oryginalna siatka 8x8
    f = interpolate.interp2d(x, y, table_data, kind='linear')

    x_new = np.linspace(0, 7, 64)  # Nowa siatka 64x64
    y_new = np.linspace(0, 7, 64)  # Nowa siatka 64x64

    table_data_64x64 = f(x_new, y_new)
    return table_data_64x64


# Funkcja rysująca tablicę na canvasie
def draw_interpolated_table(canvas, table_data, timestamp):
    canvas.create_text(200, 20, text=f"Timestamp: {timestamp}", font=("Helvetica", 12))

    # Przeprowadzamy interpolację biliniową
    interpolated_data = bilinear_interpolation_8x8_to_64x64(table_data)

    # Rysowanie tablicy na canvasie
    for row in range(64):
        for col in range(64):
            x1 = 80 + col * 5  # Szerokość komórki
            y1 = 50 + row * 5  # Wysokość komórki
            x2 = x1 + 5
            y2 = y1 + 5

            # Kolorowanie na podstawie wartości w komórce
            value = interpolated_data[row][col]
            color = interpolate_color(value, interpolated_data.min(), interpolated_data.max())

            # Rysowanie prostokąta z kolorem w odpowiedniej pozycji
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")


# Funkcja interpolująca kolor na podstawie wartości
def interpolate_color(value, min_value, max_value):
    norm_value = (value - min_value) / (max_value - min_value)  # Normalizowanie
    blue = int((1 - norm_value) * 255)
    red = int(norm_value * 255)
    return f"#{red:02x}{0:02x}{blue:02x}"


# Funkcja, która po naciśnięciu przycisku szuka danych w MongoDB i aktualizuje tablicę na canvasie
def search_and_update(vehicle_entry, canvas):
    """Funkcja, która po naciśnięciu przycisku szuka danych w MongoDB i aktualizuje etykietę."""
    name = vehicle_entry.get()

    if not name:
        messagebox.showerror("Błąd", "Wpisz nazwę pojazdu")
        return
    
    def update_data():
        result = search_database(name)

        if result:
            table_data = [result['distances'][i:i + 8] for i in range(0, len(result['distances']), 8)]
            canvas.delete("all")
            draw_interpolated_table(canvas, table_data, result.get("timestamp"))


        id = canvas.after(200, update_data)
        global stop1
        if(stop1):
            canvas.after_cancel(id)
        stop1 = False

    threading.Thread(target=update_data(), daemon=True).start()

def stop(vehicle_entry, canvas):
    global stop1
    stop1 = True

def create_live_tab(notebook):
    live_tab = Frame(notebook)
    notebook.add(live_tab, text="Live")

    live_frame = ttk.Frame(live_tab)
    live_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

    vehicle_entry = ttk.Entry(live_frame, width=30)
    vehicle_entry.pack(pady=5)


    canvas = Canvas(live_frame, width=320, height=320)
    canvas.pack(pady=10, anchor="w", padx=(170, 0))


    search_button = ttk.Button(live_frame, text="Szukaj",
                               command=lambda: search_and_update(vehicle_entry, canvas))
    search_button.pack(pady=10)

    stop_button = ttk.Button(live_frame, text="Stop",
                             command=lambda:stop(vehicle_entry, canvas))
    stop_button.pack(pady=10)

    return live_tab

