"""
استخراج قائمة الحلقات من صفحة المسلسل
"""

import asyncio
from playwright.async_api import async_playwright
from config import SERIES_URL, HEADLESS, REQUEST_DELAY
import logging

logger = logging.getLogger(__name__)


async def get_episodes():
    """
    يستخرج كل الحلقات من صفحة المسلسل
    
    Returns:
        list: قائمة بالحلقات مرتبة تنازليًا (الأحدث أولاً)
        كل حلقة عبارة عن dict:
        {
            "url": "https://...",
            "num": 13,
            "title": "مسلسل ... الحلقة 13 مترجمة",
            "is_ad": False,  # True لو معلمة بـ "إعلان"
            "image": "https://..."
        }
    """
    episodes = []
    
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
        page = await context.new_page()
        
        try:
            logger.info(f"🌐 فتح صفحة المسلسل: {SERIES_URL}")
            await page.goto(SERIES_URL, wait_until="networkidle", timeout=60000)
            
            # استنى الـ lazy loading يشتغل
            await page.wait_for_timeout(REQUEST_DELAY * 1000)
            
            # استخرج كل الحلقات بـ JavaScript
            raw_episodes = await page.evaluate("""
                () => {
                    const articles = document.querySelectorAll('article.postEp');
                    const result = [];
                    
                    articles.forEach(article => {
                        const link = article.querySelector('a[href*="/episode/"]');
                        if (!link) return;
                        
                        const numSpan = article.querySelector('.episodeNum span:nth-child(2)');
                        const titleEl = article.querySelector('.title');
                        const isAd = !!article.querySelector('.ribbon');
                        const img = article.querySelector('img.imgSer');
                        
                        result.push({
                            url: link.href,
                            num: numSpan ? parseInt(numSpan.textContent.trim()) : null,
                            title: titleEl ? titleEl.textContent.trim() : '',
                            is_ad: isAd,
                            image: img ? (img.dataset.src || img.src) : null
                        });
                    });
                    
                    return result;
                }
            """)
            
            # فلترة: خد الحلقات اللي ليها رقم صحيح
            episodes = [ep for ep in raw_episodes if ep.get("num")]
            
            # ترتيب تنازلي حسب رقم الحلقة
            episodes.sort(key=lambda x: x["num"], reverse=True)
            
            logger.info(f"📺 تم العثور على {len(episodes)} حلقة")
            
            if episodes:
                latest = episodes[0]
                status = "إعلان" if latest["is_ad"] else "متاحة"
                logger.info(f"🆕 أحدث حلقة: {latest['num']} ({status})")
        
        except Exception as e:
            logger.error(f"❌ خطأ في استخراج الحلقات: {e}")
        
        finally:
            await browser.close()
    
    return episodes


# ================== اختبار سريع ==================
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    
    episodes = asyncio.run(get_episodes())
    print(json.dumps(episodes[:3], ensure_ascii=False, indent=2))