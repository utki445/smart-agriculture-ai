"""
Soil Condition Dataset Builder
Downloads and organizes images for 4 soil condition classes:
  - healthy: Normal soil without visible defects
  - cracked: Dry stress cracks visible on soil surface
  - waterlogged: Saturated/flooded soil surface
  - compacted: Dense, lumpy, hard-packed soil

Uses DuckDuckGo image search to collect a diverse dataset.
"""

import os
import urllib.request
import time
import hashlib
import json
import ssl

# Disable SSL verification for downloads
ssl._create_default_https_context = ssl._create_unverified_context

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(PROJECT_ROOT, "IRSID_Dataset", "soil_conditions")
TARGET_PER_CLASS = 80  # Target images per class

# Search queries for each condition class
SEARCH_QUERIES = {
    "cracked": [
        "cracked dry soil surface close up",
        "soil desiccation cracks field",
        "drought cracked earth agricultural land",
        "dry cracked mud texture",
        "soil crack pattern close up farmland",
    ],
    "waterlogged": [
        "waterlogged soil field flooding",
        "saturated wet soil puddle agriculture",
        "flooded farm field muddy soil",
        "wet muddy soil surface close up",
        "waterlogged agricultural field after rain",
    ],
    "healthy": [
        "healthy fertile soil surface close up",
        "good quality farm soil texture",
        "rich dark agricultural soil surface",
        "tilled healthy soil field",
        "fertile loam soil close up",
    ],
    "compacted": [
        "compacted hard soil surface",
        "soil compaction agriculture problem",
        "dense hard packed soil surface", 
        "lumpy dry clod soil surface",
        "hard compacted clay soil field",
    ],
}


def download_image(url, save_path, timeout=10):
    """Download a single image from URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
            # Only save if it looks like an image (> 5KB)
            if len(data) > 5000:
                with open(save_path, 'wb') as f:
                    f.write(data)
                return True
    except Exception as e:
        pass
    return False


def search_and_download_duckduckgo(query, save_dir, max_images=20):
    """Search DuckDuckGo for images and download them."""
    import re
    
    count = 0
    try:
        # Use DuckDuckGo HTML search
        search_url = f"https://duckduckgo.com/?q={urllib.parse.quote(query + ' soil')}&iax=images&ia=images"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(search_url, headers=headers)
        
        # Use the vqd token approach for DDG image search
        token_url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
        req_token = urllib.request.Request(token_url, headers=headers)
        with urllib.request.urlopen(req_token, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        vqd_match = re.search(r'vqd=([\d-]+)', html)
        if not vqd_match:
            print(f"  Could not get DDG token for: {query}")
            return 0
        
        vqd = vqd_match.group(1)
        
        # Fetch image results
        img_url = f"https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}&vqd={vqd}&f=,,,,,&p=1"
        req_img = urllib.request.Request(img_url, headers=headers)
        with urllib.request.urlopen(req_img, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        results = data.get('results', [])
        for result in results[:max_images]:
            img_url = result.get('image', '')
            if not img_url or not any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                continue
            
            # Create unique filename from URL hash
            url_hash = hashlib.md5(img_url.encode()).hexdigest()[:10]
            ext = '.jpg'
            for e in ['.png', '.webp', '.jpeg']:
                if e in img_url.lower():
                    ext = e
                    break
            
            save_path = os.path.join(save_dir, f"{url_hash}{ext}")
            if os.path.exists(save_path):
                continue
            
            if download_image(img_url, save_path):
                count += 1
                print(f"    ✓ Downloaded: {url_hash}{ext}")
            
            time.sleep(0.3)  # Rate limit
            
    except Exception as e:
        print(f"  Error searching '{query}': {e}")
    
    return count


def main():
    print("=" * 60)
    print("  SOIL CONDITION DATASET BUILDER")
    print("=" * 60)
    
    os.makedirs(DATASET_DIR, exist_ok=True)
    
    total = 0
    for condition, queries in SEARCH_QUERIES.items():
        class_dir = os.path.join(DATASET_DIR, condition)
        os.makedirs(class_dir, exist_ok=True)
        
        existing = len([f for f in os.listdir(class_dir) if f.endswith(('.jpg', '.png', '.jpeg', '.webp'))])
        print(f"\n📁 {condition.upper()} — {existing} existing images")
        
        if existing >= TARGET_PER_CLASS:
            print(f"  Already have {existing}/{TARGET_PER_CLASS} images. Skipping.")
            continue
        
        class_total = existing
        for query in queries:
            needed = TARGET_PER_CLASS - class_total
            if needed <= 0:
                break
            
            print(f"  🔍 Searching: '{query}' (need {needed} more)")
            downloaded = search_and_download_duckduckgo(query, class_dir, max_images=min(needed, 20))
            class_total += downloaded
            print(f"  → Got {downloaded} images (total: {class_total}/{TARGET_PER_CLASS})")
            time.sleep(1)
        
        total += class_total
    
    print(f"\n{'=' * 60}")
    print(f"  DATASET SUMMARY")
    print(f"{'=' * 60}")
    for condition in SEARCH_QUERIES:
        class_dir = os.path.join(DATASET_DIR, condition)
        count = len([f for f in os.listdir(class_dir) if f.endswith(('.jpg', '.png', '.jpeg', '.webp'))])
        print(f"  {condition:15s}: {count} images")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
