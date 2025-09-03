import tkinter as tk
from tkinter import messagebox



class CustomInputDialog:
    def __init__(self, parent, title, prompt, initialvalue=""):
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("320x140")
        self.top.resizable(False, False)
        self.top.configure(bg='#f0f0f0')
        self.top.transient(parent)
        self.top.grab_set()
        self.top.attributes('-topmost', True)
        
        # Center the dialog
        x = parent.winfo_rootx() + 50
        y = parent.winfo_rooty() + 50
        self.top.geometry("+{}+{}".format(x, y))
        
        # Label with professional styling
        label = tk.Label(
            self.top, 
            text=prompt, 
            bg='#f0f0f0',
            fg='#000000',
            font=("Segoe UI", 10)
        )
        label.pack(pady=(20, 8))
        
        # Entry field with professional styling
        self.entry = tk.Entry(
            self.top, 
            width=35,
            font=("Segoe UI", 10),
            bg='#ffffff',
            fg='#000000',
            relief=tk.FLAT,
            bd=2
        )
        self.entry.pack(pady=5)
        self.entry.insert(0, initialvalue)
        
        # Buttons with professional styling
        button_frame = tk.Frame(self.top, bg='#f0f0f0')
        button_frame.pack(pady=(15, 20))
        
        ok_button = tk.Button(
            button_frame, 
            text="OK", 
            command=self.ok, 
            width=8,
            font=("Segoe UI", 9),
            bg='#ffffff',
            fg='#000000',
            activebackground='#e0e0e0',
            relief=tk.RAISED,
            bd=1,
            cursor='hand2'
        )
        ok_button.pack(side=tk.LEFT, padx=8)
        
        cancel_button = tk.Button(
            button_frame, 
            text="Cancel", 
            command=self.cancel, 
            width=8,
            font=("Segoe UI", 9),
            bg='#ffffff',
            fg='#000000',
            activebackground='#e0e0e0',
            relief=tk.RAISED,
            bd=1,
            cursor='hand2'
        )
        cancel_button.pack(side=tk.LEFT, padx=8)
        
        # Bind Enter key to OK
        self.top.bind('<Return>', lambda e: self.ok())
        self.top.bind('<Escape>', lambda e: self.cancel())
        
        # Set focus after a short delay to ensure dialog is fully rendered
        self.top.after(100, self.set_focus)
        
        parent.wait_window(self.top)
    
    def set_focus(self):
        self.entry.focus_force()
        self.entry.select_range(0, tk.END)
    
    def ok(self):
        self.result = self.entry.get()
        self.top.destroy()
        # Ensure main window regains focus
        self.top.master.focus_force()
    
    def cancel(self):
        self.result = None
        self.top.destroy()
        # Ensure main window regains focus
        self.top.master.focus_force()

    def ask_string(parent, title, prompt, initialvalue=""):
        dialog = CustomInputDialog(parent, title, prompt, initialvalue)
        return dialog.result

class CustomNumericDialog:
    def __init__(self, parent, title, prompt, initialvalue="", is_float=False):
        self.result = None
        self.cancelled = False
        self.is_float = is_float
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("320x140")
        self.top.resizable(False, False)
        self.top.configure(bg='#f0f0f0')
        self.top.transient(parent)
        self.top.grab_set()
        self.top.attributes('-topmost', True)
        
        # Center the dialog
        x = parent.winfo_rootx() + 50
        y = parent.winfo_rooty() + 50
        self.top.geometry("+{}+{}".format(x, y))
        
        # Label with professional styling
        label = tk.Label(
            self.top, 
            text=prompt, 
            bg='#f0f0f0',
            fg='#000000',
            font=("Segoe UI", 10)
        )
        label.pack(pady=(20, 8))
        
        # Entry field with professional styling
        self.entry = tk.Entry(
            self.top, 
            width=35,
            font=("Segoe UI", 10),
            bg='#ffffff',
            fg='#000000',
            relief=tk.FLAT,
            bd=2
        )
        self.entry.pack(pady=5)
        self.entry.insert(0, str(initialvalue))
        
        # Buttons with professional styling
        button_frame = tk.Frame(self.top, bg='#f0f0f0')
        button_frame.pack(pady=(15, 20))
        
        ok_button = tk.Button(
            button_frame, 
            text="OK", 
            command=self.ok, 
            width=8,
            font=("Segoe UI", 9),
            bg='#ffffff',
            fg='#000000',
            activebackground='#e0e0e0',
            relief=tk.RAISED,
            bd=1,
            cursor='hand2'
        )
        ok_button.pack(side=tk.LEFT, padx=8)
        
        cancel_button = tk.Button(
            button_frame, 
            text="Cancel", 
            command=self.cancel, 
            width=8,
            font=("Segoe UI", 9),
            bg='#ffffff',
            fg='#000000',
            activebackground='#e0e0e0',
            relief=tk.RAISED,
            bd=1,
            cursor='hand2'
        )
        cancel_button.pack(side=tk.LEFT, padx=8)
        
        # Bind Enter key to OK
        self.top.bind('<Return>', lambda e: self.ok())
        self.top.bind('<Escape>', lambda e: self.cancel())
        
        # Set focus after a short delay to ensure dialog is fully rendered
        self.top.after(100, self.set_focus)
        
        parent.wait_window(self.top)
    
    def set_focus(self):
        self.entry.focus_force()
        self.entry.select_range(0, tk.END)
    
    def ok(self):
        try:
            value = self.entry.get()
            if self.is_float:
                self.result = float(value)
            else:
                self.result = int(value)
            self.cancelled = False
            self.top.destroy()  # Only destroy on valid input
            # Ensure main window regains focus
            self.top.master.focus_force()
        except ValueError:
            # Invalid input - don't close dialog, show error and let user try again
            self.result = None
            self.cancelled = False
            messagebox.showerror("Invalid Input", 
                "Please enter a valid number" if self.is_float else "Please enter a valid whole number")
            # Keep dialog open for user to correct input
            self.entry.focus_force()
            self.entry.select_range(0, tk.END)
    
    def cancel(self):
        self.result = None
        self.cancelled = True
        self.top.destroy()
        # Ensure main window regains focus
        self.top.master.focus_force()

    def ask_float(parent, title, prompt, initialvalue=0.0):
        dialog = CustomNumericDialog(parent, title, prompt, initialvalue, is_float=True)
        return dialog.result, dialog.cancelled

    def ask_integer(parent, title, prompt, initialvalue=0):
        dialog = CustomNumericDialog(parent, title, prompt, initialvalue, is_float=False)
        return dialog.result, dialog.cancelled