import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = "8683823927:AAHYst9wLW4yH0ToGKZZWRcMcgqRsvvitCU"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        
        # Agar botga rasm yuborilsa
        if "photo" in message:
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            
            # Telegram serveridan rasm yo'lini olamiz
            file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
            file_response = requests.get(file_info_url).json()
            
            if file_response.get("ok"):
                file_path = file_response["result"]["file_path"]
                image_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                
                # Rasmni binar korpusda yuklab olamiz va tahlilga tayyorlaymiz
                img_data = requests.get(image_url).content
                
                print(f"ANALYSIS_READY_IMAGE: {len(img_data)} bytes | URL: {image_url}")
                
                # Foydalanuvchiga bot orqali javob yuboramiz
                send_message(chat_id, f"🔍 Rasm qabul qilindi va tahlilga jo'natildi! Hajmi: {len(img_data)} bayt.")
        
        elif "text" in message:
            text = message["text"]
            send_message(chat_id, f"✅ Xabaringiz qabul qilindi: {text}")

    return "OK", 200

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
