import json
import os
from datetime import datetime
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox

DATA_FILE = os.path.join(os.path.dirname(__file__), "viajes_data.json")

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("transports", [])
            data.setdefault("trips", [])
            return data
    except Exception:
        return {"transports": [], "trips": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def show_message(title, message):
    box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
    box.add_widget(Label(text=message, halign="left", valign="middle"))
    btn = Button(text="Aceptar", size_hint_y=None, height=dp(46))
    box.add_widget(btn)
    pop = Popup(title=title, content=box, size_hint=(.9, .42))
    btn.bind(on_release=pop.dismiss)
    pop.open()

class TravelApp(App):
    def build(self):
        self.title = "Agencia de viajes"
        self.data = load_data()
        self.root_box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        header = Label(text="[b]AGENCIA DE VIAJES[/b]", markup=True, size_hint_y=None, height=dp(42), font_size="22sp")
        self.root_box.add_widget(header)

        nav = GridLayout(cols=3, size_hint_y=None, height=dp(46), spacing=dp(5))
        for text, callback in [("Registrar viaje", self.show_trip_form), ("Transportes", self.show_transport_form), ("Viajes / lugares", self.show_trips)]:
            b = Button(text=text)
            b.bind(on_release=lambda instance, cb=callback: cb())
            nav.add_widget(b)
        self.root_box.add_widget(nav)

        self.content_area = BoxLayout(orientation="vertical")
        self.root_box.add_widget(self.content_area)
        self.show_trip_form()
        return self.root_box

    def clear_content(self):
        self.content_area.clear_widgets()

    def field(self, hint, value=""):
        return TextInput(hint_text=hint, text=value, multiline=False, size_hint_y=None, height=dp(44))

    def show_trip_form(self, *_):
        self.clear_content()
        sc = ScrollView()
        form = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None, padding=(0, dp(5)))
        form.bind(minimum_height=form.setter("height"))
        form.add_widget(Label(text="Nuevo viaje", size_hint_y=None, height=dp(30), bold=True))
        self.trip_title = self.field("Título del viaje (ej. Puerto Vallarta)")
        form.add_widget(self.trip_title)
        form.add_widget(Label(text="Usa formato AAAA-MM-DD y hora HH:MM (24 horas).", size_hint_y=None, height=dp(30)))
        row1 = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(44))
        self.depart_date = self.field("Salida: AAAA-MM-DD")
        self.depart_time = self.field("Hora: HH:MM")
        row1.add_widget(self.depart_date); row1.add_widget(self.depart_time); form.add_widget(row1)
        row2 = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(44))
        self.return_date = self.field("Regreso: AAAA-MM-DD")
        self.return_time = self.field("Hora: HH:MM")
        row2.add_widget(self.return_date); row2.add_widget(self.return_time); form.add_widget(row2)

        names = [t["name"] for t in self.data["transports"]]
        self.transport_spinner = Spinner(text=(names[0] if names else "Primero registra un transporte"),
                                         values=names, size_hint_y=None, height=dp(44))
        form.add_widget(self.transport_spinner)
        save_btn = Button(text="Guardar viaje", size_hint_y=None, height=dp(48))
        save_btn.bind(on_release=self.save_trip)
        form.add_widget(save_btn)
        hint = Label(text="Después de guardar, abre “Viajes / lugares” para marcar los asientos ocupados.",
                     size_hint_y=None, height=dp(52), halign="left")
        form.add_widget(hint)
        sc.add_widget(form); self.content_area.add_widget(sc)

    def show_transport_form(self, *_):
        self.clear_content()
        sc = ScrollView()
        form = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None, padding=(0, dp(5)))
        form.bind(minimum_height=form.setter("height"))
        form.add_widget(Label(text="Registrar medio de transporte", size_hint_y=None, height=dp(34), bold=True))
        self.transport_name = self.field("Nombre / identificación (ej. Camión 01)")
        form.add_widget(self.transport_name)
        self.transport_type = Spinner(text="Camión", values=("Camión", "Automóvil", "Van", "Avión", "Otro"),
                                      size_hint_y=None, height=dp(44))
        form.add_widget(self.transport_type)
        self.transport_seats = self.field("Cantidad de lugares (ej. 40)")
        form.add_widget(self.transport_seats)
        btn = Button(text="Guardar transporte", size_hint_y=None, height=dp(48))
        btn.bind(on_release=self.save_transport)
        form.add_widget(btn)
        form.add_widget(Label(text="Transportes registrados:", size_hint_y=None, height=dp(30)))
        for t in self.data["transports"]:
            form.add_widget(Label(text=f'{t["name"]} · {t["type"]} · {t["seats"]} lugares',
                                  size_hint_y=None, height=dp(30)))
        sc.add_widget(form); self.content_area.add_widget(sc)

    def save_transport(self, *_):
        name = self.transport_name.text.strip()
        try:
            seats = int(self.transport_seats.text.strip())
            if seats < 1 or seats > 300:
                raise ValueError()
        except ValueError:
            show_message("Dato incorrecto", "Escribe una cantidad de lugares entre 1 y 300.")
            return
        if not name:
            show_message("Falta información", "Escribe el nombre o identificación del transporte.")
            return
        if any(t["name"].lower() == name.lower() for t in self.data["transports"]):
            show_message("Ya existe", "Usa un nombre distinto para este transporte.")
            return
        self.data["transports"].append({"name": name, "type": self.transport_type.text, "seats": seats})
        save_data(self.data)
        show_message("Guardado", "El medio de transporte quedó registrado.")
        self.show_transport_form()

    def save_trip(self, *_):
        title = self.trip_title.text.strip()
        fields = [
            (self.depart_date.text.strip(), "%Y-%m-%d", "fecha de salida"),
            (self.depart_time.text.strip(), "%H:%M", "hora de salida"),
            (self.return_date.text.strip(), "%Y-%m-%d", "fecha de regreso"),
            (self.return_time.text.strip(), "%H:%M", "hora de regreso")
        ]
        if not title:
            show_message("Falta información", "Escribe el título del viaje.")
            return
        try:
            parsed = [datetime.strptime(value, fmt) for value, fmt, label in fields]
        except ValueError:
            show_message("Formato incorrecto", "Revisa fechas AAAA-MM-DD y horas HH:MM. Ejemplo: 2026-12-25 y 08:30.")
            return
        if parsed[2] < parsed[0] or (parsed[2].date() == parsed[0].date() and parsed[3].time() < parsed[1].time()):
            show_message("Fechas incorrectas", "El regreso no puede ser anterior a la salida.")
            return
        transport = next((t for t in self.data["transports"] if t["name"] == self.transport_spinner.text), None)
        if not transport:
            show_message("Falta transporte", "Registra un medio de transporte primero y selecciónalo.")
            return
        trip = {
            "id": str(int(datetime.now().timestamp() * 1000)),
            "title": title,
            "depart_date": fields[0][0], "depart_time": fields[1][0],
            "return_date": fields[2][0], "return_time": fields[3][0],
            "transport": transport["name"], "transport_type": transport["type"],
            "seats": transport["seats"], "occupied": []
        }
        self.data["trips"].append(trip)
        save_data(self.data)
        show_message("Viaje guardado", "El viaje se registró correctamente.")
        self.show_trips()

    def show_trips(self, *_):
        self.clear_content()
        sc = ScrollView()
        listing = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, padding=(0, dp(5)))
        listing.bind(minimum_height=listing.setter("height"))
        if not self.data["trips"]:
            listing.add_widget(Label(text="Todavía no hay viajes registrados.", size_hint_y=None, height=dp(45)))
        for trip in self.data["trips"]:
            card = BoxLayout(orientation="vertical", spacing=dp(5), size_hint_y=None, padding=dp(8))
            card.bind(minimum_height=card.setter("height"))
            occupied = len(trip.get("occupied", []))
            card.add_widget(Label(text=f'[b]{trip["title"]}[/b]', markup=True, size_hint_y=None, height=dp(30)))
            card.add_widget(Label(text=f'Salida: {trip["depart_date"]} {trip["depart_time"]}  |  Regreso: {trip["return_date"]} {trip["return_time"]}',
                                  size_hint_y=None, height=dp(42)))
            card.add_widget(Label(text=f'Transporte: {trip["transport"]} ({trip["transport_type"]}) · {occupied}/{trip["seats"]} ocupados',
                                  size_hint_y=None, height=dp(34)))
            btn = Button(text="Ver / marcar lugares", size_hint_y=None, height=dp(44))
            btn.bind(on_release=lambda instance, tid=trip["id"]: self.show_seats(tid))
            card.add_widget(btn)
            listing.add_widget(card)
        sc.add_widget(listing); self.content_area.add_widget(sc)

    def show_seats(self, trip_id):
        trip = next((t for t in self.data["trips"] if t["id"] == trip_id), None)
        if not trip:
            return
        self.clear_content()
        main = BoxLayout(orientation="vertical", spacing=dp(6))
        main.add_widget(Label(text=f'{trip["title"]} — lugares', size_hint_y=None, height=dp(34), bold=True))
        main.add_widget(Label(text="Marca la casilla para indicar que el lugar está OCUPADO.",
                              size_hint_y=None, height=dp(40)))
        sc = ScrollView()
        grid = GridLayout(cols=3, spacing=dp(5), padding=dp(4), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        checks = {}
        occupied = set(int(n) for n in trip.get("occupied", []))
        for n in range(1, int(trip["seats"]) + 1):
            cell = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(42), spacing=dp(3))
            cb = CheckBox(active=(n in occupied), size_hint_x=None, width=dp(34))
            label = Label(text=f"Lugar {n}", halign="left")
            cb.bind(active=lambda instance, value, seat=n: self.toggle_seat(trip_id, seat, value))
            cell.add_widget(cb); cell.add_widget(label); grid.add_widget(cell)
            checks[n] = cb
        sc.add_widget(grid)
        main.add_widget(sc)
        legend = Label(text="Casilla marcada = ocupado · Casilla vacía = disponible",
                       size_hint_y=None, height=dp(36))
        main.add_widget(legend)
        back = Button(text="Volver a viajes", size_hint_y=None, height=dp(44))
        back.bind(on_release=self.show_trips)
        main.add_widget(back)
        self.content_area.add_widget(main)

    def toggle_seat(self, trip_id, seat, is_occupied):
        trip = next((t for t in self.data["trips"] if t["id"] == trip_id), None)
        if not trip:
            return
        occupied = set(int(n) for n in trip.get("occupied", []))
        if is_occupied:
            occupied.add(seat)
        else:
            occupied.discard(seat)
        trip["occupied"] = sorted(occupied)
        save_data(self.data)

if __name__ == "__main__":
    TravelApp().run()
