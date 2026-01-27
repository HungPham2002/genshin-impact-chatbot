"""
Script to crawl all Genshin Impact characters
Run this script to collect full dataset
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.crawler.wiki_crawler import GenshinWikiCrawler
import json
from datetime import datetime


def main():
    """Crawl all characters and save to file"""

    print("=" * 60)
    print("🎮 GENSHIN IMPACT WIKI CRAWLER")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Initialize crawler with 1.5s delay (respectful crawling)
    crawler = GenshinWikiCrawler(delay=1.5, output_dir="data/raw")

    # Crawl ALL characters (no limit)
    print("Step 1: Getting character list...")
    characters = crawler.crawl_characters(max_chars=None)

    if not characters:
        print("No characters crawled!  Exiting.")
        return

    # Save raw data
    print("\nStep 2: Saving data...")
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f"characters_full_{timestamp}.json"
    filepath = crawler.save_data(characters, filename)

    # Also save as latest
    crawler.save_data(characters, "characters_latest.json")

    # Summary
    print("\n" + "=" * 60)
    print("CRAWL COMPLETE!")
    print("=" * 60)
    print(f"Total characters:  {len(characters)}")
    print(f"Saved to: {filepath}")
    print(f"Also saved to: data/raw/characters_latest.json")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Show all character names
    print("\nAll characters crawled:")
    for i, char in enumerate(characters, 1):
        print(f"  {i: 2}. {char['name']}")


if __name__ == "__main__":
    main()