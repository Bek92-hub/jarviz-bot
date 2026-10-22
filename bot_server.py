import os
import requests
from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import google.generativeai as genai

app = Flask(__name__)

TOKEN = "8683823927:AAHYst9wLW4yH0ToGKZZWRcMcgqRsvvitCU"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Gemini API kalitingizni shu yerga yozing (yoki Render Environment variables'ga qo'shing)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "SIZNING_HAQIQIY_GEMINI_API_KALITINGIZ")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def log_to_sheets(user_id, user_name, event_type, message_text, status):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        
        spreadsheet_id = "1G8ix-crU3PlWCTJZi1Yl3fdY0tKRcds9khzASOqw4yw"
        sheet = client.open_by_key(spreadsheet_id).worksheet("serviz")
        
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        
        bot_response = "Tushunarli."

        if "photo" in message:
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            
            file_info_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
            file_response = requests.get(file_info_url).json()
            
            if file_response.get("ok"):
                file_path = file_response["result"]["file_path"]
                image_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                img_bytes = requests.get(image_url).content
                
                temp_img_path = "temp_photo.jpg"
                with open(temp_img_path, "wb") as f:
                    f.write(img_bytes)
                
                sample_file = genai.upload_file(temp_img_path)
                ai_result = model.generate_content([sample_file, "Bu rasmni tahlil qil, undagi yozuvlar, xatolar yoki ma'lumotlarni o'zbek tilida tushuntirib ber."])
                bot_response = ai_result.text
                
                log_to_sheets(user_id, user_name, "Rasm tahlili", bot_response[:200], "Muvaffaqiyatli")
                os.remove(temp_img_path)

        elif "text" in message:
            text = message["text"]
            
            ai_result = model.generate_content(f"Foydalanuvchi quyidagi xabarni yozdi: '{text}'. Unga yordamchi AI sifatida o'zbek tilida aniq, foydali va to'liq javob ber.")
            bot_response = ai_result.text
            
            log_to_sheets(user_id, user_name, "Matnli xabar", f"Savol: {text} | Javob: {bot_response[:100]}", "Muvaffaqiyatli")

        send_message(chat_id, bot_response)

    return "OK", 200

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
