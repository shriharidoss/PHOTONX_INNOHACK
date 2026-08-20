import serial
import csv
import time

PORT = "COM9"
BAUD_RATE = 115200
OUTPUT_FILE = "my_ppg.csv"
TOTAL_SAMPLES = 210

print("Opening ESP32...")
print("Port:", PORT)

ser = serial.Serial(
    PORT,
    BAUD_RATE,
    timeout=2
)

time.sleep(2)

print("Waiting for PPG data...")
print("Place your finger on the MAX30102.")
print()

rows = []

header_found = False

while len(rows) < TOTAL_SAMPLES:

    line = ser.readline().decode(
        "utf-8",
        errors="ignore"
    ).strip()

    if not line:
        continue

    print(line)

    if line == "timestamp,ir,red":
        header_found = True
        continue

    if not header_found:
        continue

    if line == "COLLECTION_COMPLETE":
        break

    parts = line.split(",")

    if len(parts) != 3:
        continue

    try:
        timestamp = int(parts[0])
        ir = int(parts[1])
        red = int(parts[2])

        rows.append(
            [timestamp, ir, red]
        )

    except ValueError:
        continue

ser.close()

with open(
    OUTPUT_FILE,
    "w",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow(
        ["timestamp", "ir", "red"]
    )

    writer.writerows(rows)

print()
print("==============================")
print("PPG COLLECTION COMPLETE")
print("==============================")
print("Samples saved:", len(rows))
print("File:", OUTPUT_FILE)