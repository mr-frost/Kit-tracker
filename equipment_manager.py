import constants
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import requests
import pandas as pd
from tkintermapview import TkinterMapView
from video import VideoPlayer
import os
import datetime
import json
import threading
import queue
import time
import constants




class EquipmentManager:
    def __init__(self):
        self.equipment = []  # List of dicts
        self.previous_equipment = []  # For tracking changes
        self.devices_fetched = False  # Flag to track if initial fetch is complete
        self.device_cache = {}  # Cache for quick device lookup by serial+model

        # Performance optimization attributes
        self.update_queue = queue.Queue()  # Thread-safe queue for updates
        self.is_updating = False  # Flag to prevent concurrent updates
        self.last_update_time = 0  # Track last update timestamp
        self.update_interval = 10  # Minimum seconds between updates (reduced from 60 for more frequent updates)
        self.max_api_requests = 20  # Reduced from 100 to prevent overwhelming the API

    def load_cached_devices(self):
        """Load devices from cache file if it exists"""
        if os.path.exists(constants.CACHE_FILE):
            try:
                with open(constants.CACHE_FILE, 'r') as f:
                    cached_data = json.load(f)
                    self.equipment = cached_data.get('devices', [])
                    self.devices_fetched = cached_data.get('fetched', False)
                    self.device_cache = cached_data.get('cache', {})

                    if self.equipment:
                        print(f"📂 Loaded {len(self.equipment)} devices from cache")
                        # Rebuild cache if needed
                        if not self.device_cache:
                            self._rebuild_cache()
                        return True
            except Exception as e:
                print(f"⚠️ Error loading cache: {e}")
        return False

    def save_cached_devices(self):
        """Save current devices to cache file"""
        try:
            cache_data = {
                'devices': self.equipment,
                'fetched': self.devices_fetched,
                'cache': self.device_cache,
                'timestamp': datetime.datetime.now().isoformat()
            }
            with open(constants.CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
            print(f"💾 Saved {len(self.equipment)} devices to cache")
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")

    def _rebuild_cache(self):
        """Rebuild the device cache for quick lookups"""
        self.device_cache = {}
        for device in self.equipment:
            serial = device.get('serial', f'NO_SERIAL_{len(self.device_cache)}')
            model = device.get('model', 'Unknown')
            device_identifier = f"{serial}_{model}"
            self.device_cache[device_identifier] = device

    def fetch_equipment_from_api(self):
        """Smart fetching: collect all devices once, then update existing ones (now threaded)"""
        # Prevent concurrent updates
        if self.is_updating:
            print("⚠️ Update already in progress, skipping...")
            return

        # Check if enough time has passed since last update
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            remaining_time = int(self.update_interval - (current_time - self.last_update_time))
            print(f"⏳ Too soon for update. Wait {remaining_time} seconds...")
            return

        self.is_updating = True
        self.last_update_time = current_time

        print(f"Fetching equipment data from API with token: {constants.API_TOKEN[:10]}...")

        # Start the fetch in a background thread
        fetch_thread = threading.Thread(target=self._threaded_fetch_equipment, daemon=True)
        fetch_thread.start()

    def _threaded_fetch_equipment(self):
        """Threaded version of equipment fetching to prevent UI blocking"""
        try:
            if not self.devices_fetched:
                # First time - collect all devices
                success = self._fetch_all_devices()
            else:
                # Subsequent calls - update existing devices
                success = self._update_existing_devices()

            if success:
                # Queue UI updates to run on main thread
                self.update_queue.put(('update_ui', None))
            else:
                print("❌ Equipment fetch failed")

        except Exception as e:
            print(f"❌ Threaded fetch error: {e}")
        finally:
            self.is_updating = False

    def _fetch_all_devices(self):
        """Fetch all unique devices from API (one-time operation) - enhanced with cache sync"""
        print("🔄 Performing initial device collection...")

        # Start with existing cached devices to preserve them during initial fetch
        existing_cache = self.device_cache.copy() if self.device_cache else {}
        temp_equipment = []  # Work with temporary list
        unique_devices = {}  # Track devices by serial+model combination
        found_cached_devices = set()  # Track which cached devices we found

        # Make multiple requests to collect all available devices
        max_requests = self.max_api_requests
        consecutive_duplicates = 0
        max_consecutive_duplicates = 5
        request_count = 0

        try:
            while request_count < max_requests and consecutive_duplicates < max_consecutive_duplicates:
                request_count += 1
                response = requests.get(constants.API_URL, headers=constants.HEADERS, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        serial = data.get('serial', f'NO_SERIAL_{request_count}')
                        model = data.get('model', 'Unknown')

                        # Create a unique identifier for each device
                        device_identifier = f"{serial}_{model}"

                        if device_identifier not in unique_devices:
                            unique_devices[device_identifier] = data
                            temp_equipment.append(data)
                            consecutive_duplicates = 0

                            # Check if this device was in our existing cache
                            if device_identifier in existing_cache:
                                found_cached_devices.add(device_identifier)
                                print(f"[{request_count}] Found cached device: {model} (Serial: {serial})")
                            else:
                                print(f"[{request_count}] Added new device: {model} (Serial: {serial})")

                    elif isinstance(data, list):
                        # If we get a list, add all devices
                        for device in data:
                            if isinstance(device, dict):
                                serial = device.get('serial', f'NO_SERIAL_LIST_{len(temp_equipment)}')
                                model = device.get('model', 'Unknown')
                                device_identifier = f"{serial}_{model}"

                                if device_identifier not in unique_devices:
                                    unique_devices[device_identifier] = device
                                    temp_equipment.append(device)

                                    # Check if this device was in our existing cache
                                    if device_identifier in existing_cache:
                                        found_cached_devices.add(device_identifier)
                                        print(f"Added cached device from list: {model} (Serial: {serial})")
                                    else:
                                        print(f"Added new device from list: {model} (Serial: {serial})")
                        break  # If we get a list, we're done
                else:
                    print(f"API Error on request {request_count}: {response.status_code} - {response.text}")
                    break

            # Preserve cached devices that weren't found in this fetch
            # (they might be temporarily unavailable but should be kept)
            preserved_count = 0
            for device_id, device_data in existing_cache.items():
                if device_id not in found_cached_devices:
                    # Only preserve if we don't already have this device from the API
                    if device_id not in unique_devices:
                        unique_devices[device_id] = device_data
                        temp_equipment.append(device_data)
                        preserved_count += 1
                        print(f"💾 Preserved cached device: {device_data.get('model', 'Unknown')} (Serial: {device_data.get('serial', 'N/A')})")

            # Update equipment list atomically
            self.equipment = temp_equipment
            self.devices_fetched = True
            self.device_cache = unique_devices
            self.save_cached_devices()

            print(f"\n=== INITIAL COLLECTION COMPLETE ===")
            print(f"Total API requests made: {request_count}")
            print(f"Total unique devices collected: {len(self.equipment)}")
            print(f"New devices found: {len(unique_devices) - preserved_count}")
            print(f"Cached devices preserved: {preserved_count}")

            return True

        except Exception as e:
            print(f"❌ Error in _fetch_all_devices: {e}")
            return False

    def _update_existing_devices(self):
        """Update existing devices with fresh data from API - comprehensive update"""
        print("🔄 Updating existing devices...")

        if not self.device_cache:
            print("⚠️ No cached devices to update")
            return True

        # Track which devices have been updated
        updated_devices = set()
        devices_to_update = set(self.device_cache.keys())
        total_cached_devices = len(devices_to_update)

        print(f"📊 Need to update {total_cached_devices} cached devices")

        # Make requests until we've checked all cached devices or hit limits
        max_requests = min(self.max_api_requests * 2, total_cached_devices * 3)  # More requests for comprehensive update
        request_count = 0
        consecutive_no_updates = 0
        max_consecutive_no_updates = 5  # Stop if we get no updates for several requests

        try:
            while (request_count < max_requests and
                   updated_devices != devices_to_update and
                   consecutive_no_updates < max_consecutive_no_updates):

                request_count += 1
                response = requests.get(constants.API_URL, headers=constants.HEADERS, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    request_updated_count = 0

                    if isinstance(data, dict):
                        # Handle single device response
                        serial = data.get('serial', f'NO_SERIAL_{request_count}')
                        model = data.get('model', 'Unknown')
                        device_identifier = f"{serial}_{model}"

                        if device_identifier in devices_to_update:
                            # Update existing device if found in cache
                            self._update_single_device(device_identifier, data)
                            updated_devices.add(device_identifier)
                            request_updated_count += 1
                            consecutive_no_updates = 0

                            # Log significant changes
                            self._log_device_changes(device_identifier, data)
                        else:
                            # Check if device already exists in equipment list (prevent duplicates)
                            device_already_exists = False
                            for existing_device in self.equipment:
                                if (existing_device.get('serial') == serial and
                                    existing_device.get('model') == model):
                                    device_already_exists = True
                                    print(f"⚠️ Skipping duplicate device: {model} (Serial: {serial}) - already in equipment list")
                                    break

                            if not device_already_exists:
                                # NEW DEVICE: Add to both equipment list and cache
                                print(f"🆕 Found new device in API: {model} (Serial: {serial})")
                                data['last_seen'] = time.time()  # Add timestamp

                                # Add to equipment list
                                self.equipment.append(data)

                                # Add to cache
                                self.device_cache[device_identifier] = data

                                # Mark as updated (even though it's new)
                                updated_devices.add(device_identifier)
                                request_updated_count += 1
                                consecutive_no_updates = 0

                                print(f"✅ Added new device: {model} (Serial: {serial}) to app and cache")

                    elif isinstance(data, list):
                        # Handle list response - check all devices in the list
                        for device_data in data:
                            if isinstance(device_data, dict):
                                serial = device_data.get('serial', f'NO_SERIAL_LIST_{request_count}')
                                model = device_data.get('model', 'Unknown')
                                device_identifier = f"{serial}_{model}"

                                if device_identifier in devices_to_update:
                                    self._update_single_device(device_identifier, device_data)
                                    updated_devices.add(device_identifier)
                                    request_updated_count += 1
                                else:
                                    # Check if device already exists in equipment list (prevent duplicates)
                                    device_already_exists = False
                                    for existing_device in self.equipment:
                                        if (existing_device.get('serial') == serial and
                                            existing_device.get('model') == model):
                                            device_already_exists = True
                                            print(f"⚠️ Skipping duplicate device from list: {model} (Serial: {serial}) - already in equipment list")
                                            break

                                    if not device_already_exists:
                                        # NEW DEVICE: Add to both equipment list and cache
                                        print(f"🆕 Found new device in API list: {model} (Serial: {serial})")
                                        device_data['last_seen'] = time.time()  # Add timestamp

                                        # Add to equipment list
                                        self.equipment.append(device_data)

                                        # Add to cache
                                        self.device_cache[device_identifier] = device_data

                                        # Mark as updated (even though it's new)
                                        updated_devices.add(device_identifier)
                                        request_updated_count += 1

                                        print(f"✅ Added new device from list: {model} (Serial: {serial}) to app and cache")

                        if request_updated_count > 0:
                            consecutive_no_updates = 0
                        else:
                            consecutive_no_updates += 1

                    else:
                        consecutive_no_updates += 1

                    if request_count % 5 == 0:  # Progress update every 5 requests
                        progress = len(updated_devices) / total_cached_devices * 100
                        print(f"� Update progress: {len(updated_devices)}/{total_cached_devices} devices ({progress:.1f}%) - Request {request_count}")

                else:
                    print(f"API Error on update request {request_count}: {response.status_code}")
                    consecutive_no_updates += 1

            # Final status report
            final_progress = len(updated_devices) / total_cached_devices * 100 if total_cached_devices > 0 else 100
            new_devices_added = len(updated_devices) - len(devices_to_update & updated_devices)
            print(f"✅ Update completed: {len(updated_devices)}/{total_cached_devices} devices processed ({final_progress:.1f}%) from {request_count} API requests")
            if new_devices_added > 0:
                print(f"🆕 Added {new_devices_added} new devices to app and cache")

            # Handle devices that weren't found in API responses
            missing_devices = devices_to_update - updated_devices
            if missing_devices:
                print(f"⚠️ {len(missing_devices)} devices not found in API responses:")
                for device_id in list(missing_devices)[:5]:  # Show first 5
                    print(f"   - {device_id}")
                if len(missing_devices) > 5:
                    print(f"   ... and {len(missing_devices) - 5} more")

                # Optionally mark missing devices as offline
                self._handle_missing_devices(missing_devices)

            # Save updated cache
            self.save_cached_devices()

            return True

        except Exception as e:
            print(f"❌ Error in _update_existing_devices: {e}")
            return False

    def _update_single_device(self, device_identifier, new_data):
        """Update a single device in both equipment list and cache"""
        # Add/update last_seen timestamp
        new_data['last_seen'] = time.time()

        # Find the device in our equipment list and update it
        for i, device in enumerate(self.equipment):
            if (device.get('serial') == new_data.get('serial') and
                device.get('model') == new_data.get('model')):
                # Update the device with fresh data
                self.equipment[i] = new_data
                self.device_cache[device_identifier] = new_data
                break

    def _log_device_changes(self, device_identifier, new_data):
        """Log significant changes in device status"""
        if device_identifier in self.device_cache:
            old_data = self.device_cache[device_identifier]

            # Check for significant changes
            old_online = old_data.get('online', False)
            new_online = new_data.get('online', False)

            if old_online != new_online:
                model = new_data.get('model', 'Unknown')
                serial = new_data.get('serial', 'N/A')
                status = 'ONLINE' if new_online else 'OFFLINE'
                print(f"📡 {model} ({serial}) - Status changed to {status}")

    def _handle_missing_devices(self, missing_device_ids):
        """Handle devices that weren't found in recent API responses"""
        stale_devices = []
        current_time = time.time()

        for device_id in missing_device_ids:
            if device_id in self.device_cache:
                device = self.device_cache[device_id]

                # Add last_seen timestamp if not present
                if 'last_seen' not in device:
                    device['last_seen'] = current_time
                    self.device_cache[device_id] = device

                # Check if device has been missing for too long (e.g., 24 hours = 86400 seconds)
                time_since_last_seen = current_time - device.get('last_seen', current_time)
                if time_since_last_seen > 86400:  # 24 hours
                    stale_devices.append((device_id, device))
                else:
                    # Update last_seen for devices that were found
                    device['last_seen'] = current_time
                    self.device_cache[device_id] = device

        # Remove stale devices
        if stale_devices:
            print(f"🧹 Removing {len(stale_devices)} stale devices (not seen for 24+ hours):")
            for device_id, device in stale_devices:
                model = device.get('model', 'Unknown')
                serial = device.get('serial', 'N/A')
                print(f"   - Removed: {model} ({serial})")

                # Remove from cache
                if device_id in self.device_cache:
                    del self.device_cache[device_id]

                # Remove from equipment list
                self.equipment = [eq for eq in self.equipment
                                if not (eq.get('serial') == device.get('serial') and
                                       eq.get('model') == device.get('model'))]

        # Report remaining missing devices
        remaining_missing = missing_device_ids - set(device_id for device_id, _ in stale_devices)
        if remaining_missing:
            print(f"📍 {len(remaining_missing)} devices temporarily unavailable:")
            for device_id in list(remaining_missing)[:3]:  # Show first 3
                if device_id in self.device_cache:
                    device = self.device_cache[device_id]
                    model = device.get('model', 'Unknown')
                    serial = device.get('serial', 'N/A')
                    print(f"   - {model} ({serial}) - will check again next update")

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

    def add_equipment(self, equipment_entry):
        """Add a new equipment entry to the equipment list"""
        if isinstance(equipment_entry, dict):
            self.equipment.append(equipment_entry)
            # Update cache
            serial = equipment_entry.get('serial', f'NO_SERIAL_{len(self.equipment)}')
            model = equipment_entry.get('model', 'Unknown')
            device_identifier = f"{serial}_{model}"
            self.device_cache[device_identifier] = equipment_entry
            self.save_cached_devices()
        else:
            raise ValueError("Equipment entry must be a dictionary")

    def delete_equipment(self, idx):
        if 0 <= idx < len(self.equipment):
            device = self.equipment[idx]
            # Remove from cache
            serial = device.get('serial', '')
            model = device.get('model', 'Unknown')
            device_identifier = f"{serial}_{model}"
            if device_identifier in self.device_cache:
                del self.device_cache[device_identifier]

            # Remove from equipment list
            del self.equipment[idx]
            self.save_cached_devices()