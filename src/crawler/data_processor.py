"""
Data Processor for Genshin Impact Wiki Data
Cleans and structures the raw crawled data for RAG pipeline
"""

import json
import re
import os
from typing import List, Dict, Optional
from datetime import datetime


class GenshinDataProcessor:
    """Process and clean raw wiki data for RAG"""

    def __init__(self, input_dir: str = "data/raw", output_dir: str = "data/processed"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def clean_text(self, text: str) -> str:
        """
        Clean raw text from wiki

        Args:
            text: Raw text with formatting issues

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove reference markers like [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)

        # Remove edit markers
        text = re.sub(r'\[edit\]', '', text)

        # Add space before capital letters that are stuck together
        # e.g., "AlbedoKreideprinz" -> "Albedo Kreideprinz"
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

        # Add space before numbers stuck to words
        # e. g., "Version2. 1" -> "Version 2.1"
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)

        # Fix common patterns
        patterns = [
            (r'(\w)(Card|Wish|In-Game|Quality|Weapon|Element|Model)', r'\1 \2'),
            (r'(Type|Bonus|Roles|Bio|Birthday|Region|Dish|Namecard)([\w])', r'\1 \2'),
            (r'(English|Chinese|Japanese|Korean)([A-Z])', r'\1 \2'),
            (r'(Playable Characters)(\w)', r'\1.  \2'),
            (r'ⓘ', ''),  # Remove info icon
            (r'‍', ''),  # Remove zero-width joiner
        ]

        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Clean up spaces before punctuation
        text = re.sub(r'\s+([.,!?])', r'\1', text)

        return text.strip()

    def extract_character_info(self, raw_data: Dict) -> Dict:
        """
        Extract and structure character information

        Args:
            raw_data: Raw character data from crawler

        Returns:
            Structured character data
        """
        name = raw_data.get('name', 'Unknown')
        intro = raw_data.get('introduction', '')

        # Parse basic info from introduction
        info = {
            'name': name,
            'url': raw_data.get('url', ''),
            'element': self._extract_field(intro, ['Pyro', 'Hydro', 'Electro', 'Cryo', 'Anemo', 'Geo', 'Dendro']),
            'weapon': self._extract_field(intro, ['Sword', 'Claymore', 'Polearm', 'Bow', 'Catalyst']),
            'rarity': self._extract_rarity(intro),
            'region': self._extract_field(intro,
                                          ['Mondstadt', 'Liyue', 'Inazuma', 'Sumeru', 'Fontaine', 'Natlan', 'Snezhnaya',
                                           'Khaenri\'ah', 'Nod-Krai']),
            'model_type': self._extract_model_type(intro),
        }

        # Extract birthday
        birthday_match = re.search(r'Birthday([A-Z][a-z]+ \d+)', intro)
        if birthday_match:
            info['birthday'] = birthday_match.group(1)

        # Clean introduction text
        info['description'] = self._create_description(name, intro)

        # Clean sections
        sections = raw_data.get('sections', {})
        info['sections'] = {
            self._clean_section_name(k): self.clean_text(v)
            for k, v in sections.items()
        }

        # Create clean full text for RAG
        info['full_text'] = self._create_full_text(info)

        return info

    def _extract_field(self, text: str, options: List[str]) -> Optional[str]:
        """Extract a field value from text"""
        for option in options:
            if option.lower() in text.lower():
                return option
        return None

    def _extract_rarity(self, text: str) -> Optional[int]:
        """Extract character rarity (4 or 5 star)"""
        if '5' in text[: 200]:  # Usually in Quality section
            return 5
        elif '4' in text[: 200]:
            return 4
        return None

    def _extract_model_type(self, text: str) -> Optional[str]:
        """Extract character model type"""
        model_types = ['Tall Male', 'Tall Female', 'Medium Male', 'Medium Female', 'Short Male', 'Short Female']
        for model in model_types:
            if model.lower().replace(' ', '') in text.lower().replace(' ', ''):
                return model
        return None

    def _clean_section_name(self, name: str) -> str:
        """Clean section name"""
        # Remove [] and extra characters
        name = re.sub(r'\[\]', '', name)
        name = re.sub(r'\[.*?\]', '', name)
        return name.strip()

    def _create_description(self, name: str, intro: str) -> str:
        """Create a clean description from introduction"""
        # Find the actual description part (after "Playable Characters")
        parts = re.split(r'Playable Characters\. ?\s*', intro)

        if len(parts) > 1:
            description = parts[-1]
        else:
            description = intro

        # Clean it
        description = self.clean_text(description)

        # Remove the part before character name if exists
        name_pos = description.find(f"{name} is")
        if name_pos > 0:
            description = description[name_pos:]

        return description

    def _create_full_text(self, info: Dict) -> str:
        """Create clean full text for RAG indexing"""
        parts = []

        # Header
        parts.append(f"# {info['name']}")
        parts.append("")

        # Basic info
        parts.append("## Basic Information")
        if info.get('element'):
            parts.append(f"- Element: {info['element']}")
        if info.get('weapon'):
            parts.append(f"- Weapon: {info['weapon']}")
        if info.get('rarity'):
            parts.append(f"- Rarity: {info['rarity']}-Star")
        if info.get('region'):
            parts.append(f"- Region: {info['region']}")
        if info.get('model_type'):
            parts.append(f"- Model: {info['model_type']}")
        if info.get('birthday'):
            parts.append(f"- Birthday: {info['birthday']}")

        parts.append("")

        # Description
        if info.get('description'):
            parts.append("## Description")
            parts.append(info['description'])
            parts.append("")

        # Other sections
        for section_name, section_content in info.get('sections', {}).items():
            if section_content and len(section_content) > 20:
                parts.append(f"## {section_name}")
                parts.append(section_content)
                parts.append("")

        return '\n'.join(parts)

    def process_characters(self, input_file: str = "characters_latest.json") -> List[Dict]:
        """
        Process all characters from raw data file

        Args:
            input_file: Input filename in input_dir

        Returns:
            List of processed character data
        """
        input_path = os.path.join(self.input_dir, input_file)

        print(f"Loading raw data from: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        print(f"Processing {len(raw_data)} characters...")

        processed = []
        for char in raw_data:
            processed_char = self.extract_character_info(char)
            processed.append(processed_char)

        print(f"Processed {len(processed)} characters")

        return processed

    def save_processed_data(self, data: List[Dict], filename: str = "characters_processed.json"):
        """Save processed data to file"""
        output_path = os.path.join(self.output_dir, filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Saved to: {output_path}")

        return output_path

    def create_chunks(self, data: List[Dict], chunk_size: int = 500) -> List[Dict]:
        """
        Create text chunks for RAG indexing

        Args:
            data:  Processed character data
            chunk_size:  Approximate characters per chunk

        Returns:
            List of chunks with metadata
        """
        chunks = []

        for char in data:
            full_text = char.get('full_text', '')
            name = char.get('name', 'Unknown')

            # Split into paragraphs
            paragraphs = full_text.split('\n\n')

            current_chunk = ""
            current_section = "General"

            for para in paragraphs:
                # Track section headers
                if para.startswith('## '):
                    current_section = para.replace('## ', '').strip()

                # Add to current chunk or create new
                if len(current_chunk) + len(para) < chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    # Save current chunk
                    if current_chunk.strip():
                        chunks.append({
                            'character': name,
                            'section': current_section,
                            'content': current_chunk.strip(),
                            'metadata': {
                                'element': char.get('element'),
                                'weapon': char.get('weapon'),
                                'region': char.get('region'),
                                'url': char.get('url')
                            }
                        })
                    current_chunk = para + "\n\n"

            # Don't forget last chunk
            if current_chunk.strip():
                chunks.append({
                    'character': name,
                    'section': current_section,
                    'content': current_chunk.strip(),
                    'metadata': {
                        'element': char.get('element'),
                        'weapon': char.get('weapon'),
                        'region': char.get('region'),
                        'url': char.get('url')
                    }
                })

        print(f"Created {len(chunks)} chunks from {len(data)} characters")

        return chunks


def main():
    """Main function to process data"""

    print("=" * 60)
    print("GENSHIN DATA PROCESSOR")
    print("=" * 60)

    processor = GenshinDataProcessor()

    # Process characters
    processed_data = processor.process_characters("characters_latest.json")

    # Save processed data
    processor.save_processed_data(processed_data, "characters_processed.json")

    # Create chunks for RAG
    chunks = processor.create_chunks(processed_data)
    processor.save_processed_data(chunks, "characters_chunks.json")

    # Show sample
    print("\n" + "=" * 60)
    print("SAMPLE PROCESSED DATA")
    print("=" * 60)

    if processed_data:
        sample = processed_data[0]
        print(f"\nCharacter: {sample['name']}")
        print(f"Element:  {sample.get('element', 'N/A')}")
        print(f"Weapon:  {sample.get('weapon', 'N/A')}")
        print(f"Region: {sample.get('region', 'N/A')}")
        print(f"\nDescription (first 300 chars):")
        print(sample.get('description', 'N/A')[:300])
        print("\n--- Full Text Preview ---")
        print(sample.get('full_text', 'N/A')[:500])


if __name__ == "__main__":
    main()