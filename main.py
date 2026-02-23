import os
import requests
from fastapi import FastAPI, Request
from groq import Groq
from sclib import SoundcloudAPI

app = FastAPI()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
sc_api = SoundcloudAPI()

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
    cmd = data["request"].get("command", "").lower()

    if data["session"]["new"]:
        return make_res(v, s, "Платформа X готова. Грок на связи, музыка заряжена.")

    if any(x in cmd for x in ["стоп", "пауза", "выключи"]):
        return {"version": v, "session": s, "response": {"directives": {"audio_player": {"action": "Stop"}}, "end_session": False}}

    if "саундклауд" in cmd:
        try:
            track = list(sc_api.resolve(SC_PLAYLIST).tracks)[0]
            return make_res(v, s, f"Включаю SoundCloud: {track.title}", track.get_stream_url())
        except: return make_res(v, s, "Ошибка SoundCloud")

    if "диск" in cmd or "мои файлы" in cmd:
        link = get_yadisk_direct(YANDEX_DISK_URL)
        return make_res(v, s, "Запускаю файлы с Яндекс Диска", link) if link else make_res(v, s, "Файл не найден")

    try:
        chat = client.chat.completions.create(model="llama3-8b-8192", messages=[{"role": "user", "content": cmd}])
        return make_res(v, s, chat.choices[0].message.content)
    except:
        return make_res(v, s, "Грок занят, попробуй еще раз.")
