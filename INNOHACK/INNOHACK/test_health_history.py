from db import get_health_readings

readings = get_health_readings(2)

print("Health history:")
for reading in readings:
    print(reading)
