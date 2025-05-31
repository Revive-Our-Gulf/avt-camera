import os
import json
import piexif
from datetime import datetime

class ExifManager:
    def __init__(self, settings_manager, camera_hardware_controller=None):
        self.settings_manager = settings_manager
        self.camera_hardware_controller = camera_hardware_controller
        self.exif_settings_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'settings', 
            'exif_data.json'
        )
        self.exif_settings = self._load_exif_settings()
        
    def _load_exif_settings(self):
        """Load EXIF settings from JSON file."""
        try:
            with open(self.exif_settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading EXIF settings: {e}")
            return {
                "camera": {}, 
                "lens": {}, 
                "exposure": {}, 
                "other": {}
            }
            
    def _get_string_value(self, settings, key):
        """Extract string value from setting which might be an EnumEntry object"""
        value = settings.get(key)
        if hasattr(value, '__str__'):
            return str(value)
        return value
    
    def to_deg(self, value, loc):
        """Convert decimal coordinates to degrees format for EXIF."""
        if value < 0:
            loc_value = loc[0]  # S or W
        elif value > 0:
            loc_value = loc[1]  # N or E
        else:
            loc_value = ""
            
        abs_value = abs(value)
        deg = int(abs_value)
        t1 = (abs_value-deg)*60
        min = int(t1)

        sec = (t1 - min)* 60
        sec_multiplier = 10000
        sec_int = int(sec * sec_multiplier)
        
        return ((deg, 1), (min, 1), (sec_int, sec_multiplier)), loc_value
    
    def create_exif_dict(self, now, telemetry=None):
        """Create EXIF dictionary with camera settings and optional telemetry."""
        exif_dict = {"0th":{}, "Exif":{}, "GPS":{}, "1st":{}, "thumbnail":None}

        current_settings = {}
        try:
            if self.camera_hardware_controller:
                current_settings = self.camera_hardware_controller.get_camera_settings()
            else:
                params_list = self.settings_manager.get_parameters_definitions()["parameters"]
                current_settings = {param["id"]: param["value"] for param in params_list}
        except Exception as e:
            print(f"Could not get current camera settings: {e}")
            
        # Add camera information
        camera = self.exif_settings.get("camera", {})
        exif_dict["0th"][piexif.ImageIFD.Make] = camera.get("Make", "").encode()
        exif_dict["0th"][piexif.ImageIFD.Model] = camera.get("Model", "").encode()
        exif_dict["0th"][piexif.ImageIFD.Software] = camera.get("Software", "").encode()
        exif_dict["0th"][piexif.ImageIFD.DateTime] = now.strftime("%Y:%m:%d %H:%M:%S")
        exif_dict["0th"][piexif.ImageIFD.Artist] = camera.get("Artist", "").encode()
        exif_dict["0th"][piexif.ImageIFD.Copyright] = camera.get("Copyright", "").encode()
        
        # Add lens information
        lens = self.exif_settings.get("lens", {})
        exif_dict["Exif"][piexif.ExifIFD.LensMake] = lens.get("LensMake", "").encode()
        exif_dict["Exif"][piexif.ExifIFD.LensModel] = lens.get("LensModel", "").encode()
        exif_dict["Exif"][piexif.ExifIFD.FocalLength] = tuple(lens.get("FocalLength", [1, 100]))
        exif_dict["Exif"][piexif.ExifIFD.ApertureValue] = tuple(lens.get("MaxApertureValue", [1, 100]))
        
        # Handle exposure time
        exposure_time = current_settings.get("ExposureTime", 0)
        exif_dict["Exif"][piexif.ExifIFD.ExposureTime] = (int(exposure_time), 1000000)
        
        # Handle exposure mode - convert EnumEntry to string if needed
        exposure_auto = self._get_string_value(current_settings, "ExposureAuto")
        exif_dict["Exif"][piexif.ExifIFD.ExposureMode] = 0 if exposure_auto == "Continuous" else 1 

        # Handle flash - convert EnumEntry to string if needed
        line_source = self._get_string_value(current_settings, "LineSource")
        exif_dict["Exif"][piexif.ExifIFD.Flash] = 0 if line_source == "Off" else 1
        
        white_balance_auto = self._get_string_value(current_settings, "BalanceWhiteAuto")
        exif_dict["Exif"][piexif.ExifIFD.WhiteBalance] = 0 if white_balance_auto == "Continuous" else 1
        
        if telemetry:
            self._add_gps_data(exif_dict, telemetry)
            
        return exif_dict
    
    def _add_gps_data(self, exif_dict, telemetry):
        """Add GPS data to EXIF dictionary."""
        try:
            # GPS coordinates
            lat = float(telemetry['GLOBAL_POSITION_INT']['lat']) / 1e7
            lon = float(telemetry['GLOBAL_POSITION_INT']['lon']) / 1e7

            lat_deg = self.to_deg(lat, ["S", "N"])
            lon_deg = self.to_deg(lon, ["W", "E"])
            
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = lat_deg[1].encode()
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = lon_deg[1].encode()
            
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = lat_deg[0]
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = lon_deg[0]
            
            # Altitude
            alt = float(telemetry['GLOBAL_POSITION_INT']['relative_alt']) / 1e3
            exif_dict["GPS"][piexif.GPSIFD.GPSAltitude] = (int(abs(alt) * 1000), 1000)
            exif_dict["GPS"][piexif.GPSIFD.GPSAltitudeRef] = 1 if alt < 0 else 0
            
            # Satellites
            satellites = telemetry['GPS_RAW_INT']['satellites_visible']
            exif_dict["GPS"][piexif.GPSIFD.GPSSatellites] = str(satellites).encode()
            
            # GPS timestamp
            time_in_seconds = telemetry['GLOBAL_POSITION_INT']['time_boot_ms'] // 1000
            hours = time_in_seconds // 3600
            minutes = (time_in_seconds % 3600) // 60
            seconds = time_in_seconds % 60
            exif_dict["GPS"][piexif.GPSIFD.GPSTimeStamp] = ((hours, 1), (minutes, 1), (seconds, 1))

            temperature = telemetry['SCALED_PRESSURE2']['temperature'] / 100.0
            print(f"Temperature: {temperature}°C")
            exif_dict['Exif'][piexif.ExifIFD.Temperature] = (int(temperature * 100), 100)

            dvlDistance = -1
            try:
                dvlDistance = telemetry['RANGEFINDER']['distance']
            except Exception as e:
                print(f"Error retrieving DVL distance: {e}")
                

            serialisable_telemetry = {
                'latitude': lat,
                'longitude': lon,
                'heading': telemetry['GLOBAL_POSITION_INT']['hdg'] / 1e2,
                'depth': telemetry['GLOBAL_POSITION_INT']['relative_alt'] / 1e3,
                'waterTemp': temperature,
                'driveMode': telemetry['HEARTBEAT']['custom_mode'],
                'gpsSatellites': telemetry['GPS_RAW_INT']['satellites_visible'],
                'gpsHDOP:': telemetry['GPS_RAW_INT']['eph'] / 1e2,
                'gpsHAccuracy': telemetry['GPS_RAW_INT']['h_acc'],
                'dvlDistance': dvlDistance
            }
            
            print(f"Serialisable Telemetry: {serialisable_telemetry}")
                        
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = json.dumps(serialisable_telemetry).encode()
            
        except Exception as e:
            print(f"Error adding GPS data to EXIF: {e}")
    
    def apply_exif_to_file(self, filename, now, telemetry=None):
        """Apply EXIF data to an image file."""
        try:
            exif_dict = self.create_exif_dict(now, telemetry)
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, filename)
            return True
        except Exception as e:
            print(f"Error applying EXIF data: {e}")
            import traceback
            traceback.print_exc()
            return False