import tkinter as tk
from db_helper import get_connection

def open_worker_dashboard():
    win = tk.Tk()
    win.title("Worker / Truck Dashboard")
    win.geometry("500x400")

    tk.Label(win, text="Truck ID:").pack()
    truck_entry = tk.Entry(win)
    truck_entry.pack()

    tk.Label(win, text="Latitude:").pack()
    lat_entry = tk.Entry(win)
    lat_entry.pack()

    tk.Label(win, text="Longitude:").pack()
    lng_entry = tk.Entry(win)
    lng_entry.pack()

    tk.Label(win, text="Speed:").pack()
    speed_entry = tk.Entry(win)
    speed_entry.pack()

    def post_telemetry():
        truck_id = int(truck_entry.get())
        lat = float(lat_entry.get())
        lng = float(lng_entry.get())
        speed = float(speed_entry.get())
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO telemetry (truck_id,lat,lng,speed) VALUES (:t,:lat,:lng,:s)",
                    {'t': truck_id,'lat':lat,'lng':lng,'s':speed})
        conn.commit()
        conn.close()
        tk.messagebox.showinfo("Success","Telemetry posted!")

    tk.Button(win, text="Post Telemetry", command=post_telemetry).pack(pady=5)
    win.mainloop()
