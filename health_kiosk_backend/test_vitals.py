import requests

url = "http://127.0.0.1:5000/api/vitals"

data = {
    "patient_id": 1,
    "temperature": None,
    "heart_rate": 69.69,
    "spo2": 97.61,
    "systolic_bp": 114.44,
    "diastolic_bp": 69.99
}

response = requests.post(
    url,
    json=data
)

print("STATUS:", response.status_code)
print("RESPONSE:")
print(response.text)