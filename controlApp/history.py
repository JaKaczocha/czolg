import pymongo
from datetime import datetime
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Frame, Canvas
from pymongo import MongoClient
import tkinter as tk
import numpy as np
from scipy import interpolate

# Połączenie z MongoDB (tu wpisz swoje dane logowania)
client = pymongo.MongoClient(
    "mongodb+srv://jakub44295:<>@cluster0.x148r.mongodb.net/?retryWrites=true&w=majority")
db = client["tank_data"]  # Baza danych
collection = db["tank_data"]  # Kolekcja

counter = 1


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


def wyszukaj(data_od_entry, czas_od_entry, data_do_entry, czas_do_entry, vehicle_entry, counter, canvas):
    """Wyszukiwanie i wyświetlanie wyników z bazy danych w formie tablicy 8x8."""
    try:
        data_od_str = data_od_entry.get()  # Używamy Entry do pobrania daty w formacie string
        czas_od = czas_od_entry.get()  # Pobieramy czas z Entry
        data_do_str = data_do_entry.get()  # Używamy Entry do pobrania daty w formacie string
        czas_do = czas_do_entry.get()  # Pobieramy czas z Entry
        vehicle_name = vehicle_entry.get()  # Pobieramy nazwę pojazdu

        print(f"Przeszukiwany pojazd: {vehicle_name}, licznik: {counter}")
        counter += 1

        # Łączenie daty i czasu, aby stworzyć pełną datę i godzinę
        datetime_od = datetime.combine(datetime.strptime(data_od_str, "%d.%m.%Y"),
                                       datetime.strptime(czas_od, "%H:%M:%S").time())
        datetime_do = datetime.combine(datetime.strptime(data_do_str, "%d.%m.%Y"),
                                       datetime.strptime(czas_do, "%H:%M:%S").time())

        # Wyświetlanie dat i godzin w konsoli
        print(f"Data od: {datetime_od} | Czas od: {czas_od}")
        print(f"Data do: {datetime_do} | Czas do: {czas_do}")

        if datetime_od > datetime_do:
            messagebox.showerror("Błąd", "Data początkowa nie może być późniejsza niż końcowa!")
        elif not vehicle_name.strip():
            messagebox.showerror("Błąd", "Nazwa pojazdu nie może być pusta!")
        else:
            # Zapytanie do bazy danych MongoDB
            query = {
                "name": vehicle_name,
                "timestamp": {
                    "$gt": datetime_od,  # Tylko dokumenty z timestampem > datetime_od
                    "$lt": datetime_do  # Tylko dokumenty z timestampem < datetime_do
                }
            }

            # Odczytanie danych
            result = collection.find(query)

            # Przekształcenie kursora w listę
            results_list = list(result)

            if len(results_list) > 0:
                messagebox.showinfo("Wynik",
                                    f"Znaleziono {len(results_list)} wyników dla pojazdu '{vehicle_name}' od {datetime_od} do {datetime_do}")

                def display_data(i=0):
                    if i < len(results_list):
                        data = results_list[i]
                        timestamp = data["timestamp"]
                        values = data["distances"]

                        # Przekształcenie danych w tablicę 8x8
                        table_data = [values[i:i + 8] for i in range(0, len(values), 8)]

                        # Wyczyszczenie canvas przed narysowaniem nowej tablicy
                        canvas.delete("all")

                        # Rysowanie tytułu (timestamp)
                        canvas.create_text(200, 20, text=f"Timestamp: {timestamp}", font=("Helvetica", 12))

                        # Rysowanie tablicy 8x8
                        draw_interpolated_table(canvas, table_data, timestamp)

                        # Obliczenie różnicy czasu między kolejnymi dokumentami
                        if i + 1 < len(results_list):
                            next_timestamp = results_list[i + 1]["timestamp"]
                            delay = (next_timestamp - timestamp).total_seconds() * 1000  # opóźnienie w milisekundach
                        else:
                            delay = 1000  # Domyślne opóźnienie na końcu

                        # Ustawienie opóźnienia przed wyświetleniem kolejnego dokumentu
                        canvas.after(int(delay), display_data, i + 1)  # Wywołanie funkcji po opóźnieniu

                # Rozpoczęcie wyświetlania danych z opóźnieniem
                display_data()

            else:
                messagebox.showinfo("Brak wyników", "Brak danych spełniających kryteria.")
                print("Brak danych dla podanych kryteriów.")

    except ValueError:
        messagebox.showerror("Błąd", "Nieprawidłowy format daty lub czasu!")


def create_history_tab(notebook):
    history_tab = Frame(notebook)
    notebook.add(history_tab, text="History")

    # Zawartość zakładki "History"
    history_frame = ttk.Frame(history_tab)
    history_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

    # Układ pól w siatce
    for i in range(5):
        history_frame.columnconfigure(i, weight=1)

    # Etykieta i pole "Data od"
    ttk.Label(history_frame, text="Od:", font=("Helvetica", 9)).grid(row=0, column=0, padx=8, pady=4, sticky=E)
    data_od_entry = ttk.Entry(history_frame, width=12)
    data_od_entry.grid(row=0, column=1, padx=8, pady=4, sticky=W)

    # Pole "Czas od"
    czas_od_entry = ttk.Entry(history_frame, width=12)
    czas_od_entry.insert(0, "00:00:00")
    czas_od_entry.grid(row=0, column=2, padx=8, pady=4, sticky=W)

    # Etykieta i pole "Data do"
    ttk.Label(history_frame, text="Do:", font=("Helvetica", 9)).grid(row=2, column=0, padx=8, pady=4, sticky=E)
    data_do_entry = ttk.Entry(history_frame, width=12)
    data_do_entry.grid(row=2, column=1, padx=8, pady=4, sticky=W)

    # Pole "Czas do"
    czas_do_entry = ttk.Entry(history_frame, width=12)
    czas_do_entry.insert(0, "23:59:59")
    czas_do_entry.grid(row=2, column=2, padx=8, pady=4, sticky=W)

    # Etykieta i pole "Nazwa pojazdu"
    ttk.Label(history_frame, text="Nazwa pojazdu:", font=("Helvetica", 9)).grid(row=3, column=0, padx=8, pady=4,
                                                                                sticky=E)
    vehicle_entry = ttk.Entry(history_frame, width=20)
    vehicle_entry.grid(row=3, column=1, padx=8, pady=4, sticky=W)

    # Przycisk "Wyszukaj" na dole, zajmujący dwie kolumny
    canvas = Canvas(history_frame, width=600, height=600)
    canvas.grid(row=4, column=0, columnspan=5, padx=8, pady=10)

    wyszukaj_button = ttk.Button(
        history_frame,
        text="Wyszukaj",
        bootstyle=SUCCESS,
        command=lambda: wyszukaj(data_od_entry, czas_od_entry, data_do_entry, czas_do_entry, vehicle_entry, counter,
                                 canvas)
    )
    wyszukaj_button.grid(row=3, column=1, columnspan=4, pady=15)

    return history_tab