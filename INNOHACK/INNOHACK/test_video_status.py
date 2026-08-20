from db import get_patient_video_requests

requests = get_patient_video_requests(2)

print("Patient video consultation history:")

for request in requests:
    print(request)
