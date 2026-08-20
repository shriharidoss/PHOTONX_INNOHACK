from db import get_prescriptions

prescriptions = get_prescriptions(2)

print("Patient prescriptions:")

for prescription in prescriptions:
    print(prescription)
