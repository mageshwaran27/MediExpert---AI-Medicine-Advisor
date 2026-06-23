import tkinter as tk
from tkinter import ttk, messagebox
from db_helper import get_connection

def open_admin_dashboard():
    win = tk.Tk()
    win.title("Admin Dashboard")
    win.geometry("700x400")

    tree = ttk.Treeview(win, columns=("ID","User","Type","Label","Confidence","Status"), show='headings')
    tree.heading("ID", text="Report ID")
    tree.heading("User", text="User ID")
    tree.heading("Type", text="Type Hint")
    tree.heading("Label", text="Suggested Label")
    tree.heading("Confidence", text="Confidence")
    tree.heading("Status", text="Status")
    tree.pack(fill=tk.BOTH, expand=True)

    def load_reports():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT report_id,user_id,type_hint,suggested_label,confidence,status FROM reports")
        rows = cur.fetchall()
        for row in rows:
            tree.insert("", tk.END, values=row)
        conn.close()

    def update_status():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error","Select a report")
            return
        report_id = tree.item(selected[0])['values'][0]
        new_status = status_var.get()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE reports SET status=:s, updated_at=CURRENT_TIMESTAMP WHERE report_id=:id",
                    {'s': new_status, 'id': report_id})
        conn.commit()
        conn.close()
        messagebox.showinfo("Success","Status Updated")
        tree.delete(*tree.get_children())
        load_reports()

    status_var = tk.StringVar()
    tk.Label(win, text="Update Status:").pack()
    tk.Entry(win, textvariable=status_var).pack()
    tk.Button(win, text="Update Selected Report", command=update_status).pack(pady=5)
    tk.Button(win, text="Load Reports", command=load_reports).pack(pady=5)

    win.mainloop()
