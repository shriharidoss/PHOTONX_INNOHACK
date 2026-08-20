from db import save_patient

patient_id = save_patient(
    "Arun Kumar",
    28,
    "Male",
    "9876543211"
)

print("Patient saved successfully!")
print("Patient ID:", patient_id)
