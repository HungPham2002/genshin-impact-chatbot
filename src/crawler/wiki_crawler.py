"""
Genshin Impact Wiki Crawler
Scrapes character, weapon, and artifact data from Genshin Impact Fandom Wiki
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import os
import re
from typing import List, Dict, Optional
from tqdm import tqdm


class GenshinWikiCrawler:
    """Crawler for Genshin Impact Fandom Wiki"""

    BASE_URL = "https://genshin-impact.fandom.com"

    def __init__(self, delay: float = 2.0, output_dir: str = "data/raw"):
        """
        Initialize the crawler

        Args:
            delay: Delay between requests in seconds (be respectful!)
            output_dir: Directory to save raw data
        """
        self.delay = delay
        self. output_dir = output_dir
        self.session = requests. Session()
        self.session.headers. update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Create output directory if not exists
        os. makedirs(output_dir, exist_ok=True)

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return BeautifulSoup object

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            time.sleep(self. delay)  # Be respectful to the server
            response = self.session.get(url, timeout=15)
            response. raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"Error fetching {url}:  {e}")
            return None

    def get_character_list(self) -> List[Dict[str, str]]:
        """
        Get list of all playable characters from the Character/List page

        Returns:
            List of dicts with character name and URL
        """
        # Use the sortable table page - much better structure!
        url = f"{self. BASE_URL}/wiki/Character/List"
        print(f"Fetching character list from:  {url}")

        soup = self.get_page(url)

        if not soup:
            return []

        characters = []
        seen_names = set()  # Avoid duplicates

        # Find the main sortable table (class:  fandom-table article-table sortable)
        tables = soup.find_all('table', class_='sortable')

        print(f"Found {len(tables)} sortable tables")

        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header row

            for row in rows:
                # Find the first link in the row (usually character name)
                cells = row.find_all('td')

                if not cells:
                    continue

                # Character name is typically in first or second cell
                for cell in cells[: 2]:
                    link = cell.find('a', href=True)
                    if link:
                        href = link. get('href', '')
                        title = link.get('title', '').strip()

                        # Filter valid character links
                        if (title
                            and '/wiki/' in href
                            and ': ' not in href  # Skip Category: , File:, etc.
                            and title not in seen_names
                            and len(title) > 1
                            and len(title) < 30):

                            # Additional filter: skip non-character pages
                            skip_keywords = ['Element', 'Weapon', 'Rarity', 'Region',
                                           'Nation', 'Model', 'Release', 'List']

                            if not any(kw. lower() in title.lower() for kw in skip_keywords):
                                seen_names.add(title)
                                full_url = self.BASE_URL + href if href. startswith('/') else href

                                characters.append({
                                    'name': title,
                                    'url': full_url
                                })
                        break  # Only need first valid link per row

        print(f"Total playable characters found: {len(characters)}")

        # Print first 10 for verification
        print("\nFirst 10 characters:")
        for char in characters[:10]:
            print(f"  - {char['name']}")

        return characters

    def scrape_character_page(self, url: str) -> Optional[Dict]:
        """
        Scrape a single character page

        Args:
            url: Character page URL

        Returns:
            Dict with character data
        """
        soup = self.get_page(url)

        if not soup:
            return None

        # Extract character name from page title
        title_elem = soup.find('h1', class_='page-header__title')
        if not title_elem:
            title_elem = soup. find('h1')

        char_name = title_elem.text.strip() if title_elem else "Unknown"

        # Extract infobox data (character details)
        infobox = {}
        infobox_elem = soup.find('aside', class_='portable-infobox')

        if infobox_elem:
            # Get all data items
            data_items = infobox_elem.find_all('div', class_='pi-item')
            for item in data_items:
                label = item.find('h3', class_='pi-data-label')
                value = item.find('div', class_='pi-data-value')

                if label and value:
                    key = label.get_text(strip=True)
                    val = value.get_text(strip=True)
                    infobox[key] = val

        # Extract main content
        content_div = soup.find('div', class_='mw-parser-output')

        if not content_div:
            return None

        # Get introduction paragraphs (before first heading)
        intro_paragraphs = []
        for elem in content_div. children:
            if elem.name == 'p':
                text = elem.get_text(strip=True)
                if text and len(text) > 20:  # Filter short/empty paragraphs
                    intro_paragraphs.append(text)
            elif elem.name in ['h2', 'h3']:
                break  # Stop at first heading

        # Get sections
        sections = {}
        current_section = None
        current_content = []

        for heading in content_div. find_all(['h2', 'h3']):
            # Save previous section
            if current_section and current_content:
                sections[current_section] = ' '.join(current_content)

            # Start new section
            span = heading.find('span', class_='mw-headline')
            if span:
                current_section = span.get_text(strip=True)
            else:
                current_section = heading.get_text(strip=True)

            # Clean section name (remove [edit] etc.)
            current_section = re.sub(r'\[.*?\]', '', current_section).strip()
            current_content = []

            # Get content until next heading
            for sibling in heading.find_next_siblings():
                if sibling.name in ['h2', 'h3']:
                    break
                if sibling.name == 'p':
                    text = sibling.get_text(strip=True)
                    if text and len(text) > 10:
                        current_content.append(text)

        # Save last section
        if current_section and current_content:
            sections[current_section] = ' '.join(current_content)

        # Build result
        result = {
            'name':  char_name,
            'url': url,
            'infobox': infobox,
            'introduction': ' '.join(intro_paragraphs),
            'sections': sections,
        }

        # Create full text for RAG
        full_text_parts = [f"Character: {char_name}"]

        if infobox:
            for key, value in infobox.items():
                full_text_parts.append(f"{key}: {value}")

        if intro_paragraphs:
            full_text_parts.append("Introduction:  " + ' '.join(intro_paragraphs))

        for section_name, section_content in sections.items():
            full_text_parts.append(f"{section_name}: {section_content}")

        result['full_text'] = '\n'.join(full_text_parts)

        return result

    def crawl_characters(self, max_chars: Optional[int] = None) -> List[Dict]:
        """
        Crawl all character pages

        Args:
            max_chars: Maximum number of characters to crawl (None for all)

        Returns:
            List of character data dicts
        """
        char_list = self. get_character_list()

        if not char_list:
            print("No characters found!  Check the crawler selectors.")
            return []

        if max_chars:
            char_list = char_list[: max_chars]

        all_data = []
        failed = []

        print(f"\nCrawling {len(char_list)} characters...")

        for char_info in tqdm(char_list, desc="Crawling characters"):
            char_data = self.scrape_character_page(char_info['url'])

            if char_data:
                all_data.append(char_data)
            else:
                failed.append(char_info['name'])

        if failed:
            print(f"\nFailed to crawl: {failed}")

        print(f"\nSuccessfully crawled:  {len(all_data)} characters")

        return all_data

    def save_data(self, data:  List[Dict], filename: str = "characters.json"):
        """
        Save crawled data to JSON file

        Args:
            data:  List of data dicts
            filename:  Output filename
        """
        filepath = os.path. join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(data)} items to {filepath}")

        return filepath


def main():
    """Main function for testing the crawler"""

    # Initialize crawler
    crawler = GenshinWikiCrawler(delay=1.5)

    # Test:  Get character list first
    print("="*60)
    print("STEP 1: Getting character list...")
    print("="*60)

    char_list = crawler. get_character_list()

    if not char_list:
        print("Failed to get character list.  Exiting.")
        return

    # Test: Crawl first 5 characters
    print("\n" + "="*60)
    print("STEP 2: Crawling first 5 characters...")
    print("="*60)

    char_data = crawler.crawl_characters(max_chars=5)

    # Save data
    if char_data:
        crawler.save_data(char_data, "characters_test.json")

        # Show sample
        print("\n" + "="*60)
        print("SAMPLE DATA (First character):")
        print("="*60)

        sample = char_data[0]
        print(f"Name: {sample['name']}")
        print(f"URL:  {sample['url']}")
        print(f"Infobox keys: {list(sample. get('infobox', {}).keys())}")
        print(f"Sections: {list(sample.get('sections', {}).keys())}")
        print(f"\nIntroduction (first 300 chars):")
        print(sample. get('introduction', 'N/A')[:300])
    else:
        print("No data crawled!")


if __name__ == "__main__":
    main()