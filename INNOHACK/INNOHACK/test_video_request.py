from db import create_video_request

request_id = create_video_request(
    2,
    "Need consultation about fever"
)

print("Video consultation request created!")
print("Request ID:", request_id)
