import tkinter as tk
from tkinter import ttk
import sqlite3

class SalesViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Viewer")

        self.tree = ttk.Treeview(root, columns=("ID", "Bill Number", "Sale Date", "Sale Time", "Price Sold", "Employee"))
        self.tree.heading("#1", text="ID")
        self.tree.heading("#2", text="Bill Number")
        self.tree.heading("#3", text="Sale Date")
        self.tree.heading("#4", text="Sale Time")
        self.tree.heading("#5", text="Price Sold")
        self.tree.heading("#6", text="Employee")
        self.tree.pack(padx=10, pady=10)

        self.populate_treeview()

    def populate_treeview(self):
        # Connect to the database
        connection = sqlite3.connect('sales_history.db')
        cursor = connection.cursor()

        # Retrieve all data from the sales table
        cursor.execute('SELECT * FROM sales')
        rows = cursor.fetchall()

        # Close the connection
        connection.close()

        # Populate the treeview
        for row in rows:
            self.tree.insert("", "end", values=row)

if __name__ == "__main__":
    root = tk.Tk()
    app = SalesViewerApp(root)
    root.mainloop()
