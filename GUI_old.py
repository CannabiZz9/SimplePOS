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

        self.current_price = 0
        self.Sumprice = 0
        self.allitem_quantity =0
        self.employee = "Defualt"
        self.create_widgets()
    
    def get_printers(self):
        """Scans for available printers and returns a list of names"""
        try:
            # EnumPrinters(Flags, Name, Level)
            # Level 2 returns tuples with printer name at index 2
            printers = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
            printer_names = [printer[2] for printer in printers]
            return printer_names
        except Exception as e:
            print(f"Error finding printers: {e}")
            return ["No Printers Found"]
    
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
            # Extract and convert the values to integers
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

    def print_receipt(self, text_to_print):
        # Get the specific printer name from the combobox
        selected_printer = self.printer_combobox.get()

        # Use 'w' mode with encoding to write UTF-8 content to the file
        with open(tempfile.mktemp(".txt"), "w", encoding='utf-8') as file:
            file.write(text_to_print)

        # Specify the full path to the created file
        filename = tempfile.mktemp(".txt")
        open(filename, "w", encoding='utf-8').write(text_to_print)

        for _ in range(2): 
            win32api.ShellExecute(
                            0,
                            "print",
                            filename,
                            '/d:"%s"' % selected_printer,
                            ".",
                            0
            )

    def Checkout(self):
        self.play_sound()
        text_to_print = self.generate_receipt()
        self.print_receipt(text_to_print)
        self.add_sale(self.Sumprice,self.employee)
        self.clearcart()
        
    def generate_bill_number(self):
        # Generate a unique bill number using a timestamp
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

        # Commit the changes
        connection.commit()
    
    def check_cart(self):
        if len(self.cart) > 0:
            # Enable the Print button if the listbox has items
            self.Print.configure(state=ctk.NORMAL)
            self.clearcart_Button.configure(state=ctk.NORMAL)
            self.RemoveButton.configure(state=ctk.NORMAL)
            
        else:
            # Disable the Print button if the listbox is empty
            self.Print.configure(state=ctk.DISABLED)
            self.clearcart_Button.configure(state=ctk.DISABLED)
            self.RemoveButton.configure(state=ctk.DISABLED)
            
    
    def go2history(self):
        self.play_sound()
        #self.create_histry_widgets()
        #self.histrywindow.mainloop()
        self.path2py = r"C:\Users\POS\Desktop\Program\SimplePOS\GUISale.py"
        subprocess.run(['python', resource_path(self.path2py)])
        #os.startfile("C:\Program Files (x86)\SimplePOS\History\History.exe")
        
    def play_sound(self):
        pygame.mixer.music.play()
    
    def koon(self, value):
        current_text = self.price_entry.get()
        
        # Check if text is not exactly "0" AND does not already have a "*"
        if current_text != "0" and "*" not in current_text:
            self.play_sound()
            self.price_entry.insert('end', value)
        
    def create_widgets(self):
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                try: pygame.mixer.music.load(resource_path("s.mp3"))
                except: pass
            except: pass
        self.play_sound()
        # Create price entry widget
        self.calculator_frame = ctk.CTkFrame(self.window)
        self.calculator_frame.grid(row=1, column=2, columnspan=4, padx=80, pady=5)
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
        self.cart_frame.grid(row=1, column=6, columnspan=3, padx=25, pady=0)
        self.buttoncart_frame = ctk.CTkFrame(self.cart_frame)
        self.buttoncart_frame.grid(row=0, column=4, columnspan=2, padx=35, pady=0)
        self.cart_listbox = CTkListbox(self.cart_frame, height=400,width=305,font=("Angsana New",39))
        self.cart_listbox.grid(row=0, column=1, columnspan=2, padx=10, pady=10)
        self.RemoveButton = ctk.CTkButton(self.buttoncart_frame, text="Remove",command=self.removefromcart,font=("Arial", 30), state=ctk.DISABLED)
        self.RemoveButton.grid(row=0, column=0, padx=10, pady=20, ipady=20)
        self.clearcart_Button = ctk.CTkButton(self.buttoncart_frame, text="Clear",command=self.clearcart,font=("Arial", 30), state=ctk.DISABLED)
        self.clearcart_Button.grid(row=1, column=0, padx=10, pady=20, ipady=20)

        # Create total label
        self.total_frame = ctk.CTkFrame(self.window)
        self.total_frame.grid(row=2, column=5, columnspan=4, padx=0, pady=10)
        self.total_label = ctk.CTkLabel(self.total_frame, text=f"Total: {self.Sumprice}฿",font=("Arial", 40))
        self.total_label.grid(row=0, column=0, padx=10, pady=10)
        self.totalquantity_label = ctk.CTkLabel(self.total_frame, text=f"จำนวนทั้งหมด : {int(self.allitem_quantity)} ชิ้น",font=("Arial", 27))
        self.totalquantity_label.grid(row=1, column=0, padx=10, pady=10)
        self.Print = ctk.CTkButton(self.total_frame, text="Print", command=self.Checkout ,font=("Arial", 27), state=ctk.DISABLED)
        self.Print.grid(row=2, column=0, padx=10, pady=30, ipady=30)
        
        #Printer Selection ComboBox
        printer_list = self.get_printers()
        self.printer_combobox = ctk.CTkComboBox(
            self.window, 
            values=printer_list, 
            font=("Arial", 20),
            width=250,
            state="readonly"
        )
        # Set the default printer as the selected item
        try:
            default_printer = win32print.GetDefaultPrinter()
            if default_printer in printer_list:
                self.printer_combobox.set(default_printer)
            elif printer_list:
                self.printer_combobox.set(printer_list[0])
        except:
            if printer_list: self.printer_combobox.set(printer_list[0])
        self.printer_combobox.grid(row=0, column=6, padx=0, pady=50)

        #History and Exit
        self.histry_button = ctk.CTkButton(self.window, text="History", command=self.go2history,font=("Arial", 30))
        self.histry_button.grid(row=0, column=7, padx=20, pady=50)
        self.Exit = ctk.CTkButton(self.window, text="Exit", command=self.window.quit , font=("Arial", 30))
        self.Exit.grid(row=0, column=8, padx=5, pady=50,sticky='e')
        
        self.window.mainloop()  
        
        
    
    
    
    
ShopApp = ShoppingCartApp()
