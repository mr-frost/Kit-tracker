import concurrent.futures
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import requests
import json
import pandas as pd
from tkintermapview import TkinterMapView
import webbrowser

API_URL = "https://kit-tracker.peacemosquitto.workers.dev/devices"
API_TOKEN = "63T-nAch05-p3W5-lIn60t"  # API Key for authentication
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}  # Headers with API key for all requests

class EquipmentManager:
    def __init__(self):
        self.equipment = []  # List of dicts
        self.previous_equipment = []  # For tracking changes

    def fetch_equipment_from_api(self):
        print(f"Fetching equipment data from API with token: {API_TOKEN[:10]}...")
        response = requests.get(API_URL, headers=HEADERS)
        print(f"API Response Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Received {len(data) if isinstance(data, list) else 1} equipment records")
            if isinstance(data, list):
                self.equipment = data
            else:
                self.equipment = [data]
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            messagebox.showerror("API Error", f"{response.status_code}: {response.text}")

    def fetch_details_for_device_ids(self, id_field="id", detail_endpoint_template=None):
        # detail_endpoint_template example: "https://kit-tracker.peacemosquitto.workers.dev/device/{id}"
        if not detail_endpoint_template:
            messagebox.showerror("API Error", "No detail endpoint template provided.")
            return
        device_ids = [eq[id_field] for eq in self.equipment if id_field in eq]
        print(f"Found {len(device_ids)} device IDs: {device_ids}")
        results = []
        def fetch_detail(device_id):
            url = detail_endpoint_template.format(**{id_field: device_id})
            print(f"Fetching from {url}")
            try:
                resp = requests.get(url, headers=HEADERS)
                if resp.status_code == 200:
                    print(f"Success for {device_id}")
                    return resp.json()
                else:
                    print(f"Error for {device_id}: {resp.status_code}")
                    return {"serial": device_id, "error": resp.status_code}
            except Exception as e:
                print(f"Exception for {device_id}: {str(e)}")
                return {"serial": device_id, "error": str(e)}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(fetch_detail, device_ids))
        print(f"Total results: {len(results)}")
        # Update equipment with details
        self.equipment = results

    def check_for_alerts(self):
        if not self.previous_equipment:
            self.previous_equipment = [eq.copy() for eq in self.equipment]
            return
        current_serials = {eq.get('serial') for eq in self.equipment if 'serial' in eq}
        previous_serials = {eq.get('serial') for eq in self.previous_equipment if 'serial' in eq}
        for serial in current_serials & previous_serials:
            current_eq = next((eq for eq in self.equipment if eq.get('serial') == serial), None)
            previous_eq = next((eq for eq in self.previous_equipment if eq.get('serial') == serial), None)
            if current_eq and previous_eq:
                if previous_eq.get('online') is True and current_eq.get('online') is False:
                    messagebox.showwarning("Connectivity Alert", f"Device {serial} ({current_eq.get('model', 'Unknown')}) has gone offline!")
                if not previous_eq.get('tampered') and current_eq.get('tampered'):
                    messagebox.showerror("Tamper Alert", f"URGENT: Device {serial} ({current_eq.get('model', 'Unknown')}) has been tampered with!")
        self.previous_equipment = [eq.copy() for eq in self.equipment]

    def fetch_authenticated_stream_url(self, device_id):
        """Fetch authenticated stream URL from API"""
        try:
            # Try to get authenticated stream URL from API
            url = f"https://kit-tracker.peacemosquitto.workers.dev/device/{device_id}/stream/auth"
            print(f"Fetching authenticated stream URL: {url}")
            response = requests.get(url, headers=HEADERS)
            print(f"Auth stream response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Auth stream data: {data}")
                if isinstance(data, dict) and 'authenticated_url' in data:
                    return data['authenticated_url']
                elif isinstance(data, str):
                    return data
        except Exception as e:
            print(f"Error fetching authenticated stream: {str(e)}")
        return None

    def update_equipment(self, idx, entry):
        self.equipment[idx] = entry

    def delete_equipment(self, idx):
        del self.equipment[idx]

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
        except ValueError:
            self.result = None
        self.top.destroy()
        # Ensure main window regains focus
        self.top.master.focus_force()
    
    def cancel(self):
        self.result = None
        self.top.destroy()
        # Ensure main window regains focus
        self.top.master.focus_force()

def ask_float(parent, title, prompt, initialvalue=0.0):
    dialog = CustomNumericDialog(parent, title, prompt, initialvalue, is_float=True)
    return dialog.result

def ask_integer(parent, title, prompt, initialvalue=0):
    dialog = CustomNumericDialog(parent, title, prompt, initialvalue, is_float=False)
    return dialog.result

class EquipmentApp:
    def __init__(self, root, manager):
        self.root = root
        self.manager = manager
        
        # Professional styling
        self.root.title("Equipment Manager")
        self.root.geometry("1200x600")
        self.root.configure(bg='#f0f0f0')  # Light grey background
        
        # Custom fonts
        self.title_font = ("Segoe UI", 12, "bold")
        self.button_font = ("Segoe UI", 10)
        self.text_font = ("Consolas", 10)
        
        # Color scheme
        self.bg_color = '#f0f0f0'  # Light grey
        self.frame_bg = '#ffffff'  # White
        self.button_bg = '#ffffff'  # White buttons
        self.button_fg = '#000000'  # Black text
        self.button_active_bg = '#e0e0e0'  # Light grey when pressed
        self.border_color = '#cccccc'  # Grey borders
        
        # Main paned window with styling
        self.paned = tk.PanedWindow(root, orient=tk.HORIZONTAL, bg=self.bg_color, sashwidth=8, sashrelief=tk.RAISED)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for list and buttons
        self.list_frame = tk.Frame(self.paned, bg=self.frame_bg, relief=tk.RIDGE, bd=2)
        self.paned.add(self.list_frame)
        
        # Button frame with professional styling
        self.button_frame = tk.Frame(self.list_frame, bg=self.frame_bg)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        # Equipment details text with styling
        self.details_text = tk.Text(
            self.list_frame, 
            width=50, 
            font=self.text_font,
            bg=self.frame_bg,
            fg=self.button_fg,
            relief=tk.FLAT,
            bd=1,
            padx=10,
            pady=10
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10,5))
        
        # Professional button styling with better sizing
        button_style = {
            'font': ("Segoe UI", 9, "bold"),  # Slightly smaller, bold font
            'bg': self.button_bg,
            'fg': self.button_fg,
            'activebackground': self.button_active_bg,
            'activeforeground': self.button_fg,
            'relief': tk.RAISED,  # Raised for 3D bevel effect
            'bd': 3,  # Thicker border for better bevel
            'width': 20,  # Wider to fit text nicely
            'height': 2,
            'cursor': 'hand2',
            'highlightthickness': 1,
            'highlightbackground': self.border_color,
            'highlightcolor': '#666666'
        }
        
        # Create buttons with improved styling
        self.import_btn = tk.Button(self.button_frame, text="📥 Import to CSV", command=self.import_csv, **button_style)
        self.import_btn.grid(row=0, column=0, pady=10, padx=10)
        
        self.export_csv_btn = tk.Button(self.button_frame, text="📤 Export to CSV", command=self.export_to_csv, **button_style)
        self.export_csv_btn.grid(row=0, column=1, pady=10, padx=10)
        
        self.add_btn = tk.Button(self.button_frame, text="➕ Add Equipment", command=self.add_entry, **button_style)
        self.add_btn.grid(row=1, column=0, pady=10, padx=10)
        
        self.update_btn = tk.Button(self.button_frame, text="✏️ Update Equipment", command=self.update_entry, **button_style)
        self.update_btn.grid(row=1, column=1, pady=10, padx=10)
        
        self.delete_btn = tk.Button(self.button_frame, text="🗑️ Delete Equipment", command=self.delete_entry, **button_style)
        self.delete_btn.grid(row=2, column=0, pady=10, padx=10)
        
        self.refresh_btn = tk.Button(self.button_frame, text="🔄 Refresh from API", command=self.refresh_from_api, **button_style)
        self.refresh_btn.grid(row=2, column=1, pady=10, padx=10)
        
        # Special styling for the live feed button (spans both columns)
        live_feed_style = button_style.copy()
        live_feed_style['width'] = 25  # Wider since it spans 2 columns
        live_feed_style['bg'] = '#e8f4f8'  # Light blue background for emphasis
        live_feed_style['activebackground'] = '#d0e8f0'
        
        self.view_feed_btn = tk.Button(self.button_frame, text="📹 View Live Camera Feed", command=self.view_live_feed, **live_feed_style)
        self.view_feed_btn.grid(row=3, column=0, columnspan=2, pady=10, padx=10)
        
        # Right panel for map
        self.map_widget = TkinterMapView(self.paned)
        self.paned.add(self.map_widget)
        
        self.refresh_list()
        self.update_map()
        self.schedule_auto_update()

    def schedule_auto_update(self):
        self.refresh_from_api()
        self.root.after(60000, self.schedule_auto_update)  # Auto-update every 60 seconds

    def import_csv(self):
        filepath = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV files", "*.csv")])
        if filepath:
            try:
                df = pd.read_csv(filepath)
                self.manager.equipment = df.to_dict(orient='records')
                # Filter to only include dict entries
                self.manager.equipment = [eq for eq in self.manager.equipment if isinstance(eq, dict)]
                if not self.manager.equipment:
                    raise ValueError("No valid dictionary data found in CSV.")
                messagebox.showinfo("Import Success", f"Equipment data imported from {filepath}")
                self.refresh_list()
                self.update_map()
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import CSV: {str(e)}")

    def refresh_from_api(self):
        self.manager.fetch_equipment_from_api()
        self.manager.check_for_alerts()
        self.refresh_list()
        self.update_map()

    def refresh_list(self):
        self.details_text.delete(1.0, tk.END)
        if self.manager.equipment:
            eq = self.manager.equipment[0]  # Display details for the first (or only) device
            self.details_text.insert(tk.END, "Equipment Details:\n\n")
            for key, value in eq.items():
                if key == "position" and isinstance(value, dict):
                    lat = value.get("lat", "N/A")
                    lon = value.get("lon", "N/A")
                    self.details_text.insert(tk.END, f"GPS Location: {lat}, {lon}\n")
                elif key == "battery":
                    self.details_text.insert(tk.END, f"Battery Level: {value}%\n")
                elif key == "payload" and isinstance(value, dict) and "image" in value:
                    self.details_text.insert(tk.END, f"Recent Image: {value['image']}\n")
                elif key == "online":
                    status = "ONLINE" if value else "OFFLINE"
                    self.details_text.insert(tk.END, f"Connectivity Status: {status}\n")
                elif key == "tampered":
                    tamper_status = "DETECTED" if value else "OK"
                    self.details_text.insert(tk.END, f"Tamper Status: {tamper_status}\n")
                else:
                    self.details_text.insert(tk.END, f"{key.title()}: {value}\n")
            self.details_text.insert(tk.END, "\n")
        else:
            self.details_text.insert(tk.END, "No equipment data available.\n")

    def update_map(self):
        self.map_widget.delete_all_marker()
        if self.manager.equipment:
            first_pos = self.manager.equipment[0].get("position", {})
            lat = first_pos.get("lat", 0)
            lon = first_pos.get("lon", 0)
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(10)
        
        for eq in self.manager.equipment:
            if "position" in eq and isinstance(eq["position"], dict):
                lat = eq["position"].get("lat")
                lon = eq["position"].get("lon")
                if lat is not None and lon is not None:
                    popup = f"Model: {eq.get('model', 'Unknown')}\nSerial: {eq.get('serial', 'N/A')}\nBattery: {eq.get('battery', 'N/A')}%"
                    self.map_widget.set_marker(lat, lon, text=popup)

    def add_entry(self):
        name = ask_string(self.root, "Add Equipment", "Type:")
        if not name:
            return
        model = ask_string(self.root, "Add Equipment", "Model:")
        if not model:
            return
        serial = ask_string(self.root, "Add Equipment", "Serial:")
        if not serial:
            return
        try:
            lat = ask_float(self.root, "Add Equipment", "Latitude:")
            if lat is None:
                return
            lon = ask_float(self.root, "Add Equipment", "Longitude:")
            if lon is None:
                return
            battery = ask_integer(self.root, "Add Equipment", "Battery Level (%):")
            if battery is None:
                return
        except:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for location and battery.")
            return
        entry = {
            "type": name,
            "model": model,
            "serial": serial,
            "position": {"lat": lat, "lon": lon},
            "battery": battery,
            "online": True,
            "tampered": False,
            "payload": {}
        }
        self.manager.add_equipment(entry)
        self.refresh_list()
        self.update_map()

    def update_entry(self):
        if not self.manager.equipment:
            messagebox.showinfo("No Device", "No equipment data available.")
            return
        
        eq = self.manager.equipment[0]
        
        # Get current values
        current_type = eq.get('type', '')
        current_model = eq.get('model', '')
        current_serial = eq.get('serial', '')
        current_pos = eq.get('position', {})
        current_lat = current_pos.get('lat', 0) if isinstance(current_pos, dict) else 0
        current_lon = current_pos.get('lon', 0) if isinstance(current_pos, dict) else 0
        current_battery = eq.get('battery', 0)
        
        # Prompt for new values
        name = ask_string(self.root, "Update Equipment", "Type:", current_type)
        if name is None:  # Cancelled
            return
        
        model = ask_string(self.root, "Update Equipment", "Model:", current_model)
        if model is None:
            return
        
        serial = ask_string(self.root, "Update Equipment", "Serial:", current_serial)
        if serial is None:
            return
        
        try:
            lat = ask_float(self.root, "Update Equipment", "Latitude:", current_lat)
            if lat is None:
                return
            
            lon = ask_float(self.root, "Update Equipment", "Longitude:", current_lon)
            if lon is None:
                return
            
            battery = ask_integer(self.root, "Update Equipment", "Battery Level (%):", current_battery)
            if battery is None:
                return
        except:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for location and battery.")
            return
        
        # Update the equipment
        eq['type'] = name
        eq['model'] = model
        eq['serial'] = serial
        eq['position'] = {"lat": lat, "lon": lon}
        eq['battery'] = battery
        
        self.refresh_list()
        self.update_map()

    def delete_entry(self):
        if self.manager.equipment:
            confirm = messagebox.askyesno("Delete Equipment", "Are you sure you want to delete the equipment?")
            if confirm:
                self.manager.equipment = []
                self.refresh_list()
                self.update_map()
        else:
            messagebox.showinfo("No Device", "No equipment data available.")

    def view_live_feed(self):
        if self.manager.equipment:
            eq = self.manager.equipment[0]
            payload = eq.get('payload', {})
            
            # First, try to get authenticated stream URL from API
            stream_url = None
            device_id = payload.get('id') or eq.get('id')
            
            if device_id:
                # Try authenticated endpoint first
                stream_url = self.manager.fetch_authenticated_stream_url(device_id)
                
                # If that fails, try regular stream endpoint
                if not stream_url:
                    stream_url = self.manager.fetch_live_feed_url(device_id)
            
            # If API doesn't provide URL, try different authentication methods
            if not stream_url and 'id' in payload:
                device_id = payload['id']
                
                # Method 1: Try with token in Authorization header format as query param
                stream_url = f"https://kit-tracker.peacemosquitto.workers.dev/stream/{device_id}?authorization=Bearer%20{API_TOKEN}"
            
            if stream_url:
                try:
                    print(f"Opening stream URL: {stream_url}")
                    webbrowser.open(stream_url)
                    messagebox.showinfo("Live Feed", f"Opening live feed:\n{stream_url}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open live feed: {str(e)}")
            else:
                messagebox.showerror("No Stream Available", "Unable to generate authenticated stream URL. Please check your connection and try again.")
        else:
            messagebox.showinfo("No Device", "No equipment data available.")

    def export_to_csv(self):
        if self.manager.equipment:
            df = pd.DataFrame(self.manager.equipment)
            filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if filepath:
                df.to_csv(filepath, index=False)
                messagebox.showinfo("Export Success", f"Equipment data exported to {filepath}")
        else:
            messagebox.showinfo("No Data", "No equipment data available to export.")

if __name__ == "__main__":
    manager = EquipmentManager()
    root = tk.Tk()
    app = EquipmentApp(root, manager)
    root.mainloop()
