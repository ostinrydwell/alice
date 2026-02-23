import os
import requests
from fastapi import FastAPI, Request
from groq import Groq

app = FastAPI()

api_key = "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"
client = Groq(api_key=api_key)
SC_CLIENT_ID = "iZ8S4vGbBRmno4S6ICm2pZED9mKjru9B"
SC_PLAYLIST = "https://soundcloud.com/user-730165181/sets/gae-lk89bp5rfsxy4ai"
YANDEX_DISK_URL = "https://disk.yandex.com/d/DUXziM_pYIKVuQ"

def get_yadisk_direct(public_url):
    api_url = f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={public_url}"
    try:
        res = requests.get(api_url).json()
        return res.get("href")
    except: return None

def make_res(v, s, text, url=None):
    resp = {"text": text, "end_session": False}
    if url:
        resp["directives"] = {"audio_player": {"action": "Play", "item": {"stream": {"url": url, "offset_ms": 0, "token": "track"}}}}
    return {"version": v, "session": s, "response": resp}

@app.post("/")
async def handle(request: Request):
    data = await request.json()
    v, s = data["version"], data["session"]
    req = data.get("request", {})
    cmd = req.get("command", "").lower()

    if data.get("session", {}).get("new"):
        return make_res(v, s, "Система готова.")

    if any(x in cmd for x in ["стоп", "пауза", "выключи"]):
        return {"version": v, "session": s, "response": {"directives": {"audio_player": {"action": "Stop"}}, "end_session": False}}

    if "саундклауд" in cmd or "музыка" in cmd:
        return make_res(v, s, "Запускаю SoundCloud", SC_PLAYLIST)

    if "диск" in cmd:
        link = get_yadisk_direct(YANDEX_DISK_URL)
        return make_res(v, s, "Включаю Диск", link) if link else make_res(v, s, "Файл не найден")

    try:
        chat = client.chat.completions.create(model="llama3-8b-8192", messages=[{"role": "user", "content": cmd}])
        return make_res(v, s, chat.choices[0].message.content)
    except:
        return make_res(v, s, "Грок временно недоступен.")
