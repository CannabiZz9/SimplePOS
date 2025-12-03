import os
import subprocess
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from CTkListbox import *
import sqlite3
from datetime import datetime
import tempfile
import win32api
import win32print
import sys
import pygame

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode('dark')

connection = sqlite3.connect('sales_history.db', check_same_thread=False) 
# Added check_same_thread=False to prevent issues with multiple windows accessing DB
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
    def __init__(self, is_secondary=False):
        # Logic to decide if this is the Main Window or a Second Screen
        self.is_secondary = is_secondary
        
        if self.is_secondary:
            self.window = ctk.CTkToplevel() # Create a secondary window
            self.window.title("Shopping Cart (Window 2)")
        else:
            self.window = ctk.CTk() # Create the main root window
            self.window.title("Shopping Cart")
            
        self.histrywindow = None # Initialize as None, created only when needed
        
        if self.is_secondary:
            self.window = ctk.CTkToplevel() # Create a secondary window
            self.window.title("Shopping Cart (Window 2)")
            self.window.attributes('-fullscreen', False)
            
        else:
            self.window = ctk.CTk() # Create the main root window
            self.window.title("Shopping Cart")
            
            # --- CHANGE 2: KEEP FULLSCREEN FOR PRIMARY WINDOW ---
            self.window.attributes('-fullscreen', True) 
        
        # Determine screen dimensions (still useful if you want to place windows precisely later)
        width = self.window.winfo_screenwidth()               
        height = self.window.winfo_screenheight()
        
        self.cart = []
        self.current_price = 0
        self.Sumprice = 0
        self.allitem_quantity = 0
        self.employee = "Default"
        
        # We need to keep a reference to the second window object so it isn't garbage collected
        self.second_app_instance = None 

        self.create_widgets()
    
    def PlusWindow(self):
        self.play_sound()
        # Create a new instance of the class, but tell it it is a secondary window
        # We assign it to self.second_app_instance to keep it alive in memory
        self.second_app_instance = ShoppingCartApp(is_secondary=True)
        
        # Optional: If you want to force it to a specific monitor, you would need
        # to calculate geometry here (e.g., self.second_app_instance.window.geometry("+1920+0"))
        # For now, it opens fullscreen on top, and can be moved/managed by the OS.

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
            self.item_quantity = int(parts[1])
        except (ValueError, IndexError):
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
            self.cart.pop(self.index * 3)
            self.cart.pop(self.index * 3)
            self.cart.pop(self.index * 3)
            self.updateCart()
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
        self.allitem_quantity =0
        for x in range(0, int((len(self.cart))), 3):
            self.item_name = f"{int((x/3)+1)})"
            self.item_price = self.cart[(x)]
            self.item_quantity = self.cart[(x+1)]
            self.allitem_quantity += self.cart[(x+1)]
            self.item_overall_price = self.cart[(x+2)]
            self.cart_listbox.insert(x,f"{self.item_name}  {self.item_price}฿  {self.item_quantity} ชิ้น --> {self.item_overall_price}฿")
            self.Sumprice += self.item_overall_price
        self.total_label.configure(text=f"Total: {self.Sumprice}฿")
        self.totalquantity_label.configure(self.total_frame, text=f"จำนวนทั้งหมด : {int(self.allitem_quantity)} ชิ้น")
        self.check_cart()
        
    def delete_last_digit(self):
        current_text = self.price_entry.get()
        if len(current_text) > 0:
            self.price_entry.delete(len(self.price_entry.get())-1, 'end')
        self.play_sound()    

    def generate_receipt(self):
        bill_number = self.generate_bill_number()
        sale_date = datetime.now().strftime('%d/%m/%Y')
        sale_time = datetime.now().time()
        billsale_time_str = sale_time.strftime('%H:%M')
        itemscart = self.cart
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

        itemfirst = """
รายการ:
-------------------------------------------"""

        items = ""
        for x in range(0, int((len(itemscart))), 3):
            items += """
ราคา    {item_info:<5} ฿    {item_quan:<3} ชิ้น  =>  {itemsumprice:>1} ฿
""".format(
            item_info=f" {itemscart[x]}",
            item_quan=f" {itemscart[x+1]}",
            itemsumprice=f" {itemscart[x+2]}"
        )

        quan_item = """
สินค้า :    {item_quan:<5} รายการ   รวม  {allitemquan:>1} ชิ้น
""".format(
            item_quan=f" {int((len(itemscart))/3)}",
            allitemquan=f" {self.allitem_quantity}"
        )

        itemlast = """
-------------------------------------------

"""

        total = """            {total_label:>21} {total_amount:>10} 
        """.format(
        total_label="  รวม: ",
        total_amount=f"  {self.Sumprice}  ฿"
        )

        footer = """
          {thanks:^22}
          {tel_info:>22}
          
        """.format(
        thanks="ขอบคุณเจ้า",
        tel_info="""โทร : 054-230189\n\n
        """
        )
        blank = """
          
          
          
        """

        receipt = f"{header}{middle}{itemfirst}{items}{quan_item}{itemlast}{total}{footer}{blank}"
        return receipt.encode('utf-8').decode('utf-8')     

    def print_receipt(self,text_to_print):
        with open(tempfile.mktemp(".txt"), "w", encoding='utf-8') as file:
            file.write(text_to_print)

        filename = tempfile.mktemp(".txt")
        open(filename, "w", encoding='utf-8').write(text_to_print)

        # Added try-except to prevent crash if no printer is found
        try:
            for _ in range(2): 
                win32api.ShellExecute(
                    0,
                    "print",
                    filename,
                    '/d:"%s"' % win32print.GetDefaultPrinter(),
                    ".",
                    0
            )
        except Exception as e:
            print(f"Printer error: {e}")

    def Checkout(self):
        self.play_sound()
        text_to_print = self.generate_receipt()
        self.print_receipt(text_to_print)
        self.add_sale(self.Sumprice,self.employee)
        self.clearcart()
        
    def generate_bill_number(self):
        timestamp = datetime.now().strftime('%y%m%d%H%M%S')
        return f'B{timestamp}'
    
    def add_sale(self, price, employee):
        bill_number = self.generate_bill_number()
        sale_date = datetime.now().date()
        sale_time = datetime.now().time()
        sale_time_str = sale_time.strftime('%H:%M:%S')
        cursor.execute('''
            INSERT INTO sales (bill_number, sale_date, sale_time, price_sold, employee)
            VALUES (?, ?, ?, ?, ?)
        ''', (bill_number, sale_date, sale_time_str, price, employee))
        connection.commit()
    
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
        self.path2py = r"C:\Users\POS\Desktop\Program\Program\GUISale.py"
        #self.path2py = r"D:\Work\SimplePOS2\RealUse\SimplePOS\GUISale.py"
        try:
            subprocess.run(['python', resource_path(self.path2py)])
        except Exception as e:
            print(f"Could not open history: {e}")
        
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
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            try:
                # Use raw string or check if file exists to prevent errors
                pygame.mixer.music.load(r"D:\Work\SimplePOS2\RealUse\SimplePOS\s.mp3")
            except:
                pass # Fail silently if sound file missing

        # Create price entry widget
        self.calculator_frame = ctk.CTkFrame(self.window)
        self.calculator_frame.grid(row=1, column=2, columnspan=4, padx=40, pady=5)
        self.price_label = ctk.CTkLabel(self.window, text="Price:",font=("Arial", 27))
        self.price_label.grid(row=0, column=2, padx=10, pady=50)
        self.price_entry = ctk.CTkEntry(self.window, width=250, height=35,font=("Arial", 27))
        self.price_entry.insert(0, "0") 
        self.price_entry.grid(row=0, column=3, padx=10, pady=50)

        # Create calculator buttons
        self.calculator_buttons = {}
        for i in range(9):
            button = ctk.CTkButton(self.calculator_frame, text=str(i+1), command=lambda i=i: self.append_to_price_entry(i+1),font=("Arial", 27))
            button.grid(row=(2 - i // 3), column=(i % 3), padx=10, pady=10,ipady=40)
            self.calculator_buttons[str(i+1)] = button
        self.zero_button = ctk.CTkButton(self.calculator_frame, text="0", command=lambda: self.append_to_price_entry(0),font=("Arial", 27))
        self.zero_button.grid(row=3, column=0, padx=10, pady=10,columnspan=2,ipadx=95,ipady=40)
        self.calculator_buttons[0] = self.zero_button
        self.dot_button = ctk.CTkButton(self.calculator_frame, text=".", command=lambda: self.append_to_price_entry("."),font=("Arial", 27))
        self.dot_button.grid(row=3, column=2, padx=10, pady=10,ipady=40)
        self.calculator_buttons["."] = self.dot_button
        self.clear_button = ctk.CTkButton(self.calculator_frame, text=" C ", command=self.clear_price_entry,font=("Arial", 27), fg_color="red")
        self.clear_button.grid(row=0, column=3, padx=10, pady=10,ipady=40)
        self.koon_button = ctk.CTkButton(self.calculator_frame, text=" x ", command=lambda: self.koon('*'),font=("Arial", 27), fg_color="blue")
        self.koon_button.grid(row=2, column=3, padx=10, pady=10,ipady=40)
        self.del1_button = ctk.CTkButton(self.calculator_frame, text="<--", command=self.delete_last_digit,font=("Arial", 27), fg_color="#FC6736")
        self.del1_button.grid(row=1, column=3, padx=10, pady=10,ipady=40)
        self.add_to_cart_button = ctk.CTkButton(self.calculator_frame, text="add", command=self.add_to_cart,font=("Arial", 27), fg_color="green")
        self.add_to_cart_button.grid(row=3, column=3, padx=10, pady=10,ipady=40)
        

        # Create cart listbox
        self.cart_frame = ctk.CTkFrame(self.window)
        self.cart_frame.grid(row=1, column=6, columnspan=3, padx=35, pady=0)
        self.buttoncart_frame = ctk.CTkFrame(self.cart_frame)
        self.buttoncart_frame.grid(row=0, column=4, columnspan=2, padx=35, pady=0)
        self.cart_label = ctk.CTkLabel(self.cart_frame, text="Cart: ",font=("Arial", 27))
        self.cart_label.grid(row=0, column=0 ,columnspan=1, padx=10, pady=10)
        self.cart_listbox = CTkListbox(self.cart_frame, height=400,width=275,font=("Angsana New",39))
        self.cart_listbox.grid(row=0, column=1, columnspan=2, padx=10, pady=10)
        self.RemoveButton = ctk.CTkButton(self.buttoncart_frame, text="Remove From Cart",command=self.removefromcart,font=("Arial", 30), state=ctk.DISABLED)
        self.RemoveButton.grid(row=0, column=0, padx=10, pady=20, ipady=20)
        self.clearcart_Button = ctk.CTkButton(self.buttoncart_frame, text="Clear Cart",command=self.clearcart,font=("Arial", 30), state=ctk.DISABLED)
        self.clearcart_Button.grid(row=1, column=0, padx=10, pady=20, ipady=20)

        # Create total label
        self.total_frame = ctk.CTkFrame(self.window)
        self.total_frame.grid(row=2, column=5, columnspan=4, padx=10, pady=10)
        self.total_label = ctk.CTkLabel(self.total_frame, text=f"Total: {self.Sumprice}฿",font=("Arial", 40))
        self.total_label.grid(row=0, column=0, padx=10, pady=10)
        self.totalquantity_label = ctk.CTkLabel(self.total_frame, text=f"จำนวนทั้งหมด : {int(self.allitem_quantity)} ชิ้น",font=("Arial", 27))
        self.totalquantity_label.grid(row=1, column=0, padx=10, pady=10)
        self.Print = ctk.CTkButton(self.total_frame, text="Print", command=self.Checkout ,font=("Arial", 27), state=ctk.DISABLED)
        self.Print.grid(row=2, column=0, padx=10, pady=30, ipady=30)
        
        # --- TOP BUTTONS (History, PlusWindow, Exit) ---
        
        # 1. Sale History Button (Row 0, Col 7)
        self.histry_button = ctk.CTkButton(self.window, text="Sale History", command=self.go2history,font=("Arial", 30))
        self.histry_button.grid(row=0, column=7, padx=10, pady=50, columnspan=1, ipadx=55)

        # 2. NEW BUTTON: +Window (Row 0, Col 8)
        # Note: Only show this on the Main window to avoid infinite windows from sub-windows? 
        # (Optional, but here we render it on all)
        self.plus_window_btn = ctk.CTkButton(self.window, text="+Window", command=self.PlusWindow, font=("Arial", 30), fg_color="#6A0DAD")
        self.plus_window_btn.grid(row=0, column=8, padx=10, pady=50, columnspan=1, ipadx=20)

        # 3. Exit Button (Moved to Row 0, Col 9)
        self.Exit = ctk.CTkButton(self.window, text="Exit", command=self.window.destroy, font=("Arial", 30))
        # Note: changed command from self.window.quit to self.window.destroy for cleaner closing of specific window
        self.Exit.grid(row=0, column=9, padx=10, pady=50, columnspan=1, sticky='e')
        
        # IMPORTANT: Removed self.window.mainloop() from here!

# Create the main application instance
ShopApp = ShoppingCartApp(is_secondary=False)

# Start the main event loop
ShopApp.window.mainloop()
