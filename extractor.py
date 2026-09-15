"""
استخراج رابط الفيديو من 3 طبقات iframe
"""

import asyncio
import re
from playwright.async_api import async_playwright
from config import (
    HEADLESS, REQUEST_DELAY, PREFERRED_SERVER, MAX_RETRIES
)
import logging

logger = logging.getLogger(__name__)


async def extract_video_url(episode_url):
    """
    يستخرج رابط الفيديو (m3u8) من صفحة الحلقة
    
    المسار:
    1. صفحة الحلقة (shooflive.net) → iframe
    2. dilaymotion.cam → iframe (cdnplus.space)
    3. cdnplus.space → jwplayer() → رابط m3u8
    
    Args:
        episode_url: رابط صفحة الحلقة
    
    Returns:
        str: رابط m3u8 أو None
    """
    
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"🎬 محاولة {attempt}/{MAX_RETRIES} لاستخراج الفيديو")
        
        try:
            result = await _extract_video_url_impl(episode_url)
            if result:
                logger.info(f"✅ تم استخراج الرابط: {result[:80]}...")
                return result
        except Exception as e:
            logger.error(f"❌ فشلت المحاولة {attempt}: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(REQUEST_DELAY)
    
    logger.error("❌ فشل استخراج الرابط بعد كل المحاولات")
    return None


async def _extract_video_url_impl(episode_url):
    """التنفيذ الفعلي لاستخراج الرابط"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ar-EG"
        )
        
        try:
            # ========== المرحلة 1: صفحة الحلقة ==========
            page1 = await context.new_page()
            logger.info(f"📄 فتح صفحة الحلقة: {episode_url}")
            await page1.goto(episode_url, wait_until="domcontentloaded", timeout=60000)
            await page1.wait_for_timeout(2000)
            
            # استخرج iframe dilaymotion.cam
            dilay_iframe = await page1.query_selector("iframe[src*='dilaymotion']")
            if not dilay_iframe:
                # ابحث في أي iframe
                all_iframes = await page1.query_selector_all("iframe")
                for ifr in all_iframes:
                    src = await ifr.get_attribute("src")
                    if src and "dilaymotion" in src:
                        dilay_iframe = ifr
                        break
            
            if not dilay_iframe:
                logger.error("❌ لم يتم العثور على iframe dilaymotion")
                return None
            
            dilay_url = await dilay_iframe.get_attribute("src")
            logger.info(f"🔗 iframe 1: {dilay_url}")
            
            # ========== المرحلة 2: dilaymotion.cam ==========
            # أضف ?serv=N للسيرفر المفضل
            if "?" not in dilay_url:
                dilay_url += f"?serv={PREFERRED_SERVER}"
            elif "serv=" not in dilay_url:
                dilay_url += f"&serv={PREFERRED_SERVER}"
            
            page2 = await context.new_page()
            logger.info(f"📄 فتح dilaymotion: {dilay_url}")
            await page2.goto(dilay_url, wait_until="domcontentloaded", timeout=60000)
            await page2.wait_for_timeout(2000)
            
            # استخرج iframe cdnplus
            cdn_iframe = await page2.query_selector("iframe[src*='cdnplus']")
            if not cdn_iframe:
                all_iframes = await page2.query_selector_all("iframe")
                for ifr in all_iframes:
                    src = await ifr.get_attribute("src")
                    if src and "cdnplus" in src:
                        cdn_iframe = ifr
                        break
            
            if not cdn_iframe:
                logger.error("❌ لم يتم العثور على iframe cdnplus")
                return None
            
            cdn_url = await cdn_iframe.get_attribute("src")
            cdn_url = cdn_url.strip()  # إزالة المسافات
            logger.info(f"🔗 iframe 2: {cdn_url}")
            
            # ========== المرحلة 3: cdnplus.space ==========
            page3 = await context.new_page()
            logger.info(f"📄 فتح cdnplus: {cdn_url}")
            await page3.goto(cdn_url, wait_until="domcontentloaded", timeout=60000)
            
            # استنى jwplayer يتحمل
            await page3.wait_for_timeout(3000)
            
            # ========== المرحلة 4: استخراج الرابط ==========
            # الطريقة 1: من jwplayer
            video_url = await page3.evaluate("""
                () => {
                    try {
                        if (typeof jwplayer === 'function') {
                            const player = jwplayer();
                            if (player && player.getPlaylistItem) {
                                const item = player.getPlaylistItem();
                                if (item && item.file) return item.file;
                            }
                        }
                    } catch(e) {}
                    return null;
                }
            """)
            
            if video_url:
                logger.info(f"✅ jwplayer أعطى الرابط")
                return video_url
            
            # الطريقة 2: من Network (اعتراض طلبات m3u8)
            logger.info("⚠️ jwplayer لم يعمل، جرب اعتراض الشبكة...")
            
            # أعد تحميل الصفحة مع اعتراض الطلبات
            m3u8_urls = []
            
            def handle_request(request):
                url = request.url
                if ".m3u8" in url and "master" in url:
                    m3u8_urls.append(url)
            
            page3.on("request", handle_request)
            await page3.reload(wait_until="domcontentloaded")
            await page3.wait_for_timeout(5000)
            
            if m3u8_urls:
                logger.info(f"✅ تم اعتراض {len(m3u8_urls)} رابط m3u8")
                return m3u8_urls[0]
            
            logger.error("❌ لم يتم العثور على رابط m3u8")
            return None
        
        finally:
            await browser.close()


# ================== اختبار سريع ==================
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://shooflive.net/episode/مسلسل-إسطنبول-رأساً-على-عقب-الحلقة-13-مت/"
    
    video_url = asyncio.run(extract_video_url(url))
    print(f"\n🎬 الرابط: {video_url}")