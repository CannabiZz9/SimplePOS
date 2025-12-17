import os
import sys
import subprocess
import tkinter as tk
import sqlite3
from datetime import datetime
import tempfile
import threading

# Third-party libraries
import customtkinter as ctk
from CTkListbox import *
import pygame



# Windows specific imports
try:
    import win32api
    import win32print
except ImportError:
    print("Warning: win32 libraries not found. Printing will not work.")

# --- Configuration ---
ctk.set_appearance_mode('dark')
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1.0)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Database Setup ---
connection = sqlite3.connect('sales_history.db', check_same_thread=False)
cursor = connection.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_number TEXT,
        sale_date DATE,
        sale_time TIME,
        price_sold REAL,
        employee TEXT
    )
''')

class NotificationPopup(ctk.CTkToplevel):
    def __init__(self, master, message, **kwargs):
        super().__init__(master, **kwargs)
        
        # 1. Configuration
        self.overrideredirect(True) # Remove window borders
        self.attributes("-topmost", True) # Keep on top
        
        # 2. Size and Position (Top Right of the App)
        width = 300
        height = 60
        
        # Calculate position relative to the main window
        # We add offset so it doesn't cover the close button of the main app
        pos_x = master.winfo_x() + master.winfo_width() - width - 30
        pos_y = master.winfo_y() + 80 # Below the Top Bar
        
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        
        # 3. Design
        self.frame = ctk.CTkFrame(self, fg_color="#333333", border_width=2, border_color="#00C853")
        self.frame.pack(fill="both", expand=True)
        
        # Icon/Label
        self.lbl = ctk.CTkLabel(self.frame, text=f"🔔 {message}", font=("Arial", 14), text_color="white")
        self.lbl.pack(expand=True, padx=10, pady=10)
        
        # 4. Auto-Close after 3 seconds
        self.after(3000, self.destroy)
        
        # Close on click
        self.lbl.bind("<Button-1>", lambda e: self.destroy())


# ==============================================================================
# CLASS: POS TERMINAL (Represents ONE Station)
# ==============================================================================
class POSTerminal(ctk.CTkFrame):
    def __init__(self, master, station_id, **kwargs):
        super().__init__(master, **kwargs)
        self.station_id = station_id
        
        # --- Independent Variables ---
        self.cart = []
        self.Sumprice = 0
        self.allitem_quantity = 0
        self.employee = f"Station_{station_id}"
        
        # Layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Header Color
        title_color = "#1F6AA5" if station_id == 1 else "#D84315"
        self.header = ctk.CTkLabel(self, text=f"POS STATION {station_id}", fg_color=title_color, height=35, font=("Arial", 18, "bold"))
        self.header.pack(fill="x")
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        self.create_widgets()

    def create_widgets(self):
        # Sound Init
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                try: pygame.mixer.music.load(resource_path("s.mp3"))
                except: pass
            except: pass

       # --- CALCULATOR (Left) ---
        self.calc_area = ctk.CTkFrame(self.content_frame, width=800, height=700)
        self.calc_area.pack_propagate(False) 
        self.calc_area.pack(side="left", padx=150) # Removed expand=True
        
        self.price_entry = ctk.CTkEntry(self.calc_area, height=60, font=("Arial", 40), justify="right")
        self.price_entry.insert(0, "0")
        self.price_entry.pack(fill="x", padx=10, pady=10)
        
        # Keypad
        self.keypad_frame = ctk.CTkFrame(self.calc_area, fg_color="transparent")
        self.keypad_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        btn_bg, btn_fg, btn_active = "#002C5E", "white", "#505050"
        
        keys = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2), ('C', 0, 3),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), ('<--', 1, 3),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2), ('x', 2, 3),
            ('0', 3, 0), ('.', 3, 2), ('ADD', 3, 3) 
        ]
        
        for key, r, c in keys:
            cmd = lambda x=key: self.keypad_action(x)
            bg_color = btn_bg
            if key == 'C': bg_color = "#C62828"
            elif key == '<--': bg_color = "#EF6C00"
            elif key == 'x': bg_color = "#1A61B3"
            elif key == 'ADD': bg_color = "green"
            
            colspan = 2 if key == '0' else 1
            
            btn = tk.Button(self.keypad_frame, text=key, command=cmd,
                            font=("Arial", 30, "bold"), bg=bg_color, fg=btn_fg,
                            activebackground=btn_active, activeforeground=btn_fg,
                            relief="flat", borderwidth=0)
            btn.grid(row=r, column=c, columnspan=colspan, padx=3, pady=3, sticky="nsew")

        for i in range(4): self.keypad_frame.columnconfigure(i, weight=1)
        for i in range(4): self.keypad_frame.rowconfigure(i, weight=1)

        # --- CART (Right) ---
        self.cart_area = ctk.CTkFrame(self.content_frame, width=1300) 
        self.cart_area.pack(side="left", padx=50)
        
        self.cart_listbox = CTkListbox(self.cart_area, height=550, font=("Angsana New", 45))
        self.cart_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.btn_row = ctk.CTkFrame(self.cart_area)
        self.btn_row.pack(fill="x", pady=5)
        
        self.btn_remove = ctk.CTkButton(self.btn_row, text="Remove", command=self.removefromcart , state="disabled", fg_color="#555", width=200, height=90, font=("Arial", 18))
        self.btn_remove.pack(side="right", padx=5, expand=True)
        
        self.btn_clear = ctk.CTkButton(self.btn_row, text="Clear", command=self.clearcart , state="disabled", fg_color="#555", width=200, height=90, font=("Arial", 18))
        self.btn_clear.pack(side="left", padx=5, expand=True)
        
        self.lbl_total = ctk.CTkLabel(self.cart_area, text="0 ชิ้น \ 0 ฿", font=("Arial", 40, "bold"), text_color="#4CAF50")
        self.lbl_total.pack(pady=5)
        
        self.btn_checkout = ctk.CTkButton(self.cart_area, text="CHECKOUT", command=self.Checkout, 
                                          font=("Arial", 30, "bold"), height=90, fg_color="#00C853", state="disabled")
        self.btn_checkout.pack(fill="x", padx=10, pady=(0, 10))

    # --- LOGIC ---
    def keypad_action(self, key):
        self.play_sound()
        if key == 'C': 
            self.price_entry.delete(0, 'end')
            self.price_entry.insert(0, "0")
        elif key == '<--': 
            curr = self.price_entry.get()
            if len(curr) > 0: self.price_entry.delete(len(curr)-1, 'end')
        elif key == 'x': 
            # CHANGE: Check if value is "0" OR if "*" already exists
            curr = self.price_entry.get()
            if curr != "0" and '*' not in curr:
                self.price_entry.insert('end', '*')
        elif key == 'ADD': 
            self.add_to_cart()
        else:
            if self.price_entry.get() == "0": self.price_entry.delete(0, 'end')
            self.price_entry.insert('end', key)

    def play_sound(self):
        if pygame.mixer.get_init():
            try: pygame.mixer.music.play()
            except: pass

    def add_to_cart(self):
        try:
            val = self.price_entry.get()
            parts = val.split('*')
            price = float(parts[0])
            qty = int(parts[1]) if len(parts) > 1 else 1
            if price > 0:
                self.cart.extend([price, qty, price*qty])
                self.update_cart_display()
                self.price_entry.delete(0, 'end'); self.price_entry.insert(0, "0")
        except: pass

    def removefromcart(self):
        sel = self.cart_listbox.curselection()
        if sel is not None:
            try:
                idx = int(sel)
                for _ in range(3): self.cart.pop(idx * 3)
                self.update_cart_display()
            except: pass

    def clearcart(self):
        self.cart = []
        self.update_cart_display()

    def update_cart_display(self):
        self.allitem_quantity = 0
        self.cart_listbox.delete(0, 'end')
        self.Sumprice = 0
        def fmt(v): return int(v) if float(v).is_integer() else v
        idx = 0
        for i in range(0, len(self.cart), 3):
            p, q, t = self.cart[i], self.cart[i+1], self.cart[i+2]
            self.Sumprice += t
            self.allitem_quantity += q
            self.cart_listbox.insert(idx, f"{idx+1})    {fmt(p)} ฿  x  {fmt(q)}  =  {fmt(t)} ฿")
            idx += 1
        self.lbl_total.configure(text=f"{self.allitem_quantity} ชิ้น \ {fmt(self.Sumprice)} ฿")

        if len(self.cart) > 0:
            self.btn_checkout.configure(state="normal")
            self.btn_clear.configure(state="normal")
            self.btn_remove.configure(state="normal")
        else:
            self.btn_checkout.configure(state="disabled")
            self.btn_clear.configure(state="disabled")
            self.btn_remove.configure(state="disabled")


    def Checkout(self):
        if not self.cart: return
        self.play_sound()
        
        try:
            printer_name = app.printer_combo.get()
        except:
            try: printer_name = win32print.GetDefaultPrinter()
            except: printer_name = None

        receipt_text = self.generate_receipt_text()
        
        # Pass the printer_name to the thread
        threading.Thread(target=self.run_checkout_thread, args=(receipt_text, self.Sumprice, self.employee, printer_name)).start()
        self.clearcart()

    def run_checkout_thread(self, text, price, emp, printer_name):
        self.print_receipt(text, printer_name)
        self.save_to_db(price, emp)

    def print_receipt(self, text_to_print, printer_name):
        try:
            fd, filename = tempfile.mkstemp(".txt")
            os.close(fd)
            
            with open(filename, "w", encoding='utf-8') as file:
                file.write(text_to_print)

            try:
                # Print 2 copies (Customer + Keep)
                for _ in range(2):
                    if printer_name:
                        win32api.ShellExecute(
                            0,
                            "print",
                            filename,
                            '/d:"%s"' % printer_name,
                            ".",
                            0
                        )
                    else:
                        # Fallback if no printer name found
                        win32api.ShellExecute(0, "print", filename, None, ".", 0)
            except Exception as e:
                app.show_notification(f"Printing Error: {e}")
                
        except Exception as e:
            app.show_notification(f"File handling error during print: {e}")

    def save_to_db(self, price, emp):
        try:
            bill = f"B{datetime.now().strftime('%y%m%d%H%M%S')}"
            cursor.execute("INSERT INTO sales (bill_number, sale_date, sale_time, price_sold, employee) VALUES (?,?,?,?,?)",
                           (bill, datetime.now().date(), datetime.now().time().strftime('%H:%M:%S'), price, emp))
            connection.commit()
        except: pass

    def generate_bill_number(self):
        timestamp = datetime.now().strftime('%y%m%d%H%M%S')
        return f'B{timestamp}'
    
    def generate_receipt_text(self):
        bill_number = self.generate_bill_number()
        sale_date = datetime.now().strftime('%d/%m/%Y')
        sale_time = datetime.now().time()
        billsale_time_str = sale_time.strftime('%H:%M')
        itemscart = self.cart
        self.allitem_quantity = 0
        
        def fmt(val):
            try:
                f_val = float(val)
                if f_val.is_integer():
                    return int(f_val)
                return f_val
            except:
                return val
        
        header = """
       {title:^31}
       {subtitle:^28}
       {address:^32}   
       {open_hours:^31}
        """.format(
            title="ร้านข้าวแต๋น",
            subtitle="ของฝากจากลำปาง",
            address="ตึกสีส้มทางเข้า HOP INN",
            open_hours="เปิด 8.00-21.00น. ทุกวัน"
        )

        middle = """
{left_text:<14}{right_text:>19}
{bill_number:<20}
        """.format(
            left_text=f"วันที่ {sale_date}",
            right_text=f"เวลา {billsale_time_str}",
            bill_number=f"เลขที่บิล: {bill_number}"
        )

        itemfirst = "\nรายการ:\n-------------------------------------------"

        items = ""
        for x in range(0, len(itemscart), 3):
            p_val = fmt(itemscart[x])
            q_val = fmt(itemscart[x+1])
            sum_val = fmt(itemscart[x+2])
            self.allitem_quantity += q_val

            items += """
ราคา    {item_info:<5} ฿    {item_quan:<3} ชิ้น  =>  {itemsumprice:>1} ฿
""".format(
                item_info=f" {p_val}",
                item_quan=f" {q_val}",
                itemsumprice=f" {sum_val}"
            )

        quan_item = """
สินค้า :    {item_quan:<5} รายการ   รวม  {allitemquan:>1} ชิ้น
""".format(
            item_quan=f" {int(len(itemscart)/3)}",
            allitemquan=f" {int(self.allitem_quantity)}"
        )

        itemlast = "\n-------------------------------------------\n"
        total_val = fmt(self.Sumprice)
        total = """            {total_label:>21} {total_amount:>10} 
        """.format(
            total_label="  รวม: ",
            total_amount=f"  {total_val}  ฿"
        )

        footer = """
          {thanks:^22}
          {tel_info:>22}
          
        """.format(
            thanks="ขอบคุณเจ้า",
            tel_info="โทร : 054-230189\n\n"
        )
        blank = "\n\n\n"

        receipt = f"{header}{middle}{itemfirst}{items}{quan_item}{itemlast}{total}{footer}{blank}"
        return receipt.encode('utf-8').decode('utf-8')

# ==============================================================================
# MAIN APP (The Manager)
# ==============================================================================
class MainApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Dual Station POS")
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight() - 50
        self.is_dual_mode = False 
        
        # --- 1. TOP BAR ---
        self.top_bar = ctk.CTkFrame(self.root, height=70, fg_color="#222")
        self.top_bar.pack(side="top", fill="x")
        
        self.btn_toggle = ctk.CTkButton(self.top_bar, text="Switch to DUAL Mode", 
                                        command=self.toggle_mode, fg_color="#6A0DAD")
        self.btn_toggle.pack(side="left", padx=10, pady=5)
        
        self.btn_history = ctk.CTkButton(self.top_bar, text="History", command=self.open_history)
        self.btn_history.pack(side="left", padx=10, pady=5)

        # --- PRINTER SELECTION (Add this to Top Bar) ---
        # 1. Scan for Printers
        printer_list = ["No Printers Found"]
        try:
            # PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            printers = win32print.EnumPrinters(flags)
            if printers:
                printer_list = [p[2] for p in printers]
        except Exception as e:
            app.show_notification(f"Printer Scan Error: {e}")

        # 2. Create ComboBox
        self.printer_combo = ctk.CTkComboBox(self.top_bar, values=printer_list, width=250, font=("Arial", 14))
        self.printer_combo.pack(side="left", padx=10, pady=5)

        # 3. Set Default Printer
        try:
            default_printer = win32print.GetDefaultPrinter()
            if default_printer in printer_list:
                self.printer_combo.set(default_printer)
            elif printer_list:
                self.printer_combo.set(printer_list[0])
        except:
            pass

        self.notification_var = ctk.StringVar(value="off")
        self.chk_notification = ctk.CTkCheckBox(
            self.top_bar, 
            text="Notification", 
            variable=self.notification_var, 
            onvalue="on", 
            offvalue="off",
            font=("Arial", 14)
        )
        self.chk_notification.pack(side="left", padx=10, pady=5)

        self.btn_exit = ctk.CTkButton(self.top_bar, text="Exit App", command=self.root.destroy, fg_color="red")
        self.btn_exit.pack(side="right", padx=10, pady=5)
        
        # --- 2. MAIN CONTAINER ---
        self.container = ctk.CTkFrame(self.root, fg_color="#333")
        self.container.pack(fill="both", expand=True)
        
        # --- 3. CREATE STATIONS ---
        self.pos_left = POSTerminal(self.container, station_id=1, fg_color="#2b2b2b")
        self.pos_right = POSTerminal(self.container, station_id=2, fg_color="#2b2b2b")
        self.divider = ctk.CTkFrame(self.container, width=5, fg_color="black")
        
        self.update_layout()

    def toggle_mode(self):
        self.is_dual_mode = not self.is_dual_mode
        if self.is_dual_mode:
            self.btn_toggle.configure(text="Switch to SINGLE Mode")
        else:
            self.btn_toggle.configure(text="Switch to DUAL Mode")
        self.update_layout()

    def show_notification(self, message):
        if self.notification_var.get() == "on":
            NotificationPopup(self.root, message)
        else:
            app.show_notification(f"[Log]: {message}")

    def update_layout(self):
        if self.is_dual_mode:
            total_width = self.screen_width * 2
            self.root.geometry(f"{total_width}x{self.screen_height}+0+0")
        else:
            self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
            
        self.root.overrideredirect(True) 

        if self.is_dual_mode:
            self.pos_left.pack(side="left", fill="both", expand=True)
            self.divider.pack(side="left", fill="y")
            self.pos_right.pack(side="left", fill="both", expand=True)
            
            self.pos_left.configure(width=self.screen_width)
            self.pos_right.configure(width=self.screen_width)
            self.pos_left.pack_propagate(False)
            self.pos_right.pack_propagate(False)
        else:
            self.pos_right.pack_forget()
            self.divider.pack_forget()
            self.pos_left.pack(side="left", fill="both", expand=True)
            self.pos_left.pack_propagate(True)

    def open_history(self):
        target = "GUISale.py"
        if os.path.exists(target):
            subprocess.run(['python', target])
        else:
            app.show_notification("History file not found.")

if __name__ == "__main__":
    app = MainApp()
    app.root.mainloop()
