import tkinter as tk
from tkinter import filedialog, messagebox
import requests
from report_service import submit_report

def open_report_window(user_id):
    win = tk.Tk()
    win.title("Submit Report")
    win.geometry("400x400")

    tk.Label(win, text="Latitude:").pack()
    lat_entry = tk.Entry(win)
    lat_entry.pack()

    tk.Label(win, text="Longitude:").pack()
    lng_entry = tk.Entry(win)
    lng_entry.pack()

    tk.Label(win, text="Type Hint:").pack()
    type_entry = tk.Entry(win)
    type_entry.pack()

    tk.Label(win, text="Description:").pack()
    desc_entry = tk.Entry(win)
    desc_entry.pack()

    file_path = tk.StringVar()

    def choose_file():
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png")])
        file_path.set(path)

    tk.Button(win, text="Upload Image", command=choose_file).pack()
    tk.Label(win, textvariable=file_path).pack()

    def submit():
        lat = float(lat_entry.get())
        lng = float(lng_entry.get())
        type_hint = type_entry.get()
        description = desc_entry.get()
        image = file_path.get()
        submit_report(user_id, lat, lng, type_hint, description, image)
        # Call ML API
        resp = requests.post("http://127.0.0.1:5000/classify", json={"image_path": image})
        result = resp.json()
        messagebox.showinfo("ML Result", f"Label: {result['suggested_label']}\nConfidence: {result['confidence']}")

    tk.Button(win, text="Submit Report", command=submit).pack(pady=10)
    win.mainloop()
