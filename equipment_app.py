import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd
from tkintermapview import TkinterMapView
from video import VideoPlayer
import os
import datetime
import queue
import time
import constants
import utils


class EquipmentApp:
    def __init__(self, root, manager):
        self.root = root
        self.manager = manager
        self.device_markers = []  # Store marker references
        self.details_panel_visible = False  # Track if details panel is shown
        self.details_frame = None  # Will be created dynamically
        self.root.title("Equipment Manager")
        self.root.geometry("1400x700")  # More compact size for better space utilization
        self.root.configure(bg='#f0f0f0')  # Light grey background
        
        # Custom fonts
        self.title_font = ("Segoe UI", 10, "bold")
        self.button_font = ("Segoe UI", 9)
        self.text_font = ("Consolas", 9)
        
        # Color scheme
        self.bg_color = '#f0f0f0'  # Light grey
        self.frame_bg = '#ffffff'  # White
        self.button_bg = '#ffffff'  # White buttons
        self.button_fg = '#000000'  # Black text
        self.button_active_bg = '#e0e0e0'  # Light grey when pressed
        self.border_color = '#cccccc'  # Grey borders
        
        # Main paned window with styling
        self.paned = tk.PanedWindow(root, orient=tk.HORIZONTAL, bg=self.bg_color, sashwidth=0)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for list and buttons
        self.list_frame = tk.Frame(self.paned, bg=self.frame_bg, relief=tk.RIDGE, bd=2)
        self.paned.add(self.list_frame)
        
        # Button frame with professional styling
        self.button_frame = tk.Frame(self.list_frame, bg=self.frame_bg)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Equipment listbox with styling
        self.equipment_listbox = tk.Listbox(
            self.list_frame,
            font=self.text_font,
            bg=self.frame_bg,
            fg=self.button_fg,
            selectmode=tk.SINGLE,
            height=12,
            relief=tk.FLAT,
            bd=1,
            selectbackground='#e0e0e0',
            selectforeground=self.button_fg,
            activestyle='none'
        )
        self.equipment_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5,3))

        # Add a status label below the listbox to show selected device info
        self.selected_device_label = tk.Label(
            self.list_frame,
            text="No device selected",
            font=("Segoe UI", 9),
            bg=self.frame_bg,
            fg='#666666',
            anchor='w'
        )
        self.selected_device_label.pack(fill=tk.X, padx=5, pady=(0, 5))

        # Bind single-click event to open device details
        self.equipment_listbox.bind('<Button-1>', self.on_device_click)
        # Bind right-click or double-click to clear selection
        self.equipment_listbox.bind('<Button-3>', lambda e: self.hide_device_details())
        self.equipment_listbox.bind('<Double-Button-1>', lambda e: self.hide_device_details())
        
        # Professional button styling with better sizing
        button_style = {
            'font': ("Segoe UI", 8, "bold"),  # Smaller, bold font
            'bg': self.button_bg,
            'fg': self.button_fg,
            'activebackground': self.button_active_bg,
            'relief': tk.RAISED,  # Raised for 3D bevel effect
            'bd': 2,  # Thinner border for compactness
            'width': 18,  # Narrower to fit text nicely
            'height': 1,
            'cursor': 'hand2',
            'highlightthickness': 1,
            'highlightbackground': self.border_color,
            'highlightcolor': '#666666'
        }
        
        # Create buttons with improved styling
        self.import_btn = tk.Button(self.button_frame, text="📥 Import to CSV", command=self.import_csv, **button_style)
        self.import_btn.grid(row=0, column=0, pady=3, padx=3)
        
        self.export_csv_btn = tk.Button(self.button_frame, text="📤 Export to CSV", command=self.export_to_csv, **button_style)
        self.export_csv_btn.grid(row=0, column=1, pady=3, padx=3)
        
        self.add_btn = tk.Button(self.button_frame, text="➕ Add Equipment", command=self.add_entry, **button_style)
        self.add_btn.grid(row=1, column=0, pady=3, padx=3)
        
        self.update_btn = tk.Button(self.button_frame, text="✏️ Update Equipment", command=self.update_entry, **button_style)
        self.update_btn.grid(row=1, column=1, pady=3, padx=3)
        
        self.delete_btn = tk.Button(self.button_frame, text="🗑️ Delete Equipment", command=self.delete_entry, **button_style)
        self.delete_btn.grid(row=2, column=0, pady=3, padx=3)
        
        self.refresh_btn = tk.Button(self.button_frame, text="🔄 Refresh from API", command=self.refresh_from_api, **button_style)
        self.refresh_btn.grid(row=2, column=1, pady=3, padx=3)
        
        # Add performance settings button
        self.performance_btn = tk.Button(self.button_frame, text="⚡ Performance", command=self.configure_performance, **button_style)
        self.performance_btn.grid(row=3, column=1, pady=3, padx=3)
        
        # Add clear cache button
        self.clear_cache_btn = tk.Button(self.button_frame, text="🗑️ Clear Cache", command=self.clear_cache, **button_style)
        self.clear_cache_btn.grid(row=3, column=0, pady=3, padx=3)
        
        # Add view live feed button (centered below)
        self.live_feed_btn = tk.Button(self.button_frame, text="📹 View Live Feed", command=self.view_live_feed, **button_style)
        self.live_feed_btn.grid(row=4, columnspan=2, pady=3, padx=3)
        
        # Right panel - tabbed interface for map and VLC player
        self.middle_frame = tk.Frame(self.paned, bg=self.frame_bg)
        self.paned.add(self.middle_frame)
        
        # Create tab buttons
        self.tab_frame = tk.Frame(self.middle_frame, bg=self.frame_bg, height=35)
        self.tab_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Tab buttons
        tab_style = {
            'font': ("Segoe UI", 8, "bold"),
            'bg': self.button_bg,
            'fg': self.button_fg,
            'activebackground': self.button_active_bg,
            'relief': tk.RAISED,
            'bd': 2,
            'cursor': 'hand2',
            'width': 12
        }
        
        self.map_tab_btn = tk.Button(self.tab_frame, text="🗺️ Map View", command=self.show_map_tab, **tab_style)
        self.map_tab_btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        self.vlc_tab_btn = tk.Button(self.tab_frame, text="📹 Live Feed", command=self.show_vlc_tab, **tab_style)
        self.vlc_tab_btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        # Content frames
        self.content_frame = tk.Frame(self.middle_frame, bg=self.frame_bg)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Map widget
        self.map_frame = tk.Frame(self.content_frame, bg=self.frame_bg)
        self.map_widget = TkinterMapView(self.map_frame)
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add legend frame below the map
        self.legend_frame = tk.Frame(self.map_frame, bg=self.frame_bg, relief=tk.RIDGE, bd=1)
        self.legend_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=3, pady=3)
        
        # Legend title
        legend_title = tk.Label(self.legend_frame, text="📍 Map Legend - Device Types", 
                              font=("Segoe UI", 9, "bold"), bg=self.frame_bg)
        legend_title.pack(pady=(3, 1))
        
        # Add readability note
        readability_note = tk.Label(self.legend_frame, 
                                  text="💡 Click any device in the list to view details in a slide-out panel!\n"
                                       "📍 Markers show Model + Serial for easy identification",
                                  font=("Segoe UI", 7), bg=self.frame_bg, fg="#666666", justify="left")
        readability_note.pack(pady=(0, 3))
        
        # Legend items with updated brighter colors
        legend_items = [
            ("🔵 GPS/Tracking (BE300)", "#4169E1"),
            ("🟢 Sensors", "#32CD32"),
            ("🟣 Military (AVENGER/SCORPION/SNOOPER)", "#9932CC"),
            ("🟡 Communication", "#FFD700"),
            ("⚫ Offline Devices", "#708090")
        ]
        
        legend_inner_frame = tk.Frame(self.legend_frame, bg=self.frame_bg)
        legend_inner_frame.pack(pady=3)
        
        for i, (label, color) in enumerate(legend_items):
            # Color indicator
            color_label = tk.Label(legend_inner_frame, text="●", fg=color, 
                                 font=("Segoe UI", 10, "bold"), bg=self.frame_bg)
            color_label.grid(row=i//2, column=i%2*2, padx=(5, 1), pady=1)
            
            # Text label
            text_label = tk.Label(legend_inner_frame, text=label, 
                                font=("Segoe UI", 8), bg=self.frame_bg, anchor="w")
            text_label.grid(row=i//2, column=i%2*2+1, padx=(0, 5), pady=1, sticky="w")
        
        # VideoPlayer integration
        self.video_player = VideoPlayer(self.content_frame, status_callback=self.update_status)
        
        # Start with map tab visible
        self.show_map_tab()
        
        # Bind cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_status(self, message):
        """Update status display with video player messages"""
        print(f"Video Status: {message}")

    def on_device_click(self, event):
        """Handle single click on device in listbox - directly opens device details"""
        # Use event coordinates to determine which item was clicked
        # This avoids timing issues with curselection()
        clicked_index = self.equipment_listbox.nearest(event.y)
        
        print(f"🖱️ Single-click detected at y={event.y}, nearest item: {clicked_index}")

        # Account for header row (index 0 is header, so actual device index is clicked_index - 1)
        if clicked_index == 0:
            print("📋 Header clicked - no device action")
            return

        device_index = clicked_index - 1  # Subtract 1 because index 0 is header

        if 0 <= device_index < len(self.manager.equipment):
            device = self.manager.equipment[device_index]

            # Debug information
            model = device.get('model', 'Unknown')
            serial = device.get('serial', 'N/A')
            position = device.get('position', {})
            lat = position.get('lat', 'N/A') if isinstance(position, dict) else 'N/A'
            lon = position.get('lon', 'N/A') if isinstance(position, dict) else 'N/A'

            print(f"🎯 Device clicked: {model} (Serial: {serial})")
            print(f"📍 Coordinates: {lat}, {lon}")
            print(f"📊 Device index: {device_index} (Listbox index: {clicked_index})")

            # Directly open device details (no delay needed since there's no selection step)
            self.show_device_details(device_index)
            
            # Center the map on the selected device
            self.center_map_on_device(device)
        else:
            print(f"❌ Invalid device index: {device_index} (Total devices: {len(self.manager.equipment)})")

    def show_device_details(self, device_index):
        """Show detailed information for the selected device in a dynamic details panel"""
        print(f"🔍 Showing device details for device index: {device_index}")

        if device_index < len(self.manager.equipment):
            device = self.manager.equipment[device_index]
            model = device.get('model', 'Unknown')
            serial = device.get('serial', 'N/A')
            print(f"📋 Populating details panel for {model} (Serial: {serial})")

            # Track which device is currently displayed
            self.current_details_device_index = device_index

            # Show the details panel if not already visible
            if not self.details_panel_visible:
                self._show_details_panel()

            # Clear existing content in details frame
            for widget in self.details_frame.winfo_children():
                widget.destroy()

            # Create main frame for details (roomier for readability)
            main_frame = tk.Frame(self.details_frame, padx=1, pady=2)
            main_frame.configure(width=240)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Header with close button
            header_frame = tk.Frame(main_frame, bg=self.frame_bg)
            header_frame.configure(width=238, height=35)  # 240px main_frame - 2px padding, fixed height for button
            header_frame.pack_propagate(False)
            header_frame.pack(fill=tk.X, pady=(0, 3))

            title_label = tk.Label(header_frame, text="📱 Device Details", font=("Segoe UI", 12, "bold"))
            title_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)

            close_btn = tk.Button(header_frame, text="✕", font=("Segoe UI", 12, "bold"),
                                bg="#ff0000", fg="white", relief="raised", padx=6, pady=4,
                                command=self.hide_device_details, cursor='hand2',
                                width=3, height=1, borderwidth=2)
            close_btn.pack(side=tk.RIGHT, padx=(0, 5), pady=5)

            # Create scrollable frame for details - adjust canvas width to account for scrollbar
            canvas = tk.Canvas(main_frame, width=224, highlightthickness=0, bd=0)
            scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview, width=14)
            scrollable_frame = tk.Frame(canvas)
            scrollable_frame.configure(width=224)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=224)
            canvas.configure(yscrollcommand=scrollbar.set)

            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="y")
            scrollbar.pack(side="right", fill="y")

            print(f"📏 Canvas width: {canvas.winfo_reqwidth()}px, Scrollbar width: {scrollbar.winfo_reqwidth()}px")
            print(f"📏 Main frame requested width: {main_frame.winfo_reqwidth()}px")
            print(f"📏 Header frame width: {header_frame.winfo_reqwidth()}px")

            # Device information labels
            info_labels = []

            # Model and Serial (header info)
            header_label = tk.Label(scrollable_frame, text=f"{model} (Serial: {serial})",
                                  font=("Segoe UI", 9, "bold"), fg="#2E86C1", wraplength=224)
            header_label.pack(pady=(0, 3))
            info_labels.append(header_label)

            # Process all device fields
            for key, value in device.items():
                if key == "position" and isinstance(value, dict):
                    lat = value.get("lat", "N/A")
                    lon = value.get("lon", "N/A")
                    label = tk.Label(scrollable_frame, text=f"📍 GPS Location: {lat}, {lon}",
                                   font=("Segoe UI", 8), anchor="w", justify="left", wraplength=224)
                    label.pack(fill="x", pady=1)
                    info_labels.append(label)

                elif key == "battery":
                    battery_icon = "🔋" if value > 50 else "🪫" if value > 20 else "🔌"
                    color = "green" if value > 50 else "orange" if value > 20 else "red"
                    label = tk.Label(scrollable_frame, text=f"{battery_icon} Battery Level: {value}%",
                                   font=("Segoe UI", 8), fg=color, anchor="w", justify="left", wraplength=224)
                    label.pack(fill="x", pady=1)
                    info_labels.append(label)

                elif key == "payload" and isinstance(value, dict) and "image" in value:
                    label = tk.Label(scrollable_frame, text=f"📷 Recent Image: {value['image']}",
                                   font=("Segoe UI", 8), anchor="w", justify="left", wraplength=224)
                    label.pack(fill="x", pady=1)
                    info_labels.append(label)

                elif key == "online":
                    status_icon = "🟢" if value else "🔴"
                    status = "ONLINE" if value else "OFFLINE"
                    color = "green" if value else "red"
                    label = tk.Label(scrollable_frame, text=f"{status_icon} Connectivity Status: {status}",
                                   font=("Segoe UI", 8), fg=color, anchor="w", justify="left", wraplength=224)
                    label.pack(fill="x", pady=1)
                    info_labels.append(label)

                elif key == "tampered":
                    tamper_icon = "⚠️" if value else "✅"
                    tamper_status = "DETECTED" if value else "OK"
                    color = "red" if value else "green"
                    label = tk.Label(scrollable_frame, text=f"{tamper_icon} Tamper Status: {tamper_status}",
                                   font=("Segoe UI", 8), fg=color, anchor="w", justify="left", wraplength=224)
                    label.pack(fill="x", pady=1)
                    info_labels.append(label)

                elif key not in ["position", "battery", "payload", "online", "tampered"]:
                    # Format other fields nicely
                    if key == "type":
                        label = tk.Label(scrollable_frame, text=f"📋 Type: {value}",
                                       font=("Segoe UI", 8), anchor="w", justify="left", wraplength=224)
                    elif key == "op":
                        label = tk.Label(scrollable_frame, text=f"� Operator: {value}",
                                       font=("Segoe UI", 10), anchor="w", justify="left", wraplength=224)
                    elif key == "description":
                        label = tk.Label(scrollable_frame, text=f"📝 Description: {value}",
                                       font=("Segoe UI", 8), anchor="w", justify="left", wraplength=224)
                    elif key == "timestamp":
                        label = tk.Label(scrollable_frame, text=f"🕒 Last Update: {value}",
                                       font=("Segoe UI", 8), anchor="w", justify="left", wraplength=224)
                    elif key == "mobile":
                        mobile_status = "📱 Mobile" if value else "🏠 Stationary"
                        label = tk.Label(scrollable_frame, text=f"{mobile_status}",
                                       font=("Segoe UI", 8), anchor="w", justify="left", wraplength=224)
                    else:
                        label = tk.Label(scrollable_frame, text=f"{key.title()}: {value}",
                                       font=("Segoe UI", 8), anchor="w", justify="left", wraplength=224)

                    label.pack(fill="x", pady=1)
                    info_labels.append(label)

            # Device details panel is now complete - no refresh button needed

        else:
            # No device selected - hide the details panel
            if self.details_panel_visible:
                self.hide_device_details()

    def _show_details_panel(self):
        """Show the details panel by adding it to the paned window"""
        if not self.details_panel_visible:
            # Store original window size for restoration
            self.original_width = self.root.winfo_width()
            self.original_height = self.root.winfo_height()

            # Store current pane sizes before adding the details panel
            current_list_width = self.list_frame.winfo_width()
            current_middle_width = self.middle_frame.winfo_width()

            # Create the details frame
            self.details_frame = tk.Frame(self.paned, bg=self.frame_bg, relief=tk.RIDGE, bd=2)
            # Enforce strict width so contents don't expand the pane
            self.details_frame.configure(width=240)
            self.details_frame.pack_propagate(False)

            # Add it to the paned window
            self.paned.add(self.details_frame)

            # Configure all panes to maintain proper proportions
            # Set weights to preserve existing pane sizes when details panel is added
            self.paned.paneconfigure(self.list_frame,
                                   minsize=current_list_width,
                                   stretch="never",
                                   padx=0, pady=0)
            self.paned.paneconfigure(self.middle_frame,
                                   minsize=current_middle_width,
                                   stretch="always",
                                   padx=0, pady=0)
            self.paned.paneconfigure(self.details_frame,
                                   width=240,
                                   minsize=240,
                                   stretch="never",
                                   padx=0, pady=0)

            # Expand the main window to accommodate the new panel
            new_width = self.original_width + 245  # 240px panel + 5px for minimal spacing
            self.root.geometry(f"{new_width}x{self.original_height}")

            self.details_panel_visible = True
            print("📱 Details panel shown - window expanded")
            print(f"📏 Panel configured width: 240px, actual width: {self.details_frame.winfo_reqwidth()}px")
            print(f"📏 Window size: {self.root.winfo_width()}x{self.root.winfo_height()} (was {self.original_width}x{self.original_height})")
            print(f"📏 Panes: List={self.list_frame.winfo_width()}px, Middle={self.middle_frame.winfo_width()}px, Details={self.details_frame.winfo_width()}px")

    def hide_device_details(self):
        """Hide the device details panel and restore original layout"""
        if self.details_panel_visible and hasattr(self, 'details_frame'):
            # Remove the details frame from the paned window
            self.paned.forget(self.details_frame)

            # Destroy the details frame
            self.details_frame.destroy()
            delattr(self, 'details_frame')

            # Clear the current device index tracking
            if hasattr(self, 'current_details_device_index'):
                delattr(self, 'current_details_device_index')

            # Restore original window size
            if hasattr(self, 'original_width') and hasattr(self, 'original_height'):
                self.root.geometry(f"{self.original_width}x{self.original_height}")

            self.details_panel_visible = False
            print("📱 Details panel hidden - window restored")
            print(f"📏 Window size: {self.root.winfo_width()}x{self.root.winfo_height()} (was {self.original_width}x{self.original_height})")
            print(f"📏 Panes: List={self.list_frame.winfo_width()}px, Middle={self.middle_frame.winfo_width()}px")

    def center_map_on_device(self, device):
        """Center the map on the specified device with proper zoom"""
        if "position" in device and isinstance(device["position"], dict):
            lat = device["position"].get("lat")
            lon = device["position"].get("lon")
            if lat is not None and lon is not None:
                # Debug: Confirm coordinates
                print(f"🗺️ Centering map on coordinates: {lat}, {lon}")

                # Switch to map tab if not already visible
                self.show_map_tab()

                # Center the map on the device
                self.map_widget.set_position(lat, lon)

                # Set zoom level for close-up view of individual device
                self.map_widget.set_zoom(18)  # Higher zoom for better detail

                # Highlight the device on the map (optional - could add a special marker)
                model = device.get('model', 'Unknown')
                serial = device.get('serial', 'N/A')
                print(f"✅ Map successfully centered on {model} (Serial: {serial}) at {lat}, {lon}")

                # Ensure the marker is visible by refreshing the map view
                self.root.after(100, lambda: self._ensure_marker_visible(device))
            else:
                print(f"❌ Invalid coordinates for device: lat={lat}, lon={lon}")
        else:
            print(f"❌ No position data found for device: {device.get('model', 'Unknown')}")

    def on_closing(self):
        """Clean up resources when closing - enhanced for threading"""
        print("🧹 Cleaning up application resources...")

        # Stop queue processor
        self._queue_processor_running = False

        # Wait for any ongoing updates to complete
        if self.manager.is_updating:
            print("⏳ Waiting for ongoing update to complete...")
            # Give it a moment to finish
            self.root.after(1000, lambda: self._finish_cleanup())
        else:
            self._finish_cleanup()

    def _finish_cleanup(self):
        """Complete the cleanup process"""
        try:
            self.video_player.cleanup()
        except:
            pass
        self.root.destroy()

    def show_map_tab(self):
        """Show the map tab"""
        self.video_player.get_frame().pack_forget()
        self.map_frame.pack(fill=tk.BOTH, expand=True)
        
        # Update tab button styles
        self.map_tab_btn.config(bg='#e0e0e0', relief=tk.SUNKEN)
        self.vlc_tab_btn.config(bg=self.button_bg, relief=tk.RAISED)
        
        # Stop video if it's playing
        if self.video_player.is_playing():
            self.video_player.stop_stream()

    def show_vlc_tab(self):
        """Show the VLC player tab"""
        self.map_frame.pack_forget()
        self.video_player.get_frame().pack(fill=tk.BOTH, expand=True)
        
        # Update tab button styles
        self.vlc_tab_btn.config(bg='#e0e0e0', relief=tk.SUNKEN)
        self.map_tab_btn.config(bg=self.button_bg, relief=tk.RAISED)
        
        # Set video window
        self.video_player.set_video_window()

    def schedule_auto_update(self):
        """Auto-update with improved timing and efficiency"""
        # Only auto-update if not currently updating and enough time has passed
        if not self.manager.is_updating:
            self.refresh_from_api()
        else:
            print("⏳ Skipping auto-update - update already in progress")

        # Schedule next update (using configurable interval for frequent updates)
        self.root.after(self.manager.update_interval * 1000, self.schedule_auto_update)

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
                
                # Mark as fetched and rebuild cache
                self.manager.devices_fetched = True
                self.manager._rebuild_cache()
                self.manager.save_cached_devices()
                
                messagebox.showinfo("Import Success", f"Equipment data imported from {filepath}")
                self.refresh_list()
                self.update_map()
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import CSV: {str(e)}")

    def refresh_from_api(self):
        """Refresh data from API - now uses threading to prevent UI blocking"""
        if not self.manager.devices_fetched:
            print("🚀 Performing initial device collection...")
        else:
            print("🔄 Updating device data...")

        # Start threaded update
        self.manager.fetch_equipment_from_api()

        # Start processing update queue if not already running
        if not hasattr(self, '_queue_processor_running'):
            self._queue_processor_running = False
        if not self._queue_processor_running:
            self._start_queue_processor()

    def _start_queue_processor(self):
        """Start processing the update queue on the main thread"""
        self._queue_processor_running = True
        self._process_update_queue()

    def _process_update_queue(self):
        """Process updates from the background thread on the main thread"""
        try:
            # Process all available updates
            while True:
                try:
                    update_type, data = self.manager.update_queue.get_nowait()
                    if update_type == 'update_ui':
                        # Perform UI updates on main thread
                        self.manager.check_for_alerts()
                        self.refresh_list()
                        self.update_map()
                        print("✅ UI updated with fresh device data")
                    elif update_type == 'error':
                        messagebox.showerror("Update Error", str(data))
                except queue.Empty:
                    break

        except Exception as e:
            print(f"❌ Error processing update queue: {e}")
        finally:
            # Schedule next check
            if self._queue_processor_running:
                self.root.after(100, self._process_update_queue)  # Check every 100ms

    def refresh_list(self):
        """Refresh the equipment listbox with individual devices - optimized"""
        if not self.manager.equipment:
            self.equipment_listbox.delete(0, tk.END)
            self.equipment_listbox.insert(tk.END, "No equipment data available")
            return

        print(f"📋 Refreshing equipment list with {len(self.manager.equipment)} devices")

        # Store current selection to restore it
        try:
            current_selection = self.equipment_listbox.curselection()
            selected_index = current_selection[0] - 1 if current_selection else -1  # Account for header
        except:
            selected_index = -1

        self.equipment_listbox.delete(0, tk.END)

        # Add header
        header_text = f"📋 All Equipment ({len(self.manager.equipment)} devices)"
        self.equipment_listbox.insert(0, header_text)
        self.equipment_listbox.itemconfig(0, {'bg': '#f0f0f0', 'fg': '#666666'})

        # Add devices more efficiently
        for i, device in enumerate(self.manager.equipment):
            model = device.get('model', 'Unknown')
            serial = device.get('serial', 'N/A')
            device_type = device.get('type', 'Unknown')
            battery = device.get('battery', 'N/A')
            online = device.get('online', False)

            # Create display text with icons (simplified)
            status_icon = "🟢" if online else "🔴"
            battery_icon = "🔋" if isinstance(battery, (int, float)) and battery > 50 else "🪫" if isinstance(battery, (int, float)) and battery > 20 else "🔌" if isinstance(battery, (int, float)) else ""

            display_text = f"{status_icon} {model} - {serial} {battery_icon}"

            self.equipment_listbox.insert(tk.END, display_text)

        # Restore selection if possible
        if selected_index >= 0 and selected_index < len(self.manager.equipment):
            self.equipment_listbox.selection_set(selected_index + 1)  # +1 for header
            self._highlight_selected_device(selected_index)

    def update_map(self):
        """Update map markers - optimized for performance"""
        if not self.manager.equipment:
            self.map_widget.delete_all_marker()
            return

        print(f"🗺️ Updating map with {len(self.manager.equipment)} devices")

        # Clear existing markers efficiently
        self.map_widget.delete_all_marker()
        self.device_markers = []

        # Collect valid positions
        valid_devices = []
        lats, lons = [], []

        for device in self.manager.equipment:
            if "position" in device and isinstance(device["position"], dict):
                lat = device["position"].get("lat")
                lon = device["position"].get("lon")
                if lat is not None and lon is not None:
                    valid_devices.append((device, lat, lon))
                    lats.append(lat)
                    lons.append(lon)

        if not valid_devices:
            print("⚠️ No devices with valid GPS coordinates found")
            return

        # Calculate center position efficiently
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        self.map_widget.set_position(center_lat, center_lon)

        # Set zoom level based on spread (simplified)
        if len(lats) > 1:
            lat_range = max(lats) - min(lats)
            lon_range = max(lons) - min(lons)
            max_range = max(lat_range, lon_range)
            if max_range < 0.01:
                zoom_level = 15
            elif max_range < 0.1:
                zoom_level = 12
            elif max_range < 1:
                zoom_level = 10
            else:
                zoom_level = 8
        else:
            zoom_level = 10

        self.map_widget.set_zoom(zoom_level)

        # Add markers efficiently
        for device, lat, lon in valid_devices:
            model = device.get('model', 'Unknown')
            serial = device.get('serial', 'N/A')
            online = device.get('online', False)

            # Simplified marker text
            marker_text = f"{model}\n{serial}"

            # Get marker config
            marker_config = self._get_marker_config(model, device.get('type', 'Unknown'), online, device.get('battery', 0))

            # Create marker
            marker = self.map_widget.set_marker(
                lat, lon,
                text=marker_text,
                marker_color_circle=marker_config['color'],
                marker_color_outside=marker_config['outline'],
                text_color=marker_config['text_color']
            )
            self.device_markers.append(marker)

        print(f"✅ Map updated with {len(valid_devices)} markers")

    def _get_marker_config(self, model, device_type, online, battery):
        """Get marker configuration based on device type and status"""
        # Base configuration with better visibility
        config = {
            'color': '#FF4444',      # Bright red for default
            'outline': '#CC0000',    # Dark red outline
            'text_color': '#FFFFFF', # White text
            'font_size': 12
        }

        # Customize based on device model/type with high-contrast colors
        model_lower = model.lower() if model else ''
        type_lower = device_type.lower() if device_type else ''

        # Camera/Surveillance devices - Bright teal
        if any(keyword in model_lower for keyword in ['camera', 'cam', 'surveil', 'security']):
            config.update({
                'color': '#00CED1',      # Bright turquoise
                'outline': '#008B8B',    # Dark cyan
                'text_color': '#000000'  # Black text for contrast
            })

        # GPS/Tracking devices - Bright blue
        elif any(keyword in model_lower for keyword in ['gps', 'tracker', 'location', 'be300']):
            config.update({
                'color': '#4169E1',      # Royal blue
                'outline': '#000080',    # Navy blue
                'text_color': '#FFFFFF'  # White text
            })

        # Sensor devices - Bright green
        elif any(keyword in model_lower for keyword in ['sensor', 'detector', 'monitor']):
            config.update({
                'color': '#32CD32',      # Lime green
                'outline': '#228B22',    # Forest green
                'text_color': '#000000'  # Black text for contrast
            })

        # Communication devices - Bright yellow
        elif any(keyword in model_lower for keyword in ['radio', 'comm', 'transmit']):
            config.update({
                'color': '#FFD700',      # Gold
                'outline': '#FFA500',    # Orange
                'text_color': '#000000'  # Black text for contrast
            })

        # Military/Specialized equipment - Bright purple
        elif any(keyword in model_lower for keyword in ['avenger', 'scorpion', 'snooper']):
            config.update({
                'color': '#9932CC',      # Dark orchid
                'outline': '#4B0082',    # Indigo
                'text_color': '#FFFFFF'  # White text
            })

        # Modify appearance based on online status
        if not online:
            # Offline devices - make them grey but still visible
            config['color'] = '#708090'  # Slate grey
            config['outline'] = '#2F4F4F'  # Dark slate grey
            config['text_color'] = '#FFFFFF'  # White text

        return config

    def _adjust_color_brightness(self, hex_color, factor):
        """Adjust color brightness by factor (0.0 = black, 1.0 = original, 2.0 = brighter)"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Adjust brightness
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))

        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    def _highlight_selected_device(self, device_index):
        """Highlight the selected device in the listbox"""
        # Clear previous selection styling
        for i in range(self.equipment_listbox.size()):
            if i == 0:  # Header row
                self.equipment_listbox.itemconfig(i, {'bg': '#f0f0f0', 'fg': '#666666'})
            else:
                self.equipment_listbox.itemconfig(i, {'bg': self.equipment_listbox.cget('bg'), 'fg': self.equipment_listbox.cget('fg')})

        # Highlight the selected device (accounting for header row)
        if device_index >= 0:
            actual_index = device_index + 1  # +1 because index 0 is the header
            if actual_index < self.equipment_listbox.size():
                self.equipment_listbox.itemconfig(actual_index, {'bg': '#e3f2fd', 'fg': '#1976d2'})  # Light blue highlight

                # Update the status label with selected device info
                if device_index < len(self.manager.equipment):
                    device = self.manager.equipment[device_index]
                    model = device.get('model', 'Unknown')
                    serial = device.get('serial', 'N/A')
                    position = device.get('position', {})
                    lat = position.get('lat', 'N/A') if isinstance(position, dict) else 'N/A'
                    lon = position.get('lon', 'N/A') if isinstance(position, dict) else 'N/A'
                    battery = device.get('battery', 'N/A')
                    online = "ONLINE" if device.get('online', False) else "OFFLINE"

                    status_text = f"📍 Selected: {model} ({serial}) | 📊 {lat}, {lon} | 🔋 {battery}% | 📡 {online}"
                    self.selected_device_label.config(text=status_text, fg='#1976d2')
                    print(f"🏷️ Status label updated: {status_text}")
                else:
                    self.selected_device_label.config(text="Invalid device selection", fg='#ff4444')
        else:
            self.selected_device_label.config(text="No device selected", fg='#666666')

    def _ensure_marker_visible(self, device):
        """Ensure the selected device's marker is visible on the map"""
        if "position" in device and isinstance(device["position"], dict):
            lat = device["position"].get("lat")
            lon = device["position"].get("lon")
            if lat is not None and lon is not None:
                # Force a map refresh to ensure marker is rendered
                self.map_widget.set_position(lat, lon)
                self.map_widget.set_zoom(18)

                # Add a small delay to ensure rendering is complete
                self.root.after(200, self._add_selection_indicator)

    def _add_selection_indicator(self):
        """Add a temporary visual indicator for the selected marker"""
        # This could be enhanced to add a pulsing effect or special marker
        # For now, we'll just ensure the map is properly updated
        pass

    def add_entry(self):
        # Prompt for new values with validation loop
        while True:
            name = self.ask_string(self.root, "Add Equipment", "Type:")
            if name is None:  # Cancelled
                return
            
            # Validate device type
            valid, error_msg = utils.Regex.validate_device_identifier(name)
            if not valid:
                messagebox.showerror("Invalid Input", f"Type: {error_msg}")
                continue  # Ask again
            break
        
        while True:
            model = self.ask_string(self.root, "Add Equipment", "Model:")
            if model is None:  # Cancelled
                return
            
            # Validate model
            valid, error_msg = utils.Regex.validate_device_identifier(model)
            if not valid:
                messagebox.showerror("Invalid Input", f"Model: {error_msg}")
                continue  # Ask again
            break
        
        while True:
            serial = self.ask_string(self.root, "Add Equipment", "Serial:")
            if serial is None:  # Cancelled
                return
            
            # Validate serial
            valid, error_msg = utils.Regex.validate_device_identifier(serial)
            if not valid:
                messagebox.showerror("Invalid Input", f"Serial: {error_msg}")
                continue  # Ask again
            break
        
        while True:
            lat, cancelled = self.ask_float(self.root, "Add Equipment", "Latitude:")
            if cancelled:  # User clicked Cancel
                return
            
            if lat is None:  # Invalid input (not a number)
                messagebox.showerror("Invalid Input", "Latitude must be a valid number")
                continue  # Ask again
            
            # Validate latitude range
            valid, error_msg = utils.Regex.validate_latitude(lat)
            if not valid:
                messagebox.showerror("Invalid Input", f"Latitude: {error_msg}")
                continue  # Ask again
            break
        
        while True:
            lon, cancelled = self.ask_float(self.root, "Add Equipment", "Longitude:")
            if cancelled:  # User clicked Cancel
                return
            
            if lon is None:  # Invalid input (not a number)
                messagebox.showerror("Invalid Input", "Longitude must be a valid number")
                continue  # Ask again
            
            # Validate longitude range
            valid, error_msg = utils.Regex.validate_longitude(lon)
            if not valid:
                messagebox.showerror("Invalid Input", f"Longitude: {error_msg}")
                continue  # Ask again
            break
        
        while True:
            battery, cancelled = self.ask_integer(self.root, "Add Equipment", "Battery Level (%):")
            if cancelled:  # User clicked Cancel
                return
            
            if battery is None:  # Invalid input (not a number)
                messagebox.showerror("Invalid Input", "Battery level must be a valid whole number")
                continue  # Ask again
            
            # Validate battery range
            valid, error_msg = utils.Regex.validate_battery(battery)
            if not valid:
                messagebox.showerror("Invalid Input", f"Battery: {error_msg}")
                continue  # Ask again
            break
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
        """Update the currently selected device"""
        if not self.manager.equipment:
            messagebox.showinfo("No Device", "No equipment data available.")
            return

        # Get the currently selected device index
        try:
            selection = self.equipment_listbox.curselection()
            if not selection:
                messagebox.showinfo("No Selection", "Please select a device from the list to update.")
                return

            # Account for header row (index 0 is header, so actual device index is selection[0] - 1)
            listbox_index = selection[0]
            if listbox_index == 0:
                messagebox.showinfo("Invalid Selection", "Please select a device (not the header).")
                return

            device_index = listbox_index - 1  # Subtract 1 for header

            if device_index < 0 or device_index >= len(self.manager.equipment):
                messagebox.showerror("Error", "Invalid device selection.")
                return

        except Exception as e:
            messagebox.showerror("Error", f"Failed to get device selection: {str(e)}")
            return

        # Get the selected device
        eq = self.manager.equipment[device_index]

        # Get current values
        current_type = eq.get('type', '')
        current_model = eq.get('model', '')
        current_serial = eq.get('serial', '')
        current_pos = eq.get('position', {})
        current_lat = current_pos.get('lat', 0) if isinstance(current_pos, dict) else 0
        current_lon = current_pos.get('lon', 0) if isinstance(current_pos, dict) else 0
        current_battery = eq.get('battery', 0)

        # Prompt for new values with validation loops
        while True:
            name = self.ask_string(self.root, "Update Equipment", "Type:", current_type)
            if name is None:  # Cancelled
                return
            
            # Validate device type
            valid, error_msg = utils.Regex.validate_device_identifier(name)
            if not valid:
                messagebox.showerror("Invalid Input", f"Type: {error_msg}")
                continue  # Ask again
            break
        
        while True:
            model = self.ask_string(self.root, "Update Equipment", "Model:", current_model)
            if model is None:  # Cancelled
                return
            
            # Validate model
            valid, error_msg = utils.Regex.validate_device_identifier(model)
            if not valid:
                messagebox.showerror("Invalid Input", f"Model: {error_msg}")
                continue  # Ask again
            break
        
        while True:
            serial = self.ask_string(self.root, "Update Equipment", "Serial:", current_serial)
            if serial is None:  # Cancelled
                return
            
            # Validate serial
            valid, error_msg = utils.Regex.validate_device_identifier(serial)
            if not valid:
                messagebox.showerror("Invalid Input", f"Serial: {error_msg}")
                continue  # Ask again
            break
        
        while True:
            lat, cancelled = self.ask_float(self.root, "Update Equipment", "Latitude:", current_lat)
            if cancelled:  # User clicked Cancel
                return
            
            if lat is None:  # Invalid input (not a number)
                messagebox.showerror("Invalid Input", "Latitude must be a valid number")
                continue  # Ask again
            
            # Validate latitude range
            valid, error_msg = utils.Regex.validate_latitude(lat)
            if not valid:
                messagebox.showerror("Invalid Input", f"Latitude: {error_msg}")
                continue  # Ask again
            break
        
        while True:
            lon, cancelled = self.ask_float(self.root, "Update Equipment", "Longitude:", current_lon)
            if cancelled:  # User clicked Cancel
                return
            
            if lon is None:  # Invalid input (not a number)
                messagebox.showerror("Invalid Input", "Longitude must be a valid number")
                continue  # Ask again
            
            # Validate longitude range
            valid, error_msg = utils.Regex.validate_longitude(lon)
            if not valid:
                messagebox.showerror("Invalid Input", f"Longitude: {error_msg}")
                continue  # Ask again
            break
        
        while True:
            battery, cancelled = self.ask_integer(self.root, "Update Equipment", "Battery Level (%):", current_battery)
            if cancelled:  # User clicked Cancel
                return
            
            if battery is None:  # Invalid input (not a number)
                messagebox.showerror("Invalid Input", "Battery level must be a valid whole number")
                continue  # Ask again
            
            # Validate battery range
            valid, error_msg = utils.Regex.validate_battery(battery)
            if not valid:
                messagebox.showerror("Invalid Input", f"Battery: {error_msg}")
                continue  # Ask again
            break

        # Update the equipment
        eq['type'] = name
        eq['model'] = model
        eq['serial'] = serial
        eq['position'] = {"lat": lat, "lon": lon}
        eq['battery'] = battery

        # Update cache if serial/model changed
        old_serial = current_serial
        old_model = current_model
        if old_serial != serial or old_model != model:
            # Remove old cache entry
            old_key = f"{old_serial}_{old_model}"
            if old_key in self.manager.device_cache:
                del self.manager.device_cache[old_key]

            # Add new cache entry
            new_key = f"{serial}_{model}"
            self.manager.device_cache[new_key] = eq

        # Save updated cache
        self.manager.save_cached_devices()

        # Refresh UI
        self.refresh_list()
        self.update_map()

        # Update selection and highlight
        self.equipment_listbox.selection_set(listbox_index)
        self._highlight_selected_device(device_index)

        # Update device details panel if it's open and showing the updated device
        if self.details_panel_visible and hasattr(self, 'current_details_device_index'):
            if self.current_details_device_index == device_index:
                # Show a brief "updating" message in the details panel
                if hasattr(self, 'details_frame'):
                    # Find the title label and temporarily update it
                    for widget in self.details_frame.winfo_children():
                        if isinstance(widget, tk.Frame):  # Main frame
                            for subwidget in widget.winfo_children():
                                if isinstance(subwidget, tk.Frame):  # Header frame
                                    for label in subwidget.winfo_children():
                                        if isinstance(label, tk.Label) and "Device Details" in str(label.cget("text")):
                                            original_text = label.cget("text")
                                            label.config(text="🔄 Updating Device Details...")
                                            # Restore after a brief delay
                                            self.root.after(200, lambda: label.config(text=original_text))
                                            break
                                    break
                            break

                # Add a small delay to ensure UI updates are complete
                self.root.after(100, lambda: self.show_device_details(device_index))
                print(f"🔄 Device details panel updated for {model} ({serial})")

        messagebox.showinfo("Update Successful", f"Device {model} ({serial}) has been updated successfully!")

        print(f"✅ Device updated: {model} (Serial: {serial}) at index {device_index}")

    def delete_entry(self):
        """Delete the currently selected device"""
        if not self.manager.equipment:
            messagebox.showinfo("No Device", "No equipment data available.")
            return

        # Get the currently selected device index
        try:
            selection = self.equipment_listbox.curselection()
            if not selection:
                messagebox.showinfo("No Selection", "Please select a device from the list to delete.")
                return

            # Account for header row (index 0 is header, so actual device index is selection[0] - 1)
            listbox_index = selection[0]
            if listbox_index == 0:
                messagebox.showinfo("Invalid Selection", "Please select a device (not the header).")
                return

            device_index = listbox_index - 1  # Subtract 1 for header

            if device_index < 0 or device_index >= len(self.manager.equipment):
                messagebox.showerror("Error", "Invalid device selection.")
                return

        except Exception as e:
            messagebox.showerror("Error", f"Failed to get device selection: {str(e)}")
            return

        # Get device info for confirmation
        device = self.manager.equipment[device_index]
        model = device.get('model', 'Unknown')
        serial = device.get('serial', 'N/A')

        # Confirm deletion
        confirm = messagebox.askyesno("Delete Equipment",
            f"Are you sure you want to delete this device?\n\n"
            f"Model: {model}\n"
            f"Serial: {serial}\n\n"
            f"This action cannot be undone.")

        if not confirm:
            return

        # Remove from cache first
        device_key = f"{serial}_{model}"
        if device_key in self.manager.device_cache:
            del self.manager.device_cache[device_key]

        # Remove from equipment list
        del self.manager.equipment[device_index]

        # Save updated cache
        self.manager.save_cached_devices()

        # Refresh UI
        self.refresh_list()
        self.update_map()

        # Hide device details if they were showing the deleted device
        if self.details_panel_visible:
            self.hide_device_details()

        messagebox.showinfo("Deletion Successful", f"Device {model} ({serial}) has been deleted successfully!")

        print(f"🗑️ Device deleted: {model} (Serial: {serial}) at index {device_index}")

    def view_live_feed(self):
        """View live feed for the selected device"""
        if not self.manager.equipment:
            messagebox.showinfo("No Device", "No equipment data available.")
            return

        # Get the currently selected device
        try:
            selection = self.equipment_listbox.curselection()
            if not selection:
                messagebox.showinfo("No Selection", "Please select a device from the list to view its live feed.")
                return

            # Account for header row
            listbox_index = selection[0]
            if listbox_index == 0:
                messagebox.showinfo("Invalid Selection", "Please select a device (not the header).")
                return

            device_index = listbox_index - 1  # Subtract 1 for header

            if device_index < 0 or device_index >= len(self.manager.equipment):
                messagebox.showerror("Error", "Invalid device selection.")
                return

            device = self.manager.equipment[device_index]
            model = device.get('model', 'Unknown')
            serial = device.get('serial', 'N/A')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to get device selection: {str(e)}")
            return

        # Use RTSP stream URL (could be made device-specific in the future)
        stream_url = "rtsp://192.168.8.185:8554/cam"

        if stream_url:
            try:
                print(f"Loading RTSP stream for device {model} ({serial}): {stream_url}")

                # Switch to VLC tab
                self.show_vlc_tab()

                # Play the stream using VideoPlayer
                success = self.video_player.play_stream(stream_url)

                if not success:
                    # Fallback to external player if VideoPlayer fails
                    self.video_player.fallback_external_player(stream_url)

            except Exception as e:
                print(f"VideoPlayer Error for {model} ({serial}): {e}")
                messagebox.showerror("Video Error",
                    f"Failed to load RTSP stream for {model} ({serial}): {str(e)}\n\n"
                    "This might be due to video driver issues.\n"
                    "Try updating your graphics drivers or restarting the application.")
                # Fallback to external player
                self.video_player.fallback_external_player(stream_url)
        else:
            messagebox.showerror("No Stream Available", f"No RTSP stream configured for {model} ({serial}).")

    def clear_cache(self):
        """Clear the device cache and force fresh fetch"""
        confirm = messagebox.askyesno("Clear Cache", 
            "This will clear the cached device data and force a fresh fetch from the API.\n\nContinue?")
        if confirm:
            try:
                if os.path.exists(constants.CACHE_FILE):
                    os.remove(constants.CACHE_FILE)
                    print("🗑️ Cache file deleted")
                
                # Reset manager state
                self.manager.equipment = []
                self.manager.devices_fetched = False
                self.manager.device_cache = {}
                self.manager.previous_equipment = []
                
                # Force fresh fetch
                self.refresh_from_api()
                
                messagebox.showinfo("Cache Cleared", "Device cache has been cleared. Fresh data fetched from API.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear cache: {str(e)}")

    def configure_performance(self):
        """Configure performance settings for device updates"""
        # Create performance settings dialog
        perf_window = tk.Toplevel(self.root)
        perf_window.title("Performance Settings")
        perf_window.geometry("380x260")
        perf_window.resizable(False, False)
        perf_window.transient(self.root)
        perf_window.grab_set()

        # Center the dialog
        x = self.root.winfo_rootx() + 50
        y = self.root.winfo_rooty() + 50
        perf_window.geometry(f"+{x}+{y}")

        # Title
        title_label = tk.Label(perf_window, text="⚡ Performance Settings", font=("Segoe UI", 12, "bold"))
        title_label.pack(pady=15)

        # Current settings display
        current_frame = tk.Frame(perf_window)
        current_frame.pack(pady=8)

        tk.Label(current_frame, text="Current Settings:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(current_frame, text=f"Update Interval: {self.manager.update_interval} seconds").pack(anchor="w")
        tk.Label(current_frame, text=f"Max API Requests: {self.manager.max_api_requests}").pack(anchor="w")

        # Update interval setting
        interval_frame = tk.Frame(perf_window)
        interval_frame.pack(pady=8)

        tk.Label(interval_frame, text="Update Interval (seconds):", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        interval_var = tk.StringVar(value=str(self.manager.update_interval))
        interval_entry = tk.Entry(interval_frame, textvariable=interval_var, width=8)
        interval_entry.pack(side=tk.LEFT, padx=8)

        # Max requests setting
        requests_frame = tk.Frame(perf_window)
        requests_frame.pack(pady=8)

        tk.Label(requests_frame, text="Max API Requests:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        requests_var = tk.StringVar(value=str(self.manager.max_api_requests))
        requests_entry = tk.Entry(requests_frame, textvariable=requests_var, width=8)
        requests_entry.pack(side=tk.LEFT, padx=8)

        # Buttons
        button_frame = tk.Frame(perf_window)
        button_frame.pack(pady=15)

        def apply_settings():
            try:
                new_interval = int(interval_var.get())
                new_requests = int(requests_var.get())

                if new_interval < 10:
                    messagebox.showerror("Invalid Setting", "Update interval must be at least 10 seconds")
                    return
                if new_requests < 1 or new_requests > 50:
                    messagebox.showerror("Invalid Setting", "Max API requests must be between 1 and 50")
                    return

                self.manager.update_interval = new_interval
                self.manager.max_api_requests = new_requests

                messagebox.showinfo("Settings Applied",
                    f"Performance settings updated:\n"
                    f"• Update Interval: {new_interval} seconds\n"
                    f"• Max API Requests: {new_requests}")
                perf_window.destroy()

            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers")

        tk.Button(button_frame, text="Apply", command=apply_settings, width=8).pack(side=tk.LEFT, padx=8)
        tk.Button(button_frame, text="Cancel", command=perf_window.destroy, width=8).pack(side=tk.LEFT, padx=8)

        # Performance tips
        tips_label = tk.Label(perf_window, text=
            "💡 Performance Tips:\n"
            "• Higher interval = less frequent updates, better performance\n"
            "• Lower requests = faster initial load, fewer devices found\n"
            "• Recommended: 10-30 seconds interval for real-time updates\n"
            "• Current default: 10 seconds for frequent updates",
            font=("Segoe UI", 8), fg="#666666", justify="left")
        tips_label.pack(pady=8)

    def export_to_csv(self):
        """Export current device data to CSV file - ensures fresh API data"""
        # Show progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Exporting Data")
        progress_window.geometry("300x120")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()

        # Center the dialog
        x = self.root.winfo_rootx() + 50
        y = self.root.winfo_rooty() + 50
        progress_window.geometry(f"+{x}+{y}")

        # Progress message
        progress_label = tk.Label(progress_window, text="🔄 Fetching fresh data from API...",
                                font=("Segoe UI", 10))
        progress_label.pack(pady=20)

        # Status label
        status_label = tk.Label(progress_window, text="Please wait...",
                              font=("Segoe UI", 9), fg="#666666")
        status_label.pack(pady=(0, 20))

        # Flag to track if window was destroyed
        window_destroyed = False

        def safe_update_labels(progress_text, status_text):
            """Safely update labels if window still exists"""
            nonlocal window_destroyed
            if not window_destroyed and progress_window.winfo_exists():
                try:
                    progress_label.config(text=progress_text)
                    status_label.config(text=status_text)
                except tk.TclError:
                    window_destroyed = True

        def perform_export():
            nonlocal window_destroyed
            try:
                # Force fresh API fetch
                print("📊 Export: Starting fresh API fetch...")
                safe_update_labels("🔄 Fetching fresh data from API...", "Fetching data from API...")

                # Reset fetch flag to force fresh collection
                self.manager.devices_fetched = False
                self.manager.equipment = []

                # Start fresh fetch
                self.manager.fetch_equipment_from_api()

                # Wait for completion (with timeout)
                timeout = 30  # 30 seconds timeout
                start_time = time.time()

                while not self.manager.devices_fetched and (time.time() - start_time) < timeout:
                    if window_destroyed or not progress_window.winfo_exists():
                        print("📊 Export cancelled - progress window closed")
                        return

                    self.root.update()  # Allow UI to update
                    time.sleep(0.1)  # Small delay to prevent busy waiting

                    # Check if we have data
                    if self.manager.equipment:
                        break

                if window_destroyed or not progress_window.winfo_exists():
                    print("📊 Export cancelled - progress window closed")
                    return

                if not self.manager.equipment:
                    if not window_destroyed and progress_window.winfo_exists():
                        progress_window.destroy()
                    messagebox.showerror("Export Error", "Failed to fetch fresh data from API.\nPlease check your internet connection and try again.")
                    return

                # Update progress
                safe_update_labels("📊 Preparing CSV export...", f"Exporting {len(self.manager.equipment)} devices...")

                # Create default filename with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                default_filename = f"equipment_export_{timestamp}.csv"

                filepath = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")],
                    initialfile=default_filename
                )

                if filepath:
                    # Export fresh data
                    df = pd.DataFrame(self.manager.equipment)
                    df.to_csv(filepath, index=False)

                    if not window_destroyed and progress_window.winfo_exists():
                        progress_window.destroy()
                    messagebox.showinfo("Export Success",
                                      f"✅ Fresh data exported successfully!\n\n"
                                      f"📊 {len(self.manager.equipment)} devices exported\n"
                                      f"📁 Saved to: {filepath}\n\n"
                                      f"Data was fetched fresh from API at {timestamp}")

                    print(f"✅ CSV export completed: {len(self.manager.equipment)} devices to {filepath}")
                else:
                    if not window_destroyed and progress_window.winfo_exists():
                        progress_window.destroy()
                    print("📊 CSV export cancelled by user")

            except Exception as e:
                if not window_destroyed and progress_window.winfo_exists():
                    progress_window.destroy()
                messagebox.showerror("Export Error", f"Failed to export CSV: {str(e)}")
                print(f"❌ CSV export error: {e}")

        # Handle window close event
        def on_window_close():
            nonlocal window_destroyed
            window_destroyed = True
            progress_window.destroy()

        progress_window.protocol("WM_DELETE_WINDOW", on_window_close)

        # Start export in background to keep UI responsive
        self.root.after(100, perform_export)