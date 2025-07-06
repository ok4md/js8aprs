from js8net import start_net, send_aprs_grid
import time

# Connect to JS8Call TCP API
start_net("127.0.0.1", 2442)

# Wait a bit for connection
time.sleep(1)

# Your fixed position
my_grid = "JO70OV54FB"

# Send the position via APRSIS
send_aprs_grid(my_grid)

print(f"✅ Position {my_grid} sent to JS8Call.")
