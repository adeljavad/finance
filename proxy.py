from fastapi import FastAPI
import requests

app = FastAPI()

API_KEY = "sk-9449e910090742e09784be24d65c7e55"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

@app.post("/v1/chat/completions")
def proxy(data: dict):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    resp = requests.post(DEEPSEEK_URL, json=data, headers=headers)
    return resp.json()
