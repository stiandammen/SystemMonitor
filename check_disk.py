import psutil
import time

print("Checking disk IO counters...")
total = psutil.disk_io_counters(perdisk=False)
print(f"Total IO: {total}")

perdisk = psutil.disk_io_counters(perdisk=True)
print("\nPer-disk keys:")
for key in perdisk.keys():
    print(f" - '{key}'")

print("\nWaiting 1 second to check rates...")
time.sleep(1)
total2 = psutil.disk_io_counters(perdisk=False)
read_bps = (total2.read_bytes - total.read_bytes)
write_bps = (total2.write_bytes - total.write_bytes)
print(f"Current System Read: {read_bps/1024:.1f} KB/s")
print(f"Current System Write: {write_bps/1024:.1f} KB/s")
