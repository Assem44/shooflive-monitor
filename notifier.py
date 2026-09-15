"""
إرسال إشعارات تيليجرام
"""

import requests
from config import BOT_TOKEN, CHAT_ID
import logging

logger = logging.getLogger(__name__)


def send_telegram(message, disable_preview=False):
    """
    يرسل رسالة إلى تيليجرام
    
    Args:
        message: نص الرسالة (يدعم HTML)
        disable_preview: تعطيل معاينة الروابط
    
    Returns:
        bool: True لو نجح الإرسال
    """
    if not BOT_TOKEN or not CHAT_ID or "ضع_" in BOT_TOKEN:
        logger.error("❌ BOT_TOKEN أو CHAT_ID غير مكوّن")
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": disable_preview
    }
    
    try:
        response = requests.post(url, data=payload, timeout=15)
        response.raise_for_status()
        result = response.json()
        
        if result.get("ok"):
            logger.info("✅ تم إرسال الإشعار بنجاح")
            return True
        else:
            logger.error(f"❌ فشل الإرسال: {result}")
            return False
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ خطأ في الاتصال بتيليجرام: {e}")
        return False


def notify_new_episode(episode_num, episode_url, series_name, video_url=None):
    """
    إرسال إشعار بحلقة جديدة بتنسيق جميل
    
    Args:
        episode_num: رقم الحلقة
        episode_url: رابط صفحة الحلقة
        series_name: اسم المسلسل
        video_url: رابط الفيديو المباشر (اختياري)
    """
    message = (
        f"🎬 <b>حلقة جديدة نزلت!</b>\n\n"
        f"📺 <b>{series_name}</b>\n"
        f"🎞️ <b>الحلقة {episode_num}</b>\n\n"
        f"🔗 <a href='{episode_url}'>شاهد على الموقع</a>"
    )
    
    if video_url:
        message += f"\n\n⬇️ <a href='{video_url}'>رابط البث المباشر (m3u8)</a>"
    
    return send_telegram(message)


def notify_error(error_message):
    """إرسال إشعار بخطأ"""
    message = f"⚠️ <b>خطأ في النظام</b>\n\n<code>{error_message}</code>"
    return send_telegram(message)


def notify_startup():
    """إشعار بدء تشغيل النظام"""
    message = "🚀 <b>تم تشغيل النظام</b>"
    return send_telegram(message)


def send_video_to_telegram(file_path, episode_num, caption=""):
    """يرفع فيديو على تيليجرام"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    
    try:
        with open(file_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {
                'chat_id': CHAT_ID,
                'caption': caption or f"🎬 الحلقة {episode_num}",
                'supports_streaming': True
            }
            response = requests.post(url, files=files, data=data, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get('ok', False)
    except Exception as e:
        logger.error(f"❌ فشل رفع الفيديو على تيليجرام: {e}")
        return False

def notify_github_release(episode_num, series_name, download_url):
    """يبعت رابط التحميل من GitHub Releases"""
    message = (
        f"🎬 <b>حلقة جديدة نزلت!</b>\n\n"
        f"📺 <b>{series_name}</b>\n"
        f"🎞️ <b>الحلقة {episode_num}</b>\n\n"
        f"⬇️ <a href='{download_url}'>تحميل مباشر من GitHub</a>\n\n"
        f"⏳ <i>الرابط صالح لمدة {CLEANUP_DAYS} يوم</i>"
    )
    return send_telegram(message)
