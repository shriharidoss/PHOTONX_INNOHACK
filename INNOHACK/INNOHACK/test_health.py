from db import save_health_reading

reading_id = save_health_reading(
    2,
    36.7,
    98,
    78,
    120,
    80
)

print("Health reading saved successfully!")
print("Reading ID:", reading_id)
