import os
import subprocess
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from CTkListbox import *
import sys
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


ctk.set_appearance_mode('dark')

connection = sqlite3.connect('sales_history.db')
cursor = connection.cursor()

# Create a sales history table with additional fields
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
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Shopping Cart")
        self.histrywindow = ctk.CTk()
        self.histrywindow.title("Sale History")
        self.window.attributes('-fullscreen', True)
        self.window._state_before_windows_set_titlebar_color = 'zoomed'
        width= self.window.winfo_screenwidth()               
        height= self.window.winfo_screenheight()  
        #width= 1000               
        #height= 700             
        #self.window.geometry("%dx%d" % (width+200, height+200))
        #self.histrywindow.geometry("%dx%d" % (width, height))
        
        self.cart = []

        self.current_quantity = 1
        self.current_price = 0
        self.Sumprice = 0
        self.allitem_quantity =0
        self.employee = "Defualt"
        self.create_widgets()
    
    def append_to_price_entry(self, value):
        current_text = self.price_entry.get()
        if current_text == "0" or current_text == "":
            current_text = ""
        self.price_entry.delete(0, "end")
        self.price_entry.insert(0, current_text + str(value))

    def clear_price_entry(self):
        self.price_entry.delete(0, "end")
        self.price_entry.insert(0, "0")

    def decrement_quantity(self):
        if self.current_quantity > 1:
            self.current_quantity -= 1
            self.quantity_label.configure(text=f"Quantity: {self.current_quantity}")

    def increment_quantity(self):
        self.current_quantity += 1
        self.quantity_label.configure(text=f"Quantity: {self.current_quantity}")

    def decrement5_quantity(self):
        if self.current_quantity > 5:
            self.current_quantity -= 5
            self.quantity_label.configure(text=f"Quantity: {self.current_quantity}")

    def increment5_quantity(self):
        self.current_quantity += 5
        self.quantity_label.configure(text=f"Quantity: {self.current_quantity}")
        
    def add_to_cart(self):
        self.item_price = float(self.price_entry.get())
        self.item_quantity = self.current_quantity
        self.item_overall_price = (self.item_price * self.item_quantity)
        if self.item_price != 0:
            self.cart.append(self.item_price)
            self.cart.append(self.item_quantity) 
            self.cart.append(self.item_overall_price)
            self.current_quantity = 1
            self.quantity_label.configure(text=f"Quantity: {self.current_quantity}")
            self.current_price = 0
            self.price_entry.delete(0, "end")
            self.price_entry.insert(0, "0")
            self.updateCart()
    
    def removefromcart(self):
        self.index = self.cart_listbox.curselection()
        self.cart.pop(self.index*3)
        self.cart.pop(self.index*3)
        self.cart.pop(self.index*3)
        self.updateCart()
    
    def updateCart(self):
        self.cart_listbox.delete(0,'end')
        self.Sumprice = 0
        self.allitem_quantity =0
        for x in range(0, int((len(self.cart))), 3):
            self.item_name = f"Item {int((x/3)+1)}"
            self.item_price = self.cart[(x)]
            self.item_quantity = self.cart[(x+1)]
            self.allitem_quantity += self.cart[(x+1)]
            self.item_overall_price = self.cart[(x+2)]
            self.cart_listbox.insert(x,f"{self.item_name}  {self.item_price}฿  @{self.item_quantity} ชิ้น -->  {self.item_overall_price} ฿")
            self.Sumprice += self.item_overall_price
        self.total_label.configure(text=f"Total: {self.Sumprice}฿")
        self.totalquantity_label.configure(self.total_frame, text=f"จำนวนทั้งหมด : {int(self.allitem_quantity)} ชิ้น",font=("Arial", 27))
        
        
    def generate_receipt(self):
        items = self.cart
        receipt = f"************ Receipt ************\n"
        for x in range(0, int((len(items))), 3):
            receipt += f"Item{int((x/3)+1)} : {items[x]} Bath x @{items[x+1]}  --> {items[x+2]} Bath"
            receipt += f"\n"
        
        receipt += f"\nTotal: {self.Sumprice}"

        receipt += f"\n*********************************\n"
        print(receipt.encode('utf-8').decode('utf-8'))
        self.add_sale(self.Sumprice, self.employee)
        return receipt

    

    #def print_receipt(self):
        # Connect to the USB thermal printer (you might need to change the USB address)
        printer = Usb(0x0416, 0x5011, 0)
        # Set font size and style (optional)
        printer.set(align='center', font='b', text_type='normal', width=1, height=1)
        # Set Printer Text
        receipt_text = self.generate_receipt(self.cart)
        receipt_text = receipt_text.encode('utf-8').decode('utf-8')
        printer.text(receipt_text)
        printer.cut()
        printer.close()
        
    def generate_bill_number(self):
        # Generate a unique bill number using a timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
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

        # Commit the changes
        connection.commit()
    
    def go2history(self):
        #self.create_histry_widgets()
        #self.histrywindow.mainloop()
        self.path2py = r"D:\Work\SimplePOS2\RealUse\SimplePOS\GUISale.py"
        subprocess.run(['python', resource_path(self.path2py)])
        #os.startfile("C:\Program Files (x86)\SimplePOS\History\History.exe")
        
    
    def create_widgets(self):
        # Create price entry widget
        self.calculator_frame = ctk.CTkFrame(self.window)
        self.calculator_frame.grid(row=1, column=2, columnspan=4, padx=50, pady=5)
        self.price_label = ctk.CTkLabel(self.window, text="Price:",font=("Arial", 25))
        self.price_label.grid(row=0, column=2, padx=10, pady=5)
        self.price_entry = ctk.CTkEntry(self.window, width=150, height=20,font=("Arial", 25))
        self.price_entry.insert(0, "0")
        self.price_entry.grid(row=0, column=3, padx=10, pady=5)

        # Create calculator buttons
        self.calculator_buttons = {}
        for i in range(9):
            button = ctk.CTkButton(self.calculator_frame, text=str(i+1), command=lambda i=i: self.append_to_price_entry(i+1),font=("Arial", 25))
            button.grid(row=(2 - i // 3), column=(i % 3), padx=10, pady=10,ipady=25)
            self.calculator_buttons[str(i+1)] = button
        self.zero_button = ctk.CTkButton(self.calculator_frame, text="0", command=lambda: self.append_to_price_entry(0),font=("Arial", 25))
        self.zero_button.grid(row=3, column=0, padx=10, pady=10,columnspan=2,ipadx=95,ipady=25)
        self.calculator_buttons[0] = self.zero_button
        self.dot_button = ctk.CTkButton(self.calculator_frame, text=".", command=lambda: self.append_to_price_entry("."),font=("Arial", 25))
        self.dot_button.grid(row=3, column=2, padx=10, pady=10,ipady=25)
        self.calculator_buttons["."] = self.dot_button
        self.clear_button = ctk.CTkButton(self.calculator_frame, text="C", command=self.clear_price_entry,font=("Arial", 25))
        self.clear_button.grid(row=3, column=3, padx=10, pady=10,ipady=25)
        
        # Create quantity buttons
        self.quantity_frame = ctk.CTkFrame(self.window)
        self.quantity_frame.grid(row=1, column=6, columnspan=2, padx=20, pady=15)
        self.quantity_left_button = ctk.CTkButton(self.quantity_frame, text="-5", command=self.decrement5_quantity,font=("Arial", 20))
        self.quantity_left_button.grid(row=4, column=0, padx=5, pady=5,ipady=25)
        self.quantity_left_button = ctk.CTkButton(self.quantity_frame, text="-1", command=self.decrement_quantity,font=("Arial", 20))
        self.quantity_left_button.grid(row=3, column=0, padx=5, pady=5,ipady=25)
        self.quantity_label = ctk.CTkLabel(self.quantity_frame, text=f"Quantity: {self.current_quantity}",font=("Arial", 25))
        self.quantity_label.grid(row=2, column=0, padx=5, pady=5)
        self.quantity_right_button = ctk.CTkButton(self.quantity_frame, text="+1", command=self.increment_quantity,font=("Arial", 20))
        self.quantity_right_button.grid(row=1, column=0, padx=5, pady=5,ipady=25)
        self.quantity_right_button = ctk.CTkButton(self.quantity_frame, text="+5", command=self.increment5_quantity,font=("Arial", 20))
        self.quantity_right_button.grid(row=0, column=0, padx=5, pady=5,ipady=25)

        # Create add to cart button
        self.add_button = ctk.CTkButton(self.quantity_frame, text="Add to Cart", command=self.add_to_cart,font=("Arial", 27))
        self.add_button.grid(row=2, column=1, columnspan=1, padx=10, pady=10,ipady=35)

        # Create cart listbox
        self.cart_frame = ctk.CTkFrame(self.window)
        self.cart_frame.grid(row=2, column=2, columnspan=3, padx=35, pady=0)
        self.cart_label = ctk.CTkLabel(self.cart_frame, text="Cart: ",font=("Arial", 27))
        self.cart_label.grid(row=0, column=0 ,columnspan=1, padx=10, pady=10)
        self.cart_listbox = CTkListbox(self.cart_frame, height=350,width=220)
        self.cart_listbox.grid(row=0, column=1, columnspan=2, padx=10, pady=10)

        # Create total label
        self.total_frame = ctk.CTkFrame(self.window)
        self.total_frame.grid(row=2, column=5, columnspan=4, padx=10, pady=10)
        self.total_label = ctk.CTkLabel(self.total_frame, text=f"Total: {self.Sumprice}฿",font=("Arial", 27))
        self.total_label.grid(row=0, column=0, padx=10, pady=10)
        self.totalquantity_label = ctk.CTkLabel(self.total_frame, text=f"จำนวนทั้งหมด : {int(self.allitem_quantity)} ชิ้น",font=("Arial", 27))
        self.totalquantity_label.grid(row=1, column=0, padx=10, pady=10)
        self.Print = ctk.CTkButton(self.total_frame, text="Print", command=self.generate_receipt ,font=("Arial", 30))
        self.Print.grid(row=2, column=0, padx=10, pady=20, ipady=20)
        
        #Print and Reset Button
        self.RemoveButton = ctk.CTkButton(self.cart_frame, text="Remove From Cart",command=self.removefromcart,font=("Arial", 27))
        self.RemoveButton.grid(row=0, column=3, padx=10, pady=20, ipady=20)
        self.histry_button = ctk.CTkButton(self.window, text="Sale History", command=self.go2history,font=("Arial", 30))
        self.histry_button.grid(row=0, column=8, padx=10, pady=5,columnspan=2,ipadx=55)
        self.Exit = ctk.CTkButton(self.window, text="Exit", command=self.window.quit , font=("Arial", 30))
        self.Exit.grid(row=0, column=10, padx=10, pady=5,columnspan=1,sticky='e')
        
        self.window.mainloop()  
        
        
    
    
    
    
ShopApp = ShoppingCartApp()

