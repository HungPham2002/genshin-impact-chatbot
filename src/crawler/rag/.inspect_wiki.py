"""
Quick script to inspect Genshin Wiki HTML structure
"""

import requests
from bs4 import BeautifulSoup


def inspect_character_page():
    """Inspect the character list page structure"""

    url = "https://genshin-impact.fandom.com/wiki/Character"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print(f"Fetching: {url}\n")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')

    # Method 1: Find all tables
    print("=" * 60)
    print("METHOD 1: Looking for tables...")
    print("=" * 60)
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables\n")

    for i, table in enumerate(tables[: 5]):  # Check first 5 tables
        print(f"\n--- Table {i + 1} ---")
        # Get table class
        table_class = table.get('class', [])
        print(f"Classes: {table_class}")

        # Find links in table
        links = table.find_all('a', href=True)[:10]  # First 10 links
        print(f"Links found: {len(links)}")

        for link in links[: 5]:
            href = link.get('href', '')
            title = link.get('title', link.text.strip())
            if '/wiki/' in href and title:
                print(f"  - {title}:  {href}")

    # Method 2: Find character cards/divs
    print("\n" + "=" * 60)
    print("METHOD 2: Looking for character cards...")
    print("=" * 60)

    # Common Fandom wiki patterns
    patterns = [
        {'class': 'card'},
        {'class': 'character-card'},
        {'class': 'article-card'},
        {'class': 'category-page__member'},
    ]

    for pattern in patterns:
        cards = soup.find_all('div', pattern)
        if cards:
            print(f"\nFound {len(cards)} elements with {pattern}")
            for card in cards[: 3]:
                link = card.find('a')
                if link:
                    print(f"  - {link.get('title', 'No title')}: {link.get('href', '')}")

    # Method 3: Find all wiki links
    print("\n" + "=" * 60)
    print("METHOD 3: All /wiki/ links (filtered)...")
    print("=" * 60)

    all_links = soup.find_all('a', href=lambda x: x and '/wiki/' in x)

    # Filter to likely character pages
    char_keywords = ['Character', 'Traveler']
    filtered_links = []

    for link in all_links:
        href = link.get('href', '')
        title = link.get('title', link.text.strip())

        # Filter out common non-character pages
        skip_keywords = ['Category:', 'File:', 'Template:', 'User:', 'Special:',
                         'Talk:', 'Help:', 'Forum:', 'Blog:', 'Message', 'Comment']

        if any(skip in href for skip in skip_keywords):
            continue

        if title and len(title) > 2 and len(title) < 50:
            filtered_links.append({
                'title': title,
                'href': href
            })

    # Deduplicate
    seen = set()
    unique_links = []
    for link in filtered_links:
        if link['title'] not in seen and link['href'] not in seen:
            seen.add(link['title'])
            seen.add(link['href'])
            unique_links.append(link)

    print(f"\nFound {len(unique_links)} unique wiki links")
    print("\nFirst 20 links:")
    for link in unique_links[:20]:
        print(f"  - {link['title']}: {link['href']}")

    # Method 4: Look for specific sections
    print("\n" + "=" * 60)
    print("METHOD 4: Looking for 'Playable Characters' section...")
    print("=" * 60)

    # Find headings
    headings = soup.find_all(['h2', 'h3', 'h4'])
    for heading in headings:
        text = heading.get_text(strip=True)
        if 'Playable' in text or 'Character' in text:
            print(f"\nFound heading: '{text}'")

            # Get next sibling (usually the content)
            next_elem = heading.find_next_sibling()
            if next_elem:
                print(f"Next element: {next_elem.name}, classes: {next_elem.get('class', [])}")

                # Find links in next element
                links = next_elem.find_all('a', href=True)[:10]
                for link in links:
                    title = link.get('title', link.text.strip())
                    href = link.get('href', '')
                    if title and '/wiki/' in href:
                        print(f"  - {title}: {href}")


if __name__ == "__main__":
    inspect_character_page()