# """
# تحميل الفيديو باستخدام yt-dlp
# """

# import subprocess
# import os
# from pathlib import Path
# from config import (
# DOWNLOAD_DIR, DOWNLOAD_QUALITY, SEND_VIDEO_TO_TELEGRAM
# )
# import logging
# from notifier import send_telegram

# logger = logging.getLogger(__name__)


# def download_video(video_url, episode_num, series_name):
#     """
#     يحمّل الفيديو بـ yt-dlp
    
#     Args:
#         video_url: رابط m3u8
#         episode_num: رقم الحلقة
#         series_name: اسم المسلسل
    
#     Returns:
#         str: مسار الملف المحمّل أو None
#     """
#     # أنشئ مجلد التحميل
#     Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
#     # اسم الملف
#     safe_name = series_name.replace(" ", "_").replace("/", "_")
#     output_template = os.path.join(
#         DOWNLOAD_DIR,
#         f"{safe_name}_E{episode_num:02d}.%(ext)s"
#     )
    
#     # تحديد صيغة التحميل
#     if DOWNLOAD_QUALITY == "best":
#         format_spec = "bestvideo+bestaudio/best"
#     else:
#         format_spec = f"bestvideo[height<={DOWNLOAD_QUALITY}]+bestaudio/best[height<={DOWNLOAD_QUALITY}]"
    
#     cmd = [
#         "yt-dlp",
#         "-f", format_spec,
#         "--merge-output-format", "mp4",
#         "-o", output_template,
#         "--no-playlist",
#         "--no-warnings",
#         video_url
#     ]
    
#     logger.info(f"⬇️ بدء التحميل بجودة {DOWNLOAD_QUALITY}...")
#     logger.info(f"📁 المسار: {DOWNLOAD_DIR}")
    
#     try:
#         result = subprocess.run(
#             cmd,
#             capture_output=True,
#             text=True,
#             timeout=7200  # ساعتين max
#         )
        
#         if result.returncode == 0:
#             # ابحث عن الملف الناتج
#             for f in os.listdir(DOWNLOAD_DIR):
#                 if f.startswith(f"{safe_name}_E{episode_num:02d}"):
#                     filepath = os.path.join(DOWNLOAD_DIR, f)
#                     logger.info(f"✅ تم التحميل: {filepath}")
#                     # ارفع على تيليجرام لو مفعّل
#                     if SEND_VIDEO_TO_TELEGRAM:
#                         from notifier import send_video_to_telegram
#                         logger.info("📤 جاري رفع الفيديو على تيليجرام...")
#                         success = send_video_to_telegram(
#                             file_path=filepath,
#                             episode_num=episode_num,
#                             caption=f"🎬 {series_name} - الحلقة {episode_num}"
#                         )
#                         if success:
#                             logger.info("✅ تم رفع الفيديو على تيليجرام")
#                         else:
#                             logger.warning("⚠️ فشل رفع الفيديو على تيليجرام")
#                     try:
#                         file_size = os.path.getsize(filepath)
#                         size_mb = file_size / (1024 * 1024)
                        
#                         if size_mb > 1024:
#                             size_str = f"{size_mb / 1024:.2f} GB"
#                         else:
#                             size_str = f"{size_mb:.0f} MB"
                        
#                         message = (
#                             f"✅ <b>تم تحميل الحلقة {episode_num}!</b>\n\n"
#                             # f"📺 {series_name}\n"
#                             # f"📁 <code>{filepath}</code>\n"
#                             # f"📊 الحجم: <b>{size_str}</b>\n"
#                             # f"🎬 الجودة: <b>{DOWNLOAD_QUALITY}p</b>"
#                         )
                        
#                         send_telegram(message)
                    
#                     except Exception as e:
#                         logger.error(f"⚠️ فشل إرسال إشعار التحميل: {e}")


#                     return filepath
#         else:
#             logger.error(f"❌ فشل التحميل: {result.stderr}")

#             try:

#                 send_telegram(
#                     f"⚠️ <b>فشل تحميل الحلقة {episode_num}</b>\n\n"
#                     # f"📺 {series_name}\n"
#                     # f"❌ السبب: <code>{result.stderr[:200]}</code>"
#                 )
#             except:
#                 pass
#             return None
    
#     except subprocess.TimeoutExpired:
#         logger.error("❌ انتهت مهلة التحميل")
#         return None
#     except Exception as e:
#         logger.error(f"❌ خطأ في التحميل: {e}")
#         return None


# # ================== اختبار سريع ==================
# if __name__ == "__main__":
#     import sys
#     logging.basicConfig(level=logging.INFO)
    
#     if len(sys.argv) < 2:
#         print("الاستخدام: python downloader.py <m3u8_url>")
#         sys.exit(1)
    
#     download_video(sys.argv[1], 13, "Test_Series")


"""
تحميل الفيديو + رفع على GitHub Releases + إرسال الرابط على تيليجرام
"""

import subprocess
import os
import requests
from pathlib import Path
from config import (
    DOWNLOAD_DIR, DOWNLOAD_QUALITY,
    GITHUB_USERNAME, GITHUB_REPO, GITHUB_TOKEN,
    UPLOAD_TO_GITHUB, CLEANUP_DAYS
)
import logging

logger = logging.getLogger(__name__)


def download_video(video_url, episode_num, series_name):
    """
    يحمّل الفيديو، يرفعه على GitHub Releases، ويبعت الرابط على تيليجرام
    
    Args:
        video_url: رابط m3u8
        episode_num: رقم الحلقة
        series_name: اسم المسلسل
    
    Returns:
        str: رابط التحميل من GitHub أو None
    """
    # أنشئ مجلد التحميل
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
    # اسم الملف
    safe_name = series_name.replace(" ", "_").replace("/", "_")
    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{safe_name}_E{episode_num:02d}.%(ext)s"
    )
    
    # حدد صيغة التحميل
    if DOWNLOAD_QUALITY == "best":
        format_spec = "bestvideo+bestaudio/best"
    else:
        format_spec = (
            f"bestvideo[height<={DOWNLOAD_QUALITY}]+bestaudio/"
            f"best[height<={DOWNLOAD_QUALITY}]"
        )
    
    cmd = [
        "yt-dlp",
        "-f", format_spec,
        "--merge-output-format", "mp4",
        "-o", output_template,
        "--no-playlist",
        "--no-warnings",
        video_url
    ]
    
    logger.info(f"⬇️ بدء التحميل بجودة {DOWNLOAD_QUALITY}p...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # ساعتين max
        )
        
        if result.returncode != 0:
            logger.error(f"❌ فشل التحميل: {result.stderr[:500]}")
            return None
        
        # ابحث عن الملف الناتج
        filepath = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(f"{safe_name}_E{episode_num:02d}"):
                filepath = os.path.join(DOWNLOAD_DIR, f)
                break
        
        if not filepath:
            logger.error("❌ لم يتم العثور على الملف المحمّل")
            return None
        
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        logger.info(f"✅ تم التحميل: {filepath} ({file_size_mb:.1f} MB)")
        
        # ========== ارفع على GitHub Releases ==========
        if UPLOAD_TO_GITHUB:
            logger.info("📤 جاري الرفع على GitHub Releases...")
            release_url = upload_to_github_release(
                filepath, episode_num, series_name
            )
            
            if release_url:
                logger.info(f"✅ تم الرفع: {release_url}")
                
                # ابعت الرابط على تيليجرام
                from notifier import notify_github_release
                notify_github_release(episode_num, series_name, release_url)
                
                return release_url
            else:
                logger.warning("⚠️ فشل الرفع على GitHub")
                return filepath
        
        return filepath
    
    except subprocess.TimeoutExpired:
        logger.error("❌ انتهت مهلة التحميل")
        return None
    except Exception as e:
        logger.error(f"❌ خطأ في التحميل: {e}", exc_info=True)
        return None


def upload_to_github_release(filepath, episode_num, series_name):
    """
    يرفع الفيديو على GitHub Releases ويرجع رابط التحميل
    
    Args:
        filepath: مسار الملف المحلي
        episode_num: رقم الحلقة
        series_name: اسم المسلسل
    
    Returns:
        str: رابط التحميل المباشر أو None
    """
    if not GITHUB_TOKEN:
        logger.error("❌ GITHUB_TOKEN مش موجود")
        return None
    
    tag = f"v{episode_num}"
    release_name = f"{series_name} - الحلقة {episode_num}"
    
    api_base = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # ========== 1. اعمل Release جديد ==========
        # لو الـ Release موجود، امسحه الأول
        existing = requests.get(
            f"{api_base}/releases/tags/{tag}",
            headers=headers,
            timeout=30
        )
        
        if existing.status_code == 200:
            old_release = existing.json()
            logger.info(f"⚠️ Release {tag} موجود، جاري حذفه...")
            requests.delete(
                f"{api_base}/releases/{old_release['id']}",
                headers=headers,
                timeout=30
            )
            requests.delete(
                f"{api_base}/git/refs/tags/{tag}",
                headers=headers,
                timeout=30
            )
        
        # اعمل Release جديد
        release_data = {
            "tag_name": tag,
            "name": release_name,
            "body": (
                f"الحلقة {episode_num} من {series_name}\n\n"
                f"⏳ الرابط صالح لمدة {CLEANUP_DAYS} يوم"
            ),
            "draft": False,
            "prerelease": False
        }
        
        r = requests.post(
            f"{api_base}/releases",
            headers=headers,
            json=release_data,
            timeout=30
        )
        r.raise_for_status()
        release = r.json()
        upload_url_template = release["upload_url"]
        
        # ========== 2. ارفع الملف ==========
        filename = os.path.basename(filepath)
        # نظّف اسم الملف من الرموز اللي ممكن تسبب مشاكل
        filename = filename.replace(" ", "_")
        upload_url = upload_url_template.replace(
            "{?name,label}",
            f"?name={filename}"
        )
        
        file_size = os.path.getsize(filepath)
        logger.info(f"📊 حجم الملف: {file_size / (1024*1024):.1f} MB")
        logger.info(f"⬆️ جاري الرفع...")
        
        with open(filepath, "rb") as f:
            upload_headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Content-Type": "application/octet-stream"
            }
            
            r = requests.post(
                upload_url,
                headers=upload_headers,
                data=f,
                timeout=1800  # 30 دقيقة max للرفع
            )
            r.raise_for_status()
            asset = r.json()
        
        # ========== 3. رجّع رابط التحميل ==========
        download_url = asset["browser_download_url"]
        return download_url
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ فشل الرفع على GitHub: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response: {e.response.text[:500]}")
        return None
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع في الرفع: {e}", exc_info=True)
        return None


# ================== اختبار سريع ==================
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s"
    )
    
    if len(sys.argv) < 2:
        print("الاستخدام: python downloader.py <m3u8_url>")
        sys.exit(1)
    
    video_url = sys.argv[1]
    download_video(video_url, 14, "Test Series")
