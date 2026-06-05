import requests
import json

data = {
    "name": "product",
    "rating": 4.5,
    "price": 100.0,
    "category": "Footwear"
}

try:
    res = requests.post("http://127.0.0.1:8001/explain", json=data)
    print("Status:", res.status_code)
    with open("explain_out.json", "w", encoding="utf-8") as f:
        f.write(res.text)
except Exception as e:
    print("Error:", e)
