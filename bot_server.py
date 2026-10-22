import os
import requests
from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import google.generativeai as genai

app = Flask(__name__)

# --- SOZLAMALAR ---
TOKEN = "8683823927:AAHYst9wLW4yH0ToGKZZWRcMcgqRsvvitCU"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Google Gemini AI kalitingiz (Render muhitida GEMINI_API_KEY sifatida yoki shu yerga yozasiz)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "SIZNING_GEMINI_API_KATINGIZ")
genai.configure(api_key=GEMINI_API_KEY)
# Eng so'nggi Gemini modelidan foydalanamiz
model = genai.GenerativeModel("gemini-1.5-flash")

# --- GOOGLE SHEETS GA YOZISH ---
def log_to_sheets(user_id, user_name, event_type, message_text, status):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        
        # Siz ko'rsatgan Google Sheets jadvali ID si
        spreadsheet_id = "1G8ix-crU3PlWCTJZi1Yl3fdY0tKRcds9khzASOqw4yw"
        sheet = client.open_by_key(spreadsheet_id).worksheet("serviz")
        
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, str(user_id), user_name, event_type, message_text, status])
    except Exception as e:
        print(f"Google Sheets xatoligi: {e}")

# --- TELEGRAM WEBHOOK ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"].get("id")
        user_name = message["from"].get("first_name", "Noma'lum")
        
        bot_response = "Tushunarli."

        # 1. Agar rasm yuborilsa (AI Vision orqali tahlil qilish)
        if "photo" in message:
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            
            file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
            file_response = requests.get(file_info_url).json()
            
            if file_response.get("ok"):
                file_path = file_response["result"]["file_path"]
                image_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                img_bytes = requests.get(image_url).content
                
                # Rasmni vaqtinchalik saqlab Gemini'ga beramiz
                temp_img_path = "temp_photo.jpg"
                with open(temp_img_path, "wb") as f:
                    f.write(img_bytes)
                
                sample_file = genai.upload_file(temp_img_path)
                ai_result = model.generate_content([sample_file, "Bu rasmni tahlil qil, undagi yozuvlar, xatolar yoki ma'lumotlarni o'zbek tilida tushuntirib ber."])
                bot_response = ai_result.text
                
                # Jadvalga yozish
                log_to_sheets(user_id, user_name, "Rasm tahlili", bot_response[:200], "Muvaffaqiyatli")
                os.remove(temp_img_path)

        # 2. Agar matn yuborilsa (AI Text orqali javob berish)
        elif "text" in message:
            text = message["text"]
            
            # Gemini orqali matnni tahlil qilish yoki javob qaytarish
            ai_result = model.generate_content(f"Foydalanuvchi quyidagi xabarni yozdi: '{text}'. Unga yordamchi AI sifatida o'zbek tilida aniq, foydali va to'liq javob ber.")
            bot_response = ai_result.text
            
            # Jadvalga yozish
            log_to_sheets(user_id, user_name, "Matnli xabar", f"Savol: {text} | Javob: {bot_response[:100]}", "Muvaffaqiyatli")

        # Telegram orqali foydalanuvchiga javob yuborish
        send_message(chat_id, bot_response)

    return "OK", 200

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
