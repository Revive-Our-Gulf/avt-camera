import requests

url = 'http://192.168.2.3:5000/toggle_recording'
data = {'isRecording': False, 'folderName': 'request_test'}
response = requests.post(url, json=data)

print(f"Status Code: {response.status_code}")
print(f"Response Content: {response.text}")

try:
    print(response.json())
except requests.exceptions.JSONDecodeError as e:
    print("Response is not in JSON format")