from db import save_doctor

doctor_id = save_doctor(
    "Dr. Priya",
    "General Medicine",
    "9876543212",
    "doctor@example.com"
)

print("Doctor saved successfully!")
print("Doctor ID:", doctor_id)
