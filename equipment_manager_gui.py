import tkinter as tk
import equipment_manager as eqm
import equipment_app as eqa



if __name__ == "__main__":
    manager = eqm.EquipmentManager()
    
    # Try to load cached devices first
    if not manager.load_cached_devices():
        print("📡 No cache found, will fetch from API on startup")
    
    root = tk.Tk()
    app = eqa.EquipmentApp(root, manager)
    # Start the auto-update process
    app.schedule_auto_update()
    root.mainloop()
