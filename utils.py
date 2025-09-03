
import re


class Regex:
    @staticmethod
    def validate_device_identifier(identifier):
        """Validate device identifier (serial/model) - allows alphanumeric, hyphens, underscores, spaces"""
        print(f"🔍 Validating identifier: '{identifier}' (type: {type(identifier)})")
        if not identifier or not isinstance(identifier, str):
            print("❌ Validation failed: empty or not string")
            return False, "Device identifier cannot be empty"
        pattern = r'^[a-zA-Z0-9\s_.,()-]+$'
        if not re.match(pattern, identifier.strip()):
            print(f"❌ Validation failed: invalid characters in '{identifier.strip()}'")
            return False, "Device identifier contains invalid characters. Only letters, numbers, spaces, hyphens, underscores, and basic punctuation allowed"
        if len(identifier.strip()) < 2:
            print(f"❌ Validation failed: too short ({len(identifier.strip())} chars)")
            return False, "Device identifier must be at least 2 characters long"
        if len(identifier.strip()) > 50:
            print(f"❌ Validation failed: too long ({len(identifier.strip())} chars)")
            return False, "Device identifier cannot exceed 50 characters"
        print(f"✅ Validation passed for: '{identifier.strip()}'")
        return True, ""

    @staticmethod
    def validate_latitude(lat):
        """Validate latitude coordinate"""
        try:
            lat_val = float(lat)
            if lat_val < -90 or lat_val > 90:
                return False, "Latitude must be between -90 and 90 degrees"
            return True, ""
        except (ValueError, TypeError):
            return False, "Latitude must be a valid number"

    @staticmethod
    def validate_longitude(lon):
        """Validate longitude coordinate"""
        try:
            lon_val = float(lon)
            if lon_val < -180 or lon_val > 180:
                return False, "Longitude must be between -180 and 180 degrees"
            return True, ""
        except (ValueError, TypeError):
            return False, "Longitude must be a valid number"

    @staticmethod
    def validate_battery(battery):
        """Validate battery level (0-100)"""
        try:
            battery_val = int(battery)
            if battery_val < 0 or battery_val > 100:
                return False, "Battery level must be between 0 and 100"
            return True, ""
        except (ValueError, TypeError):
            return False, "Battery level must be a valid whole number"