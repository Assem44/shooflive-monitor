"""
تحميل الفيديو باستخدام yt-dlp
"""

import subprocess
import os
from pathlib import Path
from config import (
DOWNLOAD_DIR, DOWNLOAD_QUALITY, SEND_VIDEO_TO_TELEGERAM
)
import logging
from notifier import send_telegram

logger = logging.getLogger(__name__)


def download_video(video_url, episode_num, series_name):
    """
    يحمّل الفيديو بـ yt-dlp
    
    Args:
        video_url: رابط m3u8
        episode_num: رقم الحلقة
        series_name: اسم المسلسل
    
    Returns:
        str: مسار الملف المحمّل أو None
    """
    # أنشئ مجلد التحميل
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
    # اسم الملف
    safe_name = series_name.replace(" ", "_").replace("/", "_")
    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{safe_name}_E{episode_num:02d}.%(ext)s"
    )
    
    # تحديد صيغة التحميل
    if DOWNLOAD_QUALITY == "best":
        format_spec = "bestvideo+bestaudio/best"
    else:
        format_spec = f"bestvideo[height<={DOWNLOAD_QUALITY}]+bestaudio/best[height<={DOWNLOAD_QUALITY}]"
    
    cmd = [
        "yt-dlp",
        "-f", format_spec,
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--no-playlist",
        "--no-warnings",
        video_url
    ]
    
    logger.info(f"⬇️ بدء التحميل بجودة {DOWNLOAD_QUALITY}...")
    logger.info(f"📁 المسار: {DOWNLOAD_DIR}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # ساعتين max
        )
        
        if result.returncode == 0:
            # ابحث عن الملف الناتج
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(f"{safe_name}_E{episode_num:02d}"):
                    filepath = os.path.join(DOWNLOAD_DIR, f)
                    logger.info(f"✅ تم التحميل: {filepath}")

                    try:
                        file_size = os.path.getsize(filepath)
                        size_mb = file_size / (1024 * 1024)
                        
                        if size_mb > 1024:
                            size_str = f"{size_mb / 1024:.2f} GB"
                        else:
                            size_str = f"{size_mb:.0f} MB"
                        
                        message = (
                            f"✅ <b>تم تحميل الحلقة {episode_num}!</b>\n\n"
                            # f"📺 {series_name}\n"
                            # f"📁 <code>{filepath}</code>\n"
                            # f"📊 الحجم: <b>{size_str}</b>\n"
                            # f"🎬 الجودة: <b>{DOWNLOAD_QUALITY}p</b>"
                        )
                        
                        send_telegram(message)
                    
                    except Exception as e:
                        logger.error(f"⚠️ فشل إرسال إشعار التحميل: {e}")


                    return filepath
        else:
            logger.error(f"❌ فشل التحميل: {result.stderr}")

            try:

                send_telegram(
                    f"⚠️ <b>فشل تحميل الحلقة {episode_num}</b>\n\n"
                    # f"📺 {series_name}\n"
                    # f"❌ السبب: <code>{result.stderr[:200]}</code>"
                )
            except:
                pass
            return None
    
    except subprocess.TimeoutExpired:
        logger.error("❌ انتهت مهلة التحميل")
        return None
    except Exception as e:
        logger.error(f"❌ خطأ في التحميل: {e}")
        return None


# ================== اختبار سريع ==================
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("الاستخدام: python downloader.py <m3u8_url>")
        sys.exit(1)
    
    download_video(sys.argv[1], 13, "Test_Series")
