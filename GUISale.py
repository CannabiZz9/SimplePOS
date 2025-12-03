from tkinter import ttk, Tk
from ttkthemes import ThemedTk
from tkcalendar import Calendar
from datetime import datetime
import sqlite3

class SalesViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Viewer")

        # 🔹 Create a custom style for the scrollbar
        style = ttk.Style()
        style.configure("Vertical.TScrollbar", gripcount=0, background="gray", troughcolor="lightgray", borderwidth=2, width=30)  # 👈 Make it wider

        # Create a frame for the date pickers and the update button
        date_frame = ttk.LabelFrame(root, text="Select Date Range")
        date_frame.pack(fill="both", padx=10, pady=10)

        # Create the date pickers
        self.date_picker1 = Calendar(date_frame, selectmode='day')
        self.date_picker1.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.date_picker2 = Calendar(date_frame, selectmode='day')
        self.date_picker2.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Create the update button
        update_button = ttk.Button(date_frame, text="Update Sales", command=self.populate_treeview)
        update_button.pack(side="left", padx=5, pady=5)

        # Create a menu for selecting the type of sales report
        report_menu = ttk.Combobox(date_frame, values=["ByBill","Daily", "Weekly", "Monthly", "Quarterly", "Yearly"])
        report_menu.set("ByBill")
        report_menu.pack(side="left", padx=5, pady=5)

        # Save the report menu as an instance variable
        self.report_menu = report_menu

        # 🔹 Create a frame for the treeview and scrollbar
        tree_frame = ttk.Frame(root)
        tree_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # 🔹 Create a **thick vertical scrollbar**
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", style="Vertical.TScrollbar")

        # 🔹 Create the Treeview and configure the scrollbar
        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Bill Number", "Sale Date", "Sale Time", "Price Sold", "Employee"), height=25, yscrollcommand=tree_scroll.set)

        # 🔹 Configure the scrollbar to scroll the treeview
        tree_scroll.config(command=self.tree.yview)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")  # 🔹 Place scrollbar to the right with a **thicker size**

        # Configure Treeview headings
        self.tree.heading("#0", text="")
        self.tree.heading("#1", text="Bill Number")
        self.tree.heading("#2", text="Sale Date")
        self.tree.heading("#3", text="Sale Time")
        self.tree.heading("#4", text="Price Sold")
        self.tree.heading("#5", text="Employee")

        # Apply font settings
        self.tree.tag_configure('font', font=('Arial', 17))

        # Populate the treeview initially
        self.populate_treeview()

    def populate_treeview(self):
        start_date_str = self.date_picker1.get_date()
        end_date_str = self.date_picker2.get_date()
        
        date_format = "%m/%d/%y"
        
        date_object1 = datetime.strptime(start_date_str, date_format)
        date_object2 = datetime.strptime(end_date_str, date_format)

        start_date = date_object1.strftime("%Y-%m-%d")
        end_date = date_object2.strftime("%Y-%m-%d")

        report_type = self.report_menu.get()

        try:
            with sqlite3.connect('sales_history.db') as connection:
                cursor = connection.cursor()

                # Customize the query based on the selected report type
                if report_type == "Daily":
                    # Customize the query for weekly report
                    query = """
                        SELECT strftime('%Y-%m-%d', sale_date) AS date, COUNT(DISTINCT bill_number) AS bill_count, SUM(price_sold) AS total_price_sold
                        FROM sales
                        WHERE sale_date >= ? AND sale_date <= ?
                        GROUP BY date
                        ORDER BY date
                    """
                    self.tree.heading("#1", text="Day")
                    self.tree.heading("#2", text="Bill Count")
                    self.tree.heading("#3", text="Total Price Sold")
                    self.tree.heading("#4", text="")
                    self.tree.heading("#5", text="")
                    self.tree.heading("#6", text="")
                    
                elif report_type == "ByBill":
                    # Customize the query for Billy report
                    query = """
                        SELECT bill_number, sale_date, sale_time, price_sold, employee FROM sales
                        WHERE sale_date >= ? AND sale_date <= ?
                    """
                    self.tree.heading("#0", text="")
                    self.tree.heading("#1", text="Bill Number")
                    self.tree.heading("#2", text="Sale Date")
                    self.tree.heading("#3", text="Sale Time")
                    self.tree.heading("#4", text="Price Sold")
                    self.tree.heading("#5", text="Employee")    
                    
                elif report_type == "Weekly":
                    # Customize the query for weekly report
                    query = """
                        SELECT strftime('%Y-%W', sale_date) AS week, SUM(price_sold) AS total_price_sold
                        FROM sales
                        WHERE sale_date >= ? AND sale_date <= ?
                        GROUP BY week
                        ORDER BY week
                    """
                    self.tree.heading("#1", text="Week")
                    self.tree.heading("#2", text="Total Price Sold")
                    self.tree.heading("#3", text="")
                    self.tree.heading("#4", text="")
                    self.tree.heading("#5", text="")
                    self.tree.heading("#6", text="")
                    
                    
                elif report_type == "Monthly":
                    # Customize the query for monthly report
                    query = """
                        SELECT strftime('%Y-%m', sale_date) AS month, SUM(price_sold) AS total_price_sold
                        FROM sales
                        WHERE sale_date >= ? AND sale_date <= ?
                        GROUP BY month
                        ORDER BY month
                    """
                    self.tree.heading("#1", text="Month")
                    self.tree.heading("#2", text="Total Price Sold")
                    self.tree.heading("#3", text="")
                    self.tree.heading("#4", text="")
                    self.tree.heading("#5", text="")
                    self.tree.heading("#6", text="")
                    
                elif report_type == "Quarterly":
                    # Customize the query for quarterly report
                    query = """
                        SELECT strftime('%Y-Q', sale_date) || CAST(CEIL(strftime('%m', sale_date) / 3.0) AS INTEGER) AS quarter,
                        SUM(price_sold) AS total_price_sold
                        FROM sales
                        WHERE sale_date >= ? AND sale_date <= ?
                        GROUP BY quarter
                        ORDER BY quarter
                    """
                    self.tree.heading("#1", text="Quarter")
                    self.tree.heading("#2", text="Total Price Sold")
                    self.tree.heading("#3", text="")
                    self.tree.heading("#4", text="")
                    self.tree.heading("#5", text="")
                    self.tree.heading("#6", text="")
                    
                elif report_type == "Yearly":
                    # Customize the query for yearly report
                    query = """
                        SELECT strftime('%Y', sale_date) AS year, SUM(price_sold) AS total_price_sold
                        FROM sales
                        WHERE sale_date >= ? AND sale_date <= ?
                        GROUP BY year
                        ORDER BY year
                    """
                    self.tree.heading("#1", text="Year")
                    self.tree.heading("#2", text="Total Price Sold")
                    self.tree.heading("#3", text="")
                    self.tree.heading("#4", text="")
                    self.tree.heading("#5", text="")
                    self.tree.heading("#6", text="")
                    

                params = (start_date, end_date)
                cursor.execute(query, params)
                self.tree.delete(*self.tree.get_children())
                for row in cursor:
                    self.tree.insert("", "end", values=list(row) + [""] * (6 - len(row)))

        except sqlite3.Error as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    root = ThemedTk(theme="arc")  # You can change the theme here
    app = SalesViewerApp(root)
    root.mainloop()
