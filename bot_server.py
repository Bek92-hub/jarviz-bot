import os
import requests
from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

app = Flask(__name__)

TOKEN = "8683823927:AAHYst9wLW4yH0ToGKZZWRcMcgqRsvvitCU"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

# --- GOOGLE SHEETS ULANISHI ---
# Google Sheets API sozlamalari
# (Google Service Account JSON kalitingizni render muhitiga yuklagan bo'lishingiz kerak)
def log_to_sheets(user_id, user_name, event_type, message_text, status):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # credentials.json fayli Render papkasida bo'lishi kerak
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        
        # Siz ko'rsatgan Google Sheets jadvali (URL ID orqali)
        spreadsheet_id = "1G8ix-crU3PlWCTJZi1Yl3fdY0tKRcds9khzASOqw4yw"
        sheet = client.open_by_key(spreadsheet_id).worksheet("serviz")
        
        # Hozirgi sana va vaqt
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Jadval oxiriga qator qo'shish
        sheet.append_row([now, str(user_id), user_name, event_type, message_text, status])
    except Exception as e:
        print(f"Google Sheets xatoligi: {e}")

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"].get("id")
        user_name = message["from"].get("first_name", "Noma'lum")
        
        # Agar botga rasm yuborilsa
        if "photo" in message:
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            
            file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
            file_response = requests.get(file_info_url).json()
            
            if file_response.get("ok"):
                file_path = file_response["result"]["file_path"]
                image_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                img_data = requests.get(image_url).content
                
                print(f"WEB_BRIDGE_IMAGE_RECEIVED: {len(img_data)} bytes | URL: {image_url}")
                
                # Google Sheets'ga yozish
                log_to_sheets(user_id, user_name, "Rasm qabul qilindi", f"Hajmi: {len(img_data)} bayt", "Muvaffaqiyatli")
                
                send_message(chat_id, f"🔍 Rasm qabul qilindi va Google Sheets (serviz) jadvaliga yozildi!")
        
        elif "text" in message:
            text = message["text"]
            
            # Google Sheets'ga yozish
            log_to_sheets(user_id, user_name, "Xabar keldi", text, "Muvaffaqiyatli")
            
            send_message(chat_id, f"✅ Xabaringiz qabul qilindi va jadvalga qayd etildi: {text}")

    return "OK", 200

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
