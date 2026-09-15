"""
السكريبت الرئيسي - يراقب المسلسل ويكتشف الحلقات الجديدة
"""

import asyncio
import json
import os
import sys
from datetime import datetime

from config import (
    SERIES_NAME, SERIES_URL, STATE_FILE, LOG_FILE,
    AUTO_DOWNLOAD, REQUEST_DELAY
)
from scraper import get_episodes
from extractor import extract_video_url
from downloader import download_video
from notifier import (
    notify_new_episode, notify_error, notify_startup, send_telegram
)

import logging

# ================== إعداد السجل ==================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ================== إدارة الحالة ==================
def load_state():
    """يقرأ الحالة المحفوظة"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"⚠️ خطأ في قراءة الحالة: {e}")
    
    return {
        "last_episode_num": 0,
        "last_episode_url": None,
        "last_check": None,
        "processed_episodes": []
    }


def save_state(state):
    """يحفظ الحالة"""
    state["last_check"] = datetime.now().isoformat()
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ الحالة: {e}")


# ================== المنطق الرئيسي ==================
async def check_for_new_episode():
    logger.info("=" * 60)
    logger.info("🚀 بدء فحص الحلقات الجديدة")
    
    state = load_state()
    last_num = state.get("last_episode_num", 0)
    last_was_ad = state.get("last_was_ad", False)  # ← جديد
    logger.info(f"📌 آخر حلقة محفوظة: {last_num} (إعلان: {last_was_ad})")
    
    episodes = await get_episodes()
    if not episodes:
        logger.warning("⚠️ لم يتم العثور على حلقات")
        return
    
    latest = episodes[0]
    logger.info(f"🆕 أحدث حلقة: {latest['num']} - {'إعلان' if latest['is_ad'] else 'متاحة'}")
    
    # ========== أول تشغيل ==========
    if last_num == 0:
        logger.info("📌 أول تشغيل: حفظ الحالة فقط بدون إشعار")
        state["last_episode_num"] = latest["num"]
        state["last_episode_url"] = latest["url"]
        state["last_was_ad"] = latest["is_ad"]  # ← جديد
        save_state(state)
        return
    
    # ========== الحالة 1: نفس الرقم بس الإعلان اتشال ==========
    # (دي الحالة اللي كنا بنتكلم عنها)
    if latest["num"] == last_num and last_was_ad and not latest["is_ad"]:
        logger.info(f"🎊 الحلقة {latest['num']} نزلت فعليًا (اتشال الإعلان)!")
        # كمّل عادي عشان نستخرج الفيديو ونبعت إشعار
    
    # ========== الحالة 2: نفس الرقم ومفيش تغيير ==========
    elif latest["num"] == last_num and latest["is_ad"] == last_was_ad:
        logger.info("✅ مفيش جديد")
        return
    
    # ========== الحالة 3: حلقة جديدة ==========
    elif latest["num"] > last_num:
        logger.info(f"🎉 حلقة جديدة! {last_num} → {latest['num']}")
        
        if latest["is_ad"]:
            logger.info(f"⏳ الحلقة {latest['num']} معلمة بـ 'إعلان' - انتظار النزول الفعلي")
            state["last_episode_num"] = latest["num"]
            state["last_episode_url"] = latest["url"]
            state["last_was_ad"] = True  # ← جديد
            save_state(state)
            return
    
    # ========== الحالة 4: رقم أقل (نادرًا) ==========
    else:
        logger.info("⚠️ الرقم أقل من المحفوظ، تجاهل")
        return
    
    # ========== استخراج الفيديو ==========
    logger.info("🎬 استخراج رابط الفيديو...")
    video_url = await extract_video_url(latest["url"])
    
    if not video_url:
        logger.warning("⚠️ لم يتم استخراج رابط الفيديو")
    
    # ========== الإشعار ==========
    notify_new_episode(
        episode_num=latest["num"],
        episode_url=latest["url"],
        series_name=SERIES_NAME,
        video_url=video_url
    )
    
    # ========== التحميل ==========
    if AUTO_DOWNLOAD and video_url:
        download_video(video_url, latest["num"], SERIES_NAME)
    
    # ========== حفظ الحالة ==========
    state["last_episode_num"] = latest["num"]
    state["last_episode_url"] = latest["url"]
    state["last_was_ad"] = latest["is_ad"]  # ← جديد
    
    processed = state.get("processed_episodes", [])
    processed.append({
        "num": latest["num"],
        "url": latest["url"],
        "video_url": video_url,
        "date": datetime.now().isoformat()
    })
    state["processed_episodes"] = processed[-50:]
    
    save_state(state)
    logger.info("✅ اكتمل الفحص")

# ================== نقطة البداية ==================
def main():
    try:
        asyncio.run(check_for_new_episode())
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف النظام")
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {e}", exc_info=True)
        try:
            notify_error(str(e))
        except:
            pass


if __name__ == "__main__":
    main()
