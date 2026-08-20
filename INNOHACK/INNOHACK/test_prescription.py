from db import save_prescription

prescription_id = save_prescription(
    2,
    1,
    "Paracetamol",
    "500 mg",
    "Twice daily",
    "3 days",
    "Take after food"
)

print("Prescription saved successfully!")
print("Prescription ID:", prescription_id)
