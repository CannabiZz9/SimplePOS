import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime
import tempfile

# Third-party libraries
import customtkinter as ctk
from CTkListbox import *
import pygame

# --- FIX FOR WINDOWS SCALING (Prevents cropping at 125%/150%) ---
try:
    from ctypes import windll
    # This tells Windows: "I am DPI aware, don't scale me!"
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass
# ---------------------------------------------------------------

# Windows specific imports
try:
    import win32api
    import win32print
except ImportError:
    print("Warning: win32 libraries not found. Printing will not work.")

# --- Configuration ---
ctk.set_appearance_mode('dark')
ctk.set_default_color_theme("blue")
# Reset widget scaling to default (let the DPI awareness handle the resolution)
ctk.set_widget_scaling(1.0)

def resource_path(relative_path):
# ... (rest of the resource_path function is unchanged)
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Database Setup ---
# ... (rest of the file is unchanged)
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

class ShoppingCartApp:
# ... (rest of the class is unchanged)
    def __init__(self, is_secondary=False):
        self.is_secondary = is_secondary
        self.histrywindow = None
        
        # --- Window Setup ---
        if self.is_secondary:
            self.window = ctk.CTkToplevel()
            self.window.title("Shopping Cart (Window 2)")
            
            # --- DUAL MONITOR LOGIC ---
            # Get the width of the primary screen
            screen_width = self.window.winfo_screenwidth()
            
            # Set the position of the new window to start where the first screen ends
            self.window.geometry(f"1000x800+{screen_width}+0")
            
            self.window.attributes('-fullscreen', False)
        else:
            self.window = ctk.CTk()
            self.window.title("Shopping Cart")
            self.window.attributes('-fullscreen', True)
        
        # Screen dimensions
        self.screen_width = self.window.winfo_screenwidth()
        self.screen_height = self.window.winfo_screenheight()
        
        # Variables
        self.cart = []
        self.current_price = 0
        self.Sumprice = 0
        self.allitem_quantity = 0
        self.employee = "Default"
        
        # Reference to keep secondary window alive
        self.second_app_instance = None 

        self.create_widgets()
    
    def PlusWindow(self):
        """Opens the secondary window."""
        self.play_sound()
        if self.second_app_instance is None or not self.second_app_instance.window.winfo_exists():
            self.second_app_instance = ShoppingCartApp(is_secondary=True)
            self.second_app_instance.window.lift()
        else:
            self.second_app_instance.window.lift()

    def append_to_price_entry(self, value):
        current_text = self.price_entry.get()
        if current_text == "0" or current_text == "":
            current_text = ""
        self.price_entry.delete(0, "end")
        self.price_entry.insert(0, current_text + str(value))
        self.play_sound()

    def clear_price_entry(self):
        self.price_entry.delete(0, "end")
        self.price_entry.insert(0, "0")
        self.play_sound()
        
    def add_to_cart(self):
        self.play_sound()
        self.item_quantity = 1
        input_string = self.price_entry.get()
        parts = input_string.split('*')

        try:
            self.item_price = float(parts[0])
            self.item_quantity = int(parts[1]) if len(parts) > 1 else 1
        except (ValueError, IndexError):
            self.item_price = 0
            self.item_quantity = 1
            
        self.item_overall_price = (self.item_price * self.item_quantity)
        
        if self.item_price != 0:
            self.cart.append(self.item_price)
            self.cart.append(self.item_quantity) 
            self.cart.append(self.item_overall_price)
            self.current_price = 0
            self.price_entry.delete(0, "end")
            self.price_entry.insert(0, "0")
            self.updateCart()
    
    def removefromcart(self):
        self.index = self.cart_listbox.curselection()
        if self.index is not None and self.index != (): 
            try:
                idx = int(self.index)
                self.cart.pop(idx * 3)
                self.cart.pop(idx * 3)
                self.cart.pop(idx * 3)
                self.updateCart()
            except Exception as e:
                print(f"Error removing item: {e}")
        else:
            print("\nDidn't select anything to remove")
        self.play_sound()
    
    def clearcart(self):
        self.cart = []
        self.updateCart()
        self.play_sound()
    
    def updateCart(self):
        self.cart_listbox.delete(0,'end')
        self.Sumprice = 0
        self.allitem_quantity = 0
        
        # Helper to remove decimal if it's .0
        def fmt(val):
            return int(val) if float(val).is_integer() else val

        display_index = 0
        for x in range(0, len(self.cart), 3):
            self.item_name = f"{display_index + 1})"
            
            # Apply formatting here for display
            self.item_price = fmt(self.cart[x])
            self.item_quantity = fmt(self.cart[x+1])
            self.item_overall_price = fmt(self.cart[x+2])
            
            self.allitem_quantity += self.cart[x+1] # Keep raw math on the float value
            self.Sumprice += self.cart[x+2]         # Keep raw math on the float value
            
            display_text = f"{self.item_name}  {self.item_price}฿  {self.item_quantity} ชิ้น --> {self.item_overall_price}฿"
            self.cart_listbox.insert(display_index, display_text)
            display_index += 1
            
        self.total_label.configure(text=f"Total: {fmt(self.Sumprice)}฿")
        self.totalquantity_label.configure(self.total_frame, text=f"จำนวนทั้งหมด : {int(self.allitem_quantity)} ชิ้น")
        self.check_cart()
        
    def delete_last_digit(self):
        current_text = self.price_entry.get()
        if len(current_text) > 0:
            self.price_entry.delete(len(current_text)-1, 'end')
        self.play_sound()    

    def generate_receipt(self):
        bill_number = self.generate_bill_number()
        sale_date = datetime.now().strftime('%d/%m/%Y')
        sale_time = datetime.now().time()
        billsale_time_str = sale_time.strftime('%H:%M')
        itemscart = self.cart
        
        # --- NEW HELPER FUNCTION ---
        def fmt(val):
            """Returns int if value is whole number, else returns float"""
            try:
                f_val = float(val)
                if f_val.is_integer():
                    return int(f_val)
                return f_val
            except:
                return val
        # ---------------------------
        
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
            # Apply the formatting logic here
            p_val = fmt(itemscart[x])
            q_val = fmt(itemscart[x+1])
            sum_val = fmt(itemscart[x+2])

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
            allitemquan=f" {int(self.allitem_quantity)}" # Force int for total quantity
        )

        itemlast = "\n-------------------------------------------\n"

        # Apply formatting to the total price
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

    def print_receipt(self, text_to_print):
        try:
            fd, filename = tempfile.mkstemp(".txt")
            os.close(fd)
            
            with open(filename, "w", encoding='utf-8') as file:
                file.write(text_to_print)

            # Find Printer
            printer_name = win32print.GetDefaultPrinter()
            if not printer_name:
                printers = win32print.EnumPrinters(2 | 4) # Local | Network
                if printers: printer_name = printers[0][2]

            if printer_name:
                try:
                    # --- LOOP IS HERE ---
                    for _ in range(2): 
                        win32api.ShellExecute(
                            0,
                            "printto",
                            filename,
                            f'"{printer_name}"',
                            ".",
                            0
                        )
                except Exception as e:
                    print(f"Printing Error: {e}")
            else:
                print("No printer found.")
                
        except Exception as e:
            print(f"File error: {e}")

    def Checkout(self):
        self.play_sound()
        text_to_print = self.generate_receipt()
        self.print_receipt(text_to_print)
        # -------------------------------
        
        self.add_sale(self.Sumprice, self.employee)
        self.clearcart()
        
    def generate_bill_number(self):
        timestamp = datetime.now().strftime('%y%m%d%H%M%S')
        return f'B{timestamp}'
    
    def add_sale(self, price, employee):
        try:
            bill_number = self.generate_bill_number()
            sale_date = datetime.now().date()
            sale_time = datetime.now().time()
            sale_time_str = sale_time.strftime('%H:%M:%S')
            cursor.execute('''
                INSERT INTO sales (bill_number, sale_date, sale_time, price_sold, employee)
                VALUES (?, ?, ?, ?, ?)
            ''', (bill_number, sale_date, sale_time_str, price, employee))
            connection.commit()
        except Exception as e:
            print(f"Database Error: {e}")
    
    def check_cart(self):
        if len(self.cart) > 0:
            self.Print.configure(state=ctk.NORMAL)
            self.clearcart_Button.configure(state=ctk.NORMAL)
            self.RemoveButton.configure(state=ctk.NORMAL)
        else:
            self.Print.configure(state=ctk.DISABLED)
            self.clearcart_Button.configure(state=ctk.DISABLED)
            self.RemoveButton.configure(state=ctk.DISABLED)
            
    def go2history(self):
        self.play_sound()
        possible_paths = [
            r"C:\Users\POS\Desktop\Program\Program\GUISale.py",
            r"D:\Work\SimplePOS2\RealUse\SimplePOS\GUISale.py",
            "GUISale.py"
        ]
        
        found_path = None
        for path in possible_paths:
            if os.path.exists(path):
                found_path = path
                break
        
        if found_path:
            try:
                subprocess.run(['python', found_path])
            except Exception as e:
                print(f"Could not open history: {e}")
        else:
            print("History file 'GUISale.py' not found.")
        
    def play_sound(self):
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.play()
            except Exception:
                pass
    
    def koon(self, value):
        self.play_sound()
        self.price_entry.insert('end', value)
        
    def create_widgets(self):
        # Initialize Sound
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                pygame.mixer.music.load(r"C:\Users\POS\Desktop\Program\SimplePOS\s.mp3") 
            except Exception as e:
                print(f"Sound init failed (continuing without sound): {e}")

        # --- CALCULATOR SECTION ---
        self.calculator_frame = ctk.CTkFrame(self.window)
        self.calculator_frame.grid(row=1, column=2, columnspan=4, padx=40, pady=5)
        
        self.price_label = ctk.CTkLabel(self.window, text="Price:", font=("Arial", 27))
        self.price_label.grid(row=0, column=2, padx=10, pady=50)
        
        self.price_entry = ctk.CTkEntry(self.window, width=250, height=35, font=("Arial", 27))
        self.price_entry.insert(0, "0") 
        self.price_entry.grid(row=0, column=3, padx=10, pady=50)

        # Calculator Buttons
        self.calculator_buttons = {}
        for i in range(9):
            btn_txt = str(i+1)
            button = ctk.CTkButton(self.calculator_frame, text=btn_txt, 
                                   command=lambda x=btn_txt: self.append_to_price_entry(x),
                                   font=("Arial", 27))
            button.grid(row=(2 - i // 3), column=(i % 3), padx=10, pady=10, ipady=40)
            self.calculator_buttons[btn_txt] = button
            
        self.zero_button = ctk.CTkButton(self.calculator_frame, text="0", 
                                         command=lambda: self.append_to_price_entry(0),
                                         font=("Arial", 27))
        self.zero_button.grid(row=3, column=0, padx=10, pady=10, columnspan=2, ipadx=95, ipady=40)
        
        self.dot_button = ctk.CTkButton(self.calculator_frame, text=".", 
                                        command=lambda: self.append_to_price_entry("."),
                                        font=("Arial", 27))
        self.dot_button.grid(row=3, column=2, padx=10, pady=10, ipady=40)
        
        self.clear_button = ctk.CTkButton(self.calculator_frame, text=" C ", 
                                          command=self.clear_price_entry,
                                          font=("Arial", 27), fg_color="red")
        self.clear_button.grid(row=0, column=3, padx=10, pady=10, ipady=40)
        
        self.koon_button = ctk.CTkButton(self.calculator_frame, text=" x ", 
                                         command=lambda: self.koon('*'),
                                         font=("Arial", 27), fg_color="blue")
        self.koon_button.grid(row=2, column=3, padx=10, pady=10, ipady=40)
        
        self.del1_button = ctk.CTkButton(self.calculator_frame, text="<--", 
                                         command=self.delete_last_digit,
                                         font=("Arial", 27), fg_color="#FC6736")
        self.del1_button.grid(row=1, column=3, padx=10, pady=10, ipady=40)
        
        self.add_to_cart_button = ctk.CTkButton(self.calculator_frame, text="add", 
                                                command=self.add_to_cart,
                                                font=("Arial", 27), fg_color="green")
        self.add_to_cart_button.grid(row=3, column=3, padx=10, pady=10, ipady=40)
        
        # --- CART SECTION ---
        self.cart_frame = ctk.CTkFrame(self.window)
        self.cart_frame.grid(row=1, column=6, columnspan=3, padx=35, pady=0)
        
        self.buttoncart_frame = ctk.CTkFrame(self.cart_frame)
        self.buttoncart_frame.grid(row=0, column=4, columnspan=2, padx=35, pady=0)
        
        self.cart_label = ctk.CTkLabel(self.cart_frame, text="Cart: ", font=("Arial", 27))
        self.cart_label.grid(row=0, column=0, columnspan=1, padx=10, pady=10)
        
        self.cart_listbox = CTkListbox(self.cart_frame, height=400, width=275, font=("Angsana New", 39))
        self.cart_listbox.grid(row=0, column=1, columnspan=2, padx=10, pady=10)
        
        self.RemoveButton = ctk.CTkButton(self.buttoncart_frame, text="Remove", 
                                          command=self.removefromcart,
                                          font=("Arial", 30), state=ctk.DISABLED)
        self.RemoveButton.grid(row=0, column=0, padx=10, pady=20, ipady=20)
        
        self.clearcart_Button = ctk.CTkButton(self.buttoncart_frame, text="Clear", 
                                              command=self.clearcart,
                                              font=("Arial", 30), state=ctk.DISABLED)
        self.clearcart_Button.grid(row=1, column=0, padx=10, pady=20, ipady=20)

        # --- TOTAL & PRINT SECTION ---
        self.total_frame = ctk.CTkFrame(self.window)
        self.total_frame.grid(row=2, column=5, columnspan=4, padx=10, pady=10)
        
        self.total_label = ctk.CTkLabel(self.total_frame, text=f"Total: {self.Sumprice}฿", font=("Arial", 40))
        self.total_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.totalquantity_label = ctk.CTkLabel(self.total_frame, 
                                                text=f"จำนวนทั้งหมด : {int(self.allitem_quantity)} ชิ้น",
                                                font=("Arial", 27))
        self.totalquantity_label.grid(row=1, column=0, padx=10, pady=10)
        
        self.Print = ctk.CTkButton(self.total_frame, text="Print", 
                                   command=self.Checkout, 
                                   font=("Arial", 27), state=ctk.DISABLED)
        self.Print.grid(row=2, column=0, padx=10, pady=30, ipady=30)
        
        # --- NAVIGATION BUTTONS ---
        self.histry_button = ctk.CTkButton(self.window, text="History", 
                                           command=self.go2history,
                                           font=("Arial", 30))
        self.histry_button.grid(row=0, column=7, padx=10, pady=50, columnspan=1, ipadx=55)

        self.plus_window_btn = ctk.CTkButton(self.window, text="+Window", 
                                             command=self.PlusWindow, 
                                             font=("Arial", 30), fg_color="#6A0DAD")
        self.plus_window_btn.grid(row=0, column=8, padx=10, pady=50, columnspan=1, ipadx=20)

        self.Exit = ctk.CTkButton(self.window, text="Exit", 
                                  command=self.window.destroy,
                                  font=("Arial", 30))
        self.Exit.grid(row=0, column=9, padx=10, pady=50, columnspan=1, sticky='e')


if __name__ == "__main__":
    ShopApp = ShoppingCartApp(is_secondary=False)
    ShopApp.window.mainloop()
