import requests

BOT_TOKEN = "8920640316:AAFnvDBiEvTTc83_VfhsBS9lHnRb7oSF4x4"
CHAT_ID = "7218632889"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML", # لاستخدام تنسيقات HTML
        "disable_web_page_preview": False # لتفعيل معاينة الرابط
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print(response.json())
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

# مثال للاستخدام
send_telegram_message("🎬 <b>حلقة جديدة!</b>\n\nمسلسل إسطنبول رأساً على عقب - الحلقة 5\n<a href='https://shooflive.net/...'>رابط المشاهدة</a>")