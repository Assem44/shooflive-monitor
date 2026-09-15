"""
الإعدادات العامة للنظام
عدّل القيم دي حسب احتياجك
"""

# ================== إعدادات تيليجرام ==================
BOT_TOKEN = "8920640316:AAFnvDBiEvTTc83_VfhsBS9lHnRb7oSF4x4"        # التوكن من @BotFather
CHAT_ID = "7218632889"       # الـ Chat ID بتاعك
# إعدادات إضافية
SEND_VIDEO_TO_TELEGRAM = True   # ارفع الفيديو على تيليجرام

# ================== إعدادات المراقبة ==================
# رابط المسلسل في shooflive.net
SERIES_URL = "https://shooflive.net/series/مسلسل-إسطنبول-رأساً-على-عقب/"

# اسم المسلسل (بيظهر في الإشعارات)
SERIES_NAME = "مسلسل إسطنبول رأساً على عقب"

# Slug بتاع المسلسل في dilaymotion.cam
# (بيظهر في رابط الـ iframe)
DILAY_SLUG = "alti-ustu-istanbul-2026"

# ================== إعدادات التحميل ==================
# هل عايز تحمّل الفيديو تلقائيًا؟
AUTO_DOWNLOAD = True

# جودة التحميل المفضلة (best, 1080, 720, 480, 360)
DOWNLOAD_QUALITY = "480"

# مسار حفظ الفيديوهات
DOWNLOAD_DIR = r"C:\Users\Dell\Desktop\Estanpool"


# ================== إعدادات السيرفر ==================
# السيرفر المفضل (1=Cdnplus, 2=Voe, 3=AnaFast, 4=MP4Plus, 5=VidSpeed, 6=Vk)
PREFERRED_SERVER = 1

# ================== إعدادات متقدمة ==================
# مدة الانتظار بين الطلبات (ثواني)
REQUEST_DELAY = 3

# عدد مرات إعادة المحاولة عند الفشل
MAX_RETRIES = 3

# مسار ملف الحالة
STATE_FILE = "state.json"

# مسار ملف السجل
LOG_FILE = "monitor.log"

# هل تريد تشغيل المتصفح في وضع مرئي؟ (للتشخيص)
HEADLESS = False
