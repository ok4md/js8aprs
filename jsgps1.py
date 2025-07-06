from js8net import start_net, send_aprs_grid
import time
import serial
import re

# === Configuration ===
GPS_COM_PORT = "COM10"
FIXED_GRID = "JO70OV54EB"
GPS_INTERVAL = 60        # 1 minute
FIXED_INTERVAL = 660    # 15 minutes

def parse_gpgga(line):
    """Parse NMEA GPGGA sentence to get lat/lon"""
    try:
        parts = line.split(',')
        if parts[0] != "$GPGGA" or len(parts) < 6:
            return None

        lat_raw = parts[2]
        lat_dir = parts[3]
        lon_raw = parts[4]
        lon_dir = parts[5]

        lat_deg = float(lat_raw[:2])
        lat_min = float(lat_raw[2:])
        lat = lat_deg + lat_min / 60
        if lat_dir == 'S':
            lat = -lat

        lon_deg = float(lon_raw[:3])
        lon_min = float(lon_raw[3:])
        lon = lon_deg + lon_min / 60
        if lon_dir == 'W':
            lon = -lon

        return (lat, lon)
    except:
        return None

def latlon_to_maiden(lat, lon):
    """Convert lat/lon to Maidenhead grid locator (6-char)"""
    A = ord('A')
    lon += 180
    lat += 90

    field_lon = int(lon // 20)
    field_lat = int(lat // 10)
    square_lon = int((lon % 20) // 2)
    square_lat = int((lat % 10) // 1)
    subsquare_lon = int(((lon % 2) * 12))
    subsquare_lat = int(((lat % 1) * 24))

    grid = chr(A + field_lon) + chr(A + field_lat)
    grid += str(square_lon) + str(square_lat)
    grid += chr(A + subsquare_lon) + chr(A + subsquare_lat)

    return grid

def get_gps_grid():
    """Try to read a grid from GPS on COM7"""
    try:
        with serial.Serial(GPS_COM_PORT, 4800, timeout=2) as ser:
            timeout = time.time() + 5  # 5 seconds max
            while time.time() < timeout:
                line = ser.readline().decode(errors='ignore').strip()
                if "$GPGGA" in line:
                    pos = parse_gpgga(line)
                    if pos:
                        lat, lon = pos
                        grid = latlon_to_maiden(lat, lon)
                        print(f"📡 GPS: lat={lat:.6f}, lon={lon:.6f} -> grid={grid}")
                        return grid
    except Exception as e:
        print(f"⚠️  GPS read error: {e}")
    return None

# === Main loop ===
def main():
    print("🚀 Starting JS8Call position beacon script...")
    start_net("127.0.0.1", 2442)

    while True:
        gps_grid = get_gps_grid()
        if gps_grid:
            send_aprs_grid(gps_grid)
            print(f"[{time.ctime()}] ✅ Sent GPS position: {gps_grid}")
            time.sleep(GPS_INTERVAL)
        else:
            send_aprs_grid(FIXED_GRID)
            print(f"[{time.ctime()}] 🧭 Sent fallback fixed position: {FIXED_GRID}")
            time.sleep(FIXED_INTERVAL)

if __name__ == "__main__":
    main()
