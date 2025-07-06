from js8net import start_net, send_aprs_grid
import time
import serial

# === Configuration ===
GPS_COM_PORT = "COM10"
FIXED_GRID = "KN12DR"
GPS_INTERVAL = 180       
FIXED_INTERVAL = 900

def parse_gpgga(line):
    """Parse GPGGA NMEA sentence and return decimal lat/lon"""
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

def latlon_to_maiden(lat, lon, precision=10):
    """Convert lat/lon to valid Maidenhead Locator up to 10 characters"""
    if precision not in [4, 6, 8, 10]:
        precision = 10

    lon += 180
    lat += 90
    A = ord('A')

    # First pair: field (A-R)
    field_lon = chr(A + int(lon // 20))
    field_lat = chr(A + int(lat // 10))

    # Second pair: square (0–9)
    square_lon = str(int((lon % 20) // 2))
    square_lat = str(int((lat % 10) // 1))

    # Third pair: subsquare (A–X)
    subsquare_lon = chr(A + int(((lon % 2) * 12)))
    subsquare_lat = chr(A + int(((lat % 1) * 24)))

    grid = field_lon + field_lat + square_lon + square_lat + subsquare_lon + subsquare_lat

    if precision >= 8:
        # Fourth pair: extended square (0-9)
        ext_lon = str(int((((lon % (1/12)) * 60 * 60) // 30)))
        ext_lat = str(int((((lat % (1/24)) * 60 * 60) // 15)))
        grid += ext_lon + ext_lat

    if precision == 10:
        # Fifth pair: extended subsquare (A-X)
        ext_lon = chr(A + int(((((lon % (1/12)) * 60 * 60) % 30) / (30/24))))
        ext_lat = chr(A + int(((((lat % (1/24)) * 60 * 60) % 15) / (15/24))))
        grid += ext_lon + ext_lat

    return grid[:precision]



def get_gps_grid():
    """Try to read 10-char Maidenhead from GPS on COM port"""
    try:
        # Ensure a fresh connection each time
        time.sleep(0.5)  # Small delay to help with Bluetooth stack
        ser = serial.Serial(GPS_COM_PORT, 4800, timeout=2)
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            timeout = time.time() + 5
            while time.time() < timeout:
                line = ser.readline().decode(errors='ignore').strip()
                if "$GPGGA" in line:
                    pos = parse_gpgga(line)
                    if pos:
                        lat, lon = pos
                        grid = latlon_to_maiden(lat, lon, precision=10)
                        print(f"📡 GPS: lat={lat:.6f}, lon={lon:.6f} → grid={grid}")
                        return grid
        finally:
            ser.close()
    except Exception as e:
        print(f"⚠️  GPS read error on {GPS_COM_PORT}: {e}")
    return None

# === Main loop ===
def main():
    print("🚀 Starting JS8Call GPS beacon script (10-char Maidenhead, COM10)...")
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
