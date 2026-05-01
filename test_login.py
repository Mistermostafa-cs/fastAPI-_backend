import urllib.request
import json

url = "http://localhost:8001/api/auth/login"
payload = {
    "email": "admin@school.com",
    "password": "Admin@123"
}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data)
req.add_header('accept', 'application/json')
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req) as response:
        status = response.getcode()
        body = response.read().decode('utf-8')
        print(f"Status Code: {status}")
        print(f"Response Body: {body}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Response Body: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
