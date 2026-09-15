"""
حذف الـ Releases القديمة (أكبر من CLEANUP_DAYS يوم)
"""

import requests
from datetime import datetime, timedelta
from config import (
    GITHUB_USERNAME, GITHUB_REPO, GITHUB_TOKEN, CLEANUP_DAYS
)
import logging

logger = logging.getLogger(__name__)


def cleanup_old_releases():
    """يمسح الـ Releases الأقدم من CLEANUP_DAYS"""
    
    if not GITHUB_TOKEN:
        logger.warning("⚠️ GITHUB_TOKEN مش موجود، تخطي التنظيف")
        return
    
    api_base = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # 1. جيب كل الـ Releases
        r = requests.get(f"{api_base}/releases", headers=headers, timeout=30)
        r.raise_for_status()
        releases = r.json()
        
        logger.info(f"📋 عدد الـ Releases: {len(releases)}")
        
        # 2. حدد التاريخ
        cutoff = datetime.now() - timedelta(days=CLEANUP_DAYS)
        deleted_count = 0
        
        # 3. افحص كل Release
        for release in releases:
            created_at = datetime.strptime(
                release["created_at"], "%Y-%m-%dT%H:%M:%SZ"
            )
            
            if created_at < cutoff:
                tag = release["tag_name"]
                logger.info(f"🗑️ حذف Release: {tag} (تاريخ: {created_at.date()})")
                
                # امسح الـ Release
                del_r = requests.delete(
                    f"{api_base}/releases/{release['id']}",
                    headers=headers,
                    timeout=30
                )
                
                if del_r.status_code == 204:
                    logger.info(f"✅ تم حذف {tag}")
                    deleted_count += 1
                    
                    # امسح الـ tag كمان
                    requests.delete(
                        f"{api_base}/git/refs/tags/{tag}",
                        headers=headers,
                        timeout=30
                    )
                else:
                    logger.warning(f"⚠️ فشل حذف {tag}: {del_r.status_code}")
        
        logger.info(f"✅ تم حذف {deleted_count} Release قديم")
        return deleted_count
    
    except Exception as e:
        logger.error(f"❌ خطأ في التنظيف: {e}")
        return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cleanup_old_releases()
