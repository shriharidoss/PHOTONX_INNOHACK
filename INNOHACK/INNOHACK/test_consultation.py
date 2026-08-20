from db import save_consultation

consultation_id = save_consultation(
    2,
    1,
    "Video",
    "Routine health consultation"
)

print("Consultation saved successfully!")
print("Consultation ID:", consultation_id)
