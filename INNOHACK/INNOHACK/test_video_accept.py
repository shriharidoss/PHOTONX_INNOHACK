from db import accept_video_request

result = accept_video_request(
    1,
    1,
    "ROOM-TEST1234"
)

if result == 1:
    print("Video consultation accepted successfully!")
else:
    print("Request not found or already processed.")
