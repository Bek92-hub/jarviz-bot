import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Sizning Telegram bot tokeningiz
TOKEN = "8683823927:AAHYst9wLW4yH0ToGKZZWRcMcgqRsvvitCU"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Rasmlarni saqlash uchun papka
UPLOAD_FOLDER = "downloads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Telegram'dan keladigan xabar va rasmlarni qabul qiluvchi asosiy funksiya"""
    data = request.get_json()
    
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        
        # 1. Agar botga rasm yuborilsa
        if "photo" in message:
            # Eng sifatli rasmni tanlaymiz
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            
            # Telegram serveridan rasm yo'lini olamiz
            file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
            file_response = requests.get(file_info_url).json()
            
            if file_response.get("ok"):
                file_path = file_response["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                
                # Rasmni serverga yuklab olamiz
                img_data = requests.get(download_url).content
                local_file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.jpg")
                
                with open(local_file_path, "wb") as f:
                    f.write(img_data)
                
                print(f"Rasm muvaffaqiyatli saqlandi: {local_file_path}")
                send_message(chat_id, "📷 Rasm qabul qilindi va tizimga saqlandi, xo'jayin! Uni tahlil qilishga tayyorman.")
        
        # 2. Agar matnli xabar yuborilsa
        elif "text" in message:
            text = message["text"]
            print(f"Xabar keldi: {text}")
            send_message(chat_id, f"✅ Xabaringiz qabul qilindi, xo'jayin: {text}")

    return "OK", 200

def send_message(chat_id, text):
    """Bot orqali foydalanuvchiga javob yuborish"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
