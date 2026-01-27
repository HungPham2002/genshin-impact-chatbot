"""
Enhanced Data Processor for Genshin Impact Wiki Data
Improved cleaning and extraction for better RAG performance
Version 2.1 - Added more useful field extraction
"""

import json
import re
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class EnhancedGenshinProcessor:
    """Enhanced processor with better text cleaning and extraction"""

    # Known 5-star characters (for accurate rarity detection)
    FIVE_STAR_CHARS = {
        'Albedo', 'Alhaitham', 'Tartaglia', 'Lyney', 'Baizhu', 'Chasca', 'Chiori',
        'Citlali', 'Clorinde', 'Cyno', 'Dehya', 'Diluc', 'Eula', 'Furina',
        'Ganyu', 'Hu Tao', 'Itto', 'Jean', 'Kazuha', 'Keqing', 'Kinich',
        'Klee', 'Mavuika', 'Mona', 'Mualani', 'Nahida', 'Navia', 'Neuvillette',
        'Nilou', 'Qiqi', 'Raiden Shogun', 'Shenhe', 'Sigewinne', 'Tighnari',
        'Venti', 'Wanderer', 'Wriothesley', 'Xiao', 'Xianyun', 'Xilonen',
        'Yae Miko', 'Yelan', 'Yoimiya', 'Zhongli', 'Arlecchino', 'Emilie',
        'Kamisato Ayaka', 'Kamisato Ayato', 'Kaedehara Kazuha', 'Arataki Itto',
        'Sangonomiya Kokomi', 'Yae Miko', 'Raiden Shogun', 'Columbina',
        'Zibai', 'Ineffa', 'Nefer', 'Lauma', 'Flins', 'Aloy', 'Traveler',
        'Yumemizuki Mizuki', 'Durin', 'Escoffier', 'Skirk', 'Varesa'
    }

    # Noise patterns to remove from description (simplified, safe patterns)
    NOISE_PATTERNS = [
        r'Card\s*Wish\s*In-Game',
        r'Quality\s*Weapon',
        r'Element\s*Model\s*Type',
        r'Team\s*Bonus',
        r'Bio\s*Relatives',
        r'Voice\s*Actors',
        r'Additional\s*Titles\s*Categories',
        r'Moonsign',
        r'Hexerei',
        r'Arkhe',
        r'Pneuma\s*Ousia',
        r'Ousia',
        r'Pneuma',
    ]

    def __init__(self, input_dir: str = "data/raw", output_dir: str = "data/processed"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def clean_text(self, text: str) -> str:
        """Advanced text cleaning"""
        if not text:
            return ""

        # Remove reference markers
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\[edit\]', '', text)
        text = re.sub(r'\[Note\s*\d+\]', '', text)

        # Remove special unicode characters
        text = text.replace('ⓘ', '')
        text = text.replace('‍', '')
        text = text.replace('­', '')  # soft hyphen

        # Fix stuck words - add space before capitals after lowercase
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

        # Fix common stuck patterns
        stuck_patterns = [
            (r'(\w)(Card|Wish|Quality|Weapon|Element|Model)', r'\1 \2'),
            (r'(Type|Bonus|Roles|Bio|Birthday|Region|Dish)([\w])', r'\1 \2'),
            (r'(English|Chinese|Japanese|Korean)([A-Z])', r'\1 \2'),
            (r'(Playable\s*Characters)(\w)', r'\1. \2'),
            (r'(Genshin)(Impact)', r'\1 \2'),
            (r'(\w)(character)(in)', r'\1 \2 \3'),
            (r'(in)(Genshin)', r'\1 \2'),
        ]

        for pattern, replacement in stuck_patterns:
            text = re.sub(pattern, replacement, text)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([.,!?])', r'\1', text)

        return text.strip()

    def extract_character_roles(self, intro: str) -> Dict[str, bool]:
        """Extract character roles (On-Field, Off-Field, DPS, Support, Survivability)"""
        roles = {
            'on_field': False,
            'off_field': False,
            'dps': False,
            'support': False,
            'survivability': False
        }

        intro_lower = intro.lower()

        # Check for role keywords
        if 'on-field' in intro_lower or 'on field' in intro_lower:
            roles['on_field'] = True
        if 'off-field' in intro_lower or 'off field' in intro_lower:
            roles['off_field'] = True
        if 'dps' in intro_lower:
            roles['dps'] = True
        if 'support' in intro_lower:
            roles['support'] = True
        if 'survivability' in intro_lower or 'healing' in intro_lower or 'healer' in intro_lower:
            roles['survivability'] = True

        return roles

    def extract_how_to_obtain(self, intro: str) -> List[str]:
        """Extract how to obtain the character"""
        methods = []

        # Check for common obtain methods
        if 'wishes' in intro.lower() or 'wish' in intro.lower():
            methods.append('Wishes')
        if 'event wish' in intro.lower():
            # Try to extract event wish name
            match = re.search(r'Event Wish\s*[—-]\s*([^F]+?)(?: Featured|Release)', intro)
            if match:
                event_name = match.group(1).strip()
                methods.append(f'Event Wish: {event_name}')
        if 'chronicled wishes' in intro.lower():
            methods.append('Chronicled Wishes')
        if "paimon's bargains" in intro.lower():
            methods.append("Paimon's Bargains")
        if 'adventure rank' in intro.lower():
            methods.append('Adventure Rank Reward')
        if 'archon quest' in intro.lower() or 'complete' in intro.lower():
            methods.append('Quest Reward')

        return methods if methods else ['Wishes']

    def extract_release_date(self, intro: str) -> Optional[str]:
        """Extract character release date"""
        # Pattern:  Release Date Month DD, YYYY
        patterns = [
            r'Release\s*Date\s*([A-Z][a-z]+\s+\d{1,2},?\s*\d{4})',
            r'Released?\s*(?:on\s*)?([A-Z][a-z]+\s+\d{1,2},?\s*\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, intro)
            if match:
                return match.group(1).strip()

        return None

    def extract_voice_actors(self, intro: str) -> Dict[str, str]:
        """Extract voice actors for different languages"""
        voice_actors = {}

        # Patterns for each language
        patterns = {
            'english': r'English\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'chinese':  r'Chinese\s*([^\[\]]+?)(?:\s*\([^)]+\))?\s*(?:\[|Japanese)',
            'japanese': r'Japanese\s*([^\[\]]+?)(?:\s*\([^)]+\))?\s*(?:\[|Korean)',
            'korean': r'Korean\s*([^\[\]]+?)(?:\s*\([^)]+\))?\s*(?:\[|Additional)',
        }

        for lang, pattern in patterns.items():
            match = re.search(pattern, intro)
            if match:
                actor = match.group(1).strip()
                # Clean up the actor name
                actor = re.sub(r'\s*\([^)]*\)\s*', '', actor)
                actor = re.sub(r'\[\d+\]', '', actor)
                if actor and len(actor) > 1 and len(actor) < 50:
                    voice_actors[lang] = actor

        return voice_actors

    def extract_character_type(self, intro: str) -> str:
        """Extract if character is biological, synthetic, or adoptive"""
        intro_lower = intro.lower()

        if 'synthetic' in intro_lower:
            if 'creator' in intro_lower or 'created by' in intro_lower:
                return 'Synthetic (Created)'
            elif 'derived from' in intro_lower:
                return 'Synthetic (Derived)'
            return 'Synthetic'
        elif 'adoptive' in intro_lower:
            return 'Adoptive'
        else:
            return 'Biological'

    def extract_event_wishes(self, intro: str) -> Optional[int]:
        """Extract number of event wishes character has been featured in"""
        patterns = [
            r'promoted or featured with a drop-rate boost in\s*(\d+)\s*Event Wish',
            r'featured.*?(\d+)\s*Event Wish',
        ]

        for pattern in patterns:
            match = re.search(pattern, intro, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def extract_special_dish(self, intro: str) -> Optional[str]:
        """Extract character's special dish"""
        patterns = [
            r'Special\s*Dish\s*([A-Z][^N]+?)(?: Namecard|How)',
            r'Special\s*Dish([^N]+?)Namecard',
        ]

        for pattern in patterns:
            match = re.search(pattern, intro)
            if match:
                dish = match.group(1).strip()
                # Clean up
                dish = re.sub(r'\[\d+\]', '', dish)
                dish = dish.strip()
                if dish and len(dish) > 2 and len(dish) < 100:
                    return dish

        return None

    def extract_namecard(self, intro: str) -> Optional[str]:
        """Extract character's namecard"""
        patterns = [
            r'Namecard\s*([A-Z][^H]+?)(?:How|Featured|Release)',
            r'Namecard([^H]+?)How',
        ]

        for pattern in patterns:
            match = re.search(pattern, intro)
            if match:
                namecard = match.group(1).strip()
                namecard = re.sub(r'\[\d+\]', '', namecard)
                if namecard and len(namecard) > 2:
                    return namecard

        return None

    def extract_real_name(self, intro: str) -> Optional[str]:
        """Extract character's real name if different from display name"""
        patterns = [
            r'Real\s*Name\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, intro)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 2:
                    return name

        return None

    def extract_clean_description(self, *, name, intro, full_text, sections, url):
        """
        Extract a clean, lore-focused description for a character.
        Tiered, additive, regression-safe.
        """

        # =========================
        # Tier-2: System / mode characters (early return)
        # =========================
        if self._is_system_character(name, url, intro):
            return (
                "The Wonderland Manekin is a playable system character representing "
                "the Miliastra Wonderland gameplay mode in Genshin Impact."
            )

        description_parts = []

        # =========================
        # Tier-1.5: Official Introduction (highest priority narrative)
        # =========================
        official_intro = self._extract_official_intro(sections)
        if official_intro:
            description_parts.append(official_intro)

        # =========================
        # Prepare text for lore extraction ONLY
        # =========================
        # Important: do NOT mutate original intro globally
        fixed_intro = self._aggressive_spacing_fix(intro)

        # Sentence split AFTER aggressive spacing fix
        sentences = re.split(r'(?<=[.!?])\s+', fixed_intro)

        # =========================
        # Tier-0: Marker-based lore (Playable Characters, aliases)
        # =========================
        marker_lore = self._extract_marker_lore(fixed_intro, name)
        for s in marker_lore:
            if s not in description_parts:
                description_parts.append(s)

        # =========================
        # Tier-1: Role / identity reveal lore (Archon, Harbinger, Consultant, etc.)
        # =========================
        role_lore = self._extract_role_reveal_lore(sentences)
        for s in role_lore:
            if s not in description_parts:
                description_parts.append(s)

        # =========================
        # Existing scoring logic
        # =========================
        scored = []
        for s in sentences:
            s = s.strip()
            if 30 <= len(s) <= 400:
                score = self._score_sentence(s, name)
                scored.append((s, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        selected = [s for s, sc in scored if sc >= 4][:3]

        for s in selected:
            if s not in description_parts:
                description_parts.append(s)

        # =========================
        # Final fallback
        # =========================
        if description_parts:
            description = " ".join(description_parts[:3])
        else:
            # Extremely rare fallback
            description = sentences[0] if sentences else fixed_intro[:300]

        # =========================
        # Final cleanup
        # =========================
        description = self.clean_text(description)
        description = re.sub(r"\s+", " ", description).strip()

        return description

    def _score_sentence(self, sentence: str, name: str) -> int:
        s = sentence.lower()
        score = 0

        # Identity / lore signals
        IDENTITY_KEYWORDS = [
            'archon', 'god', 'deity', 'immortal',
            'former', 'current', 'leader', 'founder',
            'captain', 'consultant', 'knight',
            'descendant', 'wander', 'guardian'
        ]

        # Narrative openers
        if re.match(r'^(a|an|the)\s+', s):
            score += 3

        # Pronoun-based identity (Zhongli, Klee, Nahida)
        if re.search(r'\b(he|she)\s+is\b', s):
            score += 3

        # Name explicitly mentioned
        if name.lower() in s:
            score += 4

        # Identity keywords
        for kw in IDENTITY_KEYWORDS:
            if kw in s:
                score += 2

        # Penalty: obvious noise
        NOISE = [
            'voice actor', 'english', 'chinese', 'japanese',
            'birthday', 'constellation', 'release date',
            'featured', 'event wish', 'how to obtain'
        ]
        for n in NOISE:
            if n in s:
                score -= 4

        return score

    def _aggressive_spacing_fix(self, text: str) -> str:
        """
        Fix severe word-gluing issues common in fandom wiki text.
        Applied ONLY for lore extraction.
        """
        if not text:
            return text

        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = re.sub(r'(is)([A-Z])', r'\1 \2', text)
        text = re.sub(r'([a-zA-Z])(character)', r'\1 character', text, flags=re.I)
        text = re.sub(r'([a-zA-Z])(Archon)', r'\1 Archon', text)
        text = re.sub(r'([a-zA-Z])(Harbinger)', r'\1 Harbinger', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _extract_marker_lore(self, text: str, name: str) -> List[str]:
        """
        Tier-0: Extract lore immediately following strong semantic markers
        (Playable Characters, alias-based markers).
        """
        lore_sentences = []

        MARKERS = [
            rf'Playable Characters\s*{re.escape(name)}',
            rf'Playable Characters.*?{re.escape(name)}',
            rf'{re.escape(name)}\s+is\s+a\s+playable',
        ]

        for marker in MARKERS:
            match = re.search(marker, text, re.IGNORECASE)
            if match:
                tail = text[match.end(): match.end() + 800]
                sentences = re.split(r'(?<=[.!?])\s+', tail)
                for s in sentences[:3]:
                    s = s.strip()
                    if 40 <= len(s) <= 400:
                        lore_sentences.append(s)

        return lore_sentences

    def _extract_role_reveal_lore(self, sentences: List[str]) -> List[str]:
        """
        Tier-1: Identity / role reveal sentences that may not mention name.
        """
        patterns = [
            r'is later revealed to be',
            r'is the .*? archon',
            r'is the .*? harbinger',
            r'a consultant of',
            r'former .*? of',
            r'leader of',
            r'founder of',
            r'from another world',
            r'crossover character',
        ]

        results = []
        for s in sentences:
            s_low = s.lower()
            if any(re.search(p, s_low) for p in patterns):
                if 40 <= len(s) <= 300:
                    results.append(s.strip())

        return results

    def _extract_official_intro(self, sections: dict) -> Optional[str]:
        """
        Tier-1.5: Use Official Introduction if present and meaningful.
        """
        if not sections:
            return None

        for key, value in sections.items():
            if key.lower() == 'official introduction':
                if value and len(value) > 200:
                    return value.strip()

        return None

    def _is_system_character(self, name: str, url: str, intro: str) -> bool:
        text = f"{name} {url} {intro}".lower()
        return (
                'wonderland' in text
                or 'gameplay mode' in text
                or 'system character' in text
        )

    def extract_rarity(self, name: str, intro: str) -> int:
        """Extract character rarity with better accuracy"""
        # Check known 5-star list first
        name_parts = name.split()
        for part in name_parts:
            if part in self.FIVE_STAR_CHARS:
                return 5

        if name in self.FIVE_STAR_CHARS:
            return 5

        # Check for 5-star indicators in text
        five_star_indicators = ['5★', '5-Star', '5 Star', 'Quality5', '★★★★★']
        for indicator in five_star_indicators:
            if indicator.lower() in intro.lower():
                return 5

        # Default to 4-star for playable characters
        return 4

    def extract_title(self, intro: str) -> Optional[str]:
        """Extract character title/alias"""
        # Common title patterns
        title_patterns = [
            r'"([^"]+)"',  # Quoted titles
            r'also known as\s+"?([^",.\[\]]+)"?',
            r'known as\s+"?([^",.\[\]]+)"?',
            r'titled\s+"?([^",.\[\]]+)"?',
        ]

        for pattern in title_patterns:
            try:
                match = re.search(pattern, intro, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 3 and len(title) < 50:
                        return title
            except re.error:
                continue

        return None

    def extract_affiliation(self, intro: str) -> List[str]:
        """Extract character's affiliations/organizations"""
        affiliations = []

        affiliation_keywords = [
            'Knights of Favonius', 'Liyue Qixing', 'Fatui', "Adventurers' Guild",
            'Wangsheng Funeral Parlor', 'Yashiro Commission', 'Tenryou Commission',
            'Kamisato Clan', 'Arataki Gang', 'Watatsumi Army', 'Sumeru Akademiya',
            'Spina di Rosula', "Hotel Bouffes d'ete", 'House of the Hearth',
            'Maison Gardiennage', 'The Crux', 'Church of Favonius',
            'Grand Narukami Shrine', 'Sangonomiya Shrine', 'Shuumatsuban',
            'Hexenzirkel', 'Eleven Fatui Harbingers', 'The Seven',
            'Bubu Pharmacy', 'Adepti', 'Forest Rangers', 'Matra',
            'Temple of Silence', 'The Steambird', 'Zubayr Theater',
            'Lightkeepers', 'Three Moons', 'Frostmoon Scions'
        ]

        for affiliation in affiliation_keywords:
            if affiliation.lower() in intro.lower():
                affiliations.append(affiliation)

        return affiliations

    def extract_constellation(self, intro: str) -> Optional[str]:
        """Extract character constellation name"""
        # Fixed patterns - avoid problematic regex
        patterns = [
            r'Constellation\s*([A-Z][a-z]+\s*[A-Z]?[a-z]*)',
            r'lation\s*([A-Z][a-z]+\s*[A-Z]?[a-z]*)',
        ]

        for pattern in patterns:
            try:
                match = re.search(pattern, intro)
                if match:
                    constellation = match.group(1).strip()
                    # Validate it looks like a constellation name
                    if constellation and len(constellation) > 3 and not constellation.startswith('Story'):
                        return constellation
            except re.error:
                continue

        return None

    def process_character(self, raw_data: Dict) -> Dict:
        """Process a single character with enhanced extraction"""
        name = raw_data.get('name', 'Unknown')
        intro = raw_data.get('introduction', '')

        # Extract all fields
        info = {
            'name': name,
            'url': raw_data.get('url', ''),
            'element': self._extract_field(intro,
                                           ['Pyro', 'Hydro', 'Electro', 'Cryo', 'Anemo', 'Geo', 'Dendro']),
            'weapon': self._extract_field(intro,
                                          ['Sword', 'Claymore', 'Polearm', 'Bow', 'Catalyst']),
            'rarity': self.extract_rarity(name, intro),
            'region': self._extract_field(intro,
                                          ['Mondstadt', 'Liyue', 'Inazuma', 'Sumeru', 'Fontaine',
                                           'Natlan', 'Snezhnaya', "Khaenri'ah", 'Nod-Krai']),
            'model_type': self._extract_model_type(intro),
            'title': self.extract_title(intro),
            'affiliations': self.extract_affiliation(intro),
            'constellation':  self.extract_constellation(intro),
        }

        # NEW: Extract character roles
        roles = self.extract_character_roles(intro)
        info['roles'] = roles
        info['role_summary'] = self._create_role_summary(roles)

        # NEW: Extract how to obtain
        info['how_to_obtain'] = self.extract_how_to_obtain(intro)

        # NEW: Extract release date
        info['release_date'] = self.extract_release_date(intro)

        # NEW: Extract voice actors
        info['voice_actors'] = self.extract_voice_actors(intro)

        # NEW: Extract character type (biological/synthetic/adoptive)
        info['character_type'] = self.extract_character_type(intro)

        # NEW: Extract event wishes count
        info['event_wishes_count'] = self.extract_event_wishes(intro)

        # NEW: Extract special dish
        info['special_dish'] = self.extract_special_dish(intro)

        # NEW: Extract namecard
        info['namecard'] = self.extract_namecard(intro)

        # NEW: Extract real name
        info['real_name'] = self.extract_real_name(intro)

        # Extract birthday
        birthday_match = re.search(r'Birthday\s*([A-Z][a-z]+\s+\d+)', intro)
        if birthday_match:
            info['birthday'] = birthday_match.group(1)

        # Create clean description
        info['description'] = self.extract_clean_description(
            name=name,
            intro=intro,
            full_text=raw_data.get('full_text', ''),
            sections=raw_data.get('sections', {}),
            url=raw_data.get('url', '')
        )

        # Clean sections
        sections = raw_data.get('sections', {})
        info['sections'] = {
            self._clean_section_name(k): self.clean_text(v)
            for k, v in sections.items()
            if v and len(v) > 20
        }

        # Create optimized full text for RAG
        info['full_text'] = self._create_rag_text(info)

        return info

    def _create_role_summary(self, roles: Dict[str, bool]) -> str:
        """Create a human-readable role summary"""
        role_parts = []

        if roles.get('on_field'):
            role_parts.append('On-Field')
        if roles.get('off_field'):
            role_parts.append('Off-Field')
        if roles.get('dps'):
            role_parts.append('DPS')
        if roles.get('support'):
            role_parts.append('Support')
        if roles.get('survivability'):
            role_parts.append('Healer/Shielder')

        return ' / '.join(role_parts) if role_parts else 'Unknown'

    def _extract_field(self, text: str, options: List[str]) -> Optional[str]:
        """Extract a field value from text"""
        for option in options:
            if option.lower() in text.lower():
                return option
        return None

    def _extract_model_type(self, text: str) -> Optional[str]:
        """Extract character model type"""
        model_types = [
            'Tall Male', 'Tall Female',
            'Medium Male', 'Medium Female',
            'Short Male', 'Short Female'
        ]
        for model in model_types:
            if model.lower().replace(' ', '') in text.lower().replace(' ', ''):
                return model
        return None

    def _clean_section_name(self, name: str) -> str:
        """Clean section name"""
        name = re.sub(r'\[\]', '', name)
        name = re.sub(r'\[.*?\]', '', name)
        return name.strip()

    def _create_rag_text(self, info: Dict) -> str:
        """Create optimized text for RAG indexing"""
        parts = []

        # Character name as header
        parts.append(f"# {info['name']}")

        if info.get('title'):
            parts.append(f"Also known as: {info['title']}")

        if info.get('real_name') and info.get('real_name') != info['name']:
            parts.append(f"Real name: {info['real_name']}")

        parts.append("")

        # Basic information in a structured format
        parts.append("## Basic Information")

        fields = [
            ('Element', 'element'),
            ('Weapon', 'weapon'),
            ('Rarity', 'rarity'),
            ('Region', 'region'),
            ('Model', 'model_type'),
            ('Birthday', 'birthday'),
            ('Constellation', 'constellation'),
            ('Character Type', 'character_type'),
        ]

        for label, key in fields:
            value = info.get(key)
            if value:
                if key == 'rarity':
                    parts.append(f"- {label}: {value}-Star")
                else:
                    parts.append(f"- {label}: {value}")

        # Affiliations
        if info.get('affiliations'):
            parts.append(f"- Affiliations: {', '.join(info['affiliations'])}")

        parts.append("")

        # NEW: Role information
        if info.get('role_summary'):
            parts.append("## Character Roles")
            parts.append(f"- Role: {info['role_summary']}")
            parts.append("")

        # NEW:  Obtain methods
        if info.get('how_to_obtain'):
            parts.append("## How to Obtain")
            for method in info['how_to_obtain']:
                parts.append(f"- {method}")
            if info.get('event_wishes_count'):
                parts.append(f"- Featured in {info['event_wishes_count']} Event Wishes")
            parts.append("")

        # NEW: Release date
        if info.get('release_date'):
            parts.append(f"## Release Date")
            parts.append(f"Released on: {info['release_date']}")
            parts.append("")

        # NEW: Voice actors
        if info.get('voice_actors'):
            parts.append("## Voice Actors")
            for lang, actor in info['voice_actors'].items():
                parts.append(f"- {lang.capitalize()}: {actor}")
            parts.append("")

        # NEW: Special dish
        if info.get('special_dish'):
            parts.append(f"## Special Dish")
            parts.append(f"- {info['special_dish']}")
            parts.append("")

        # NEW: Namecard
        if info.get('namecard'):
            parts.append(f"## Namecard")
            parts.append(f"- {info['namecard']}")
            parts.append("")

        # Description
        if info.get('description'):
            parts.append("## About")
            parts.append(info['description'])
            parts.append("")

        # Include relevant sections
        skip_sections = ['Ascensions', 'Stats', 'Wishes', 'Bargains', 'Gallery', 'Trivia']

        for section_name, section_content in info.get('sections', {}).items():
            if not any(skip in section_name for skip in skip_sections):
                if section_content and len(section_content) > 30:
                    parts.append(f"## {section_name}")
                    parts.append(section_content)
                    parts.append("")

        return '\n'.join(parts)

    def process_all(self, input_file: str = "characters_latest.json") -> List[Dict]:
        """Process all characters"""
        input_path = os.path.join(self.input_dir, input_file)

        print(f"Loading raw data from: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        print(f"Processing {len(raw_data)} characters...")

        processed = []
        errors = []

        for char in raw_data:
            try:
                processed_char = self.process_character(char)
                processed.append(processed_char)
            except Exception as e:
                char_name = char.get('name', 'Unknown')
                errors.append((char_name, str(e)))
                print(f"Error processing {char_name}: {e}")

        print(f"Processed {len(processed)} characters successfully")
        if errors:
            print(f"Errors: {len(errors)}")

        return processed

    def create_smart_chunks(self, data: List[Dict], chunk_size: int = 800) -> List[Dict]:
        """Create smart chunks optimized for RAG retrieval"""
        chunks = []

        for char in data:
            name = char.get('name', 'Unknown')

            # Chunk 1: Basic info chunk (always created)
            basic_info = f"""# {name}

## Basic Information
- Element: {char.get('element', 'Unknown')}
- Weapon: {char.get('weapon', 'Unknown')}
- Rarity: {char.get('rarity', 4)}-Star
- Region: {char.get('region', 'Unknown')}
- Role: {char.get('role_summary', 'Unknown')}
"""
            if char.get('affiliations'):
                basic_info += f"- Affiliations: {', '.join(char['affiliations'])}\n"
            if char.get('birthday'):
                basic_info += f"- Birthday: {char['birthday']}\n"
            if char.get('release_date'):
                basic_info += f"- Release Date: {char['release_date']}\n"

            chunks.append({
                'id': f"{name.lower().replace(' ', '_')}_basic",
                'character': name,
                'chunk_type': 'basic_info',
                'content': basic_info.strip(),
                'metadata': {
                    'element': char.get('element'),
                    'weapon': char.get('weapon'),
                    'rarity': char.get('rarity'),
                    'region':  char.get('region'),
                    'role_summary': char.get('role_summary'),
                    'url': char.get('url')
                }
            })

            # Chunk 2: Description chunk
            if char.get('description') and len(char['description']) > 50:
                desc_chunk = f"""# {name} - Description

{char['description']}
"""
                chunks.append({
                    'id': f"{name.lower().replace(' ', '_')}_description",
                    'character': name,
                    'chunk_type': 'description',
                    'content': desc_chunk.strip(),
                    'metadata': {
                        'element': char.get('element'),
                        'weapon': char.get('weapon'),
                        'region': char.get('region'),
                        'url': char.get('url')
                    }
                })

            # Chunk 3: Voice actors and meta info
            if char.get('voice_actors') or char.get('special_dish'):
                meta_content = f"# {name} - Additional Info\n\n"

                if char.get('voice_actors'):
                    meta_content += "## Voice Actors\n"
                    for lang, actor in char['voice_actors'].items():
                        meta_content += f"- {lang.capitalize()}: {actor}\n"
                    meta_content += "\n"

                if char.get('special_dish'):
                    meta_content += f"## Special Dish\n- {char['special_dish']}\n\n"

                if char.get('namecard'):
                    meta_content += f"## Namecard\n- {char['namecard']}\n\n"

                if char.get('how_to_obtain'):
                    meta_content += "## How to Obtain\n"
                    for method in char['how_to_obtain']:
                        meta_content += f"- {method}\n"

                chunks.append({
                    'id': f"{name.lower().replace(' ', '_')}_meta",
                    'character': name,
                    'chunk_type': 'meta_info',
                    'content':  meta_content.strip(),
                    'metadata': {
                        'element': char.get('element'),
                        'url': char.get('url')
                    }
                })

            # Additional chunks from sections
            for section_name, section_content in char.get('sections', {}).items():
                if section_content and len(section_content) > 50:
                    section_chunk = f"""# {name} - {section_name}

{section_content}
"""
                    chunks.append({
                        'id': f"{name.lower().replace(' ', '_')}_{section_name.lower().replace(' ', '_')}",
                        'character':  name,
                        'chunk_type': 'section',
                        'section_name': section_name,
                        'content': section_chunk.strip(),
                        'metadata': {
                            'element':  char.get('element'),
                            'weapon': char.get('weapon'),
                            'region': char.get('region'),
                            'url': char.get('url')
                        }
                    })

        print(f"Created {len(chunks)} smart chunks from {len(data)} characters")

        return chunks

    def save_data(self, data: List[Dict], filename: str):
        """Save data to JSON file"""
        output_path = os.path.join(self.output_dir, filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Saved to: {output_path}")

        return output_path

    def generate_stats(self, data: List[Dict]) -> Dict:
        """Generate statistics about the processed data"""
        stats = {
            'total_characters': len(data),
            'by_element': {},
            'by_weapon': {},
            'by_region': {},
            'by_rarity': {},
            'by_role': {},
            'by_character_type': {},
            'missing_fields': {
                'element': 0,
                'weapon': 0,
                'region': 0,
                'description': 0,
                'voice_actors': 0,
            }
        }

        for char in data:
            # Count by element
            element = char.get('element', 'Unknown')
            stats['by_element'][element] = stats['by_element'].get(element, 0) + 1

            # Count by weapon
            weapon = char.get('weapon', 'Unknown')
            stats['by_weapon'][weapon] = stats['by_weapon'].get(weapon, 0) + 1

            # Count by region
            region = char.get('region', 'Unknown')
            stats['by_region'][region] = stats['by_region'].get(region, 0) + 1

            # Count by rarity
            rarity = char.get('rarity', 'Unknown')
            stats['by_rarity'][rarity] = stats['by_rarity'].get(rarity, 0) + 1

            # Count by role
            role = char.get('role_summary', 'Unknown')
            stats['by_role'][role] = stats['by_role'].get(role, 0) + 1

            # Count by character type
            char_type = char.get('character_type', 'Unknown')
            stats['by_character_type'][char_type] = stats['by_character_type'].get(char_type, 0) + 1

            # Count missing fields
            if not char.get('element'):
                stats['missing_fields']['element'] += 1
            if not char.get('weapon'):
                stats['missing_fields']['weapon'] += 1
            if not char.get('region'):
                stats['missing_fields']['region'] += 1
            if not char.get('description') or len(char.get('description', '')) < 50:
                stats['missing_fields']['description'] += 1
            if not char.get('voice_actors'):
                stats['missing_fields']['voice_actors'] += 1

        return stats


def main():
    """Main function to run enhanced processing"""
    print("=" * 60)
    print("ENHANCED GENSHIN DATA PROCESSOR v2.1")
    print("=" * 60)

    processor = EnhancedGenshinProcessor()

    # Process all characters
    processed_data = processor.process_all("characters_latest.json")

    # Save processed data
    processor.save_data(processed_data, "characters_processed_v3.json")

    # Create smart chunks
    chunks = processor.create_smart_chunks(processed_data)
    processor.save_data(chunks, "characters_chunks_v3.json")

    # Generate and display stats
    stats = processor.generate_stats(processed_data)

    print("\n" + "=" * 60)
    print("DATA STATISTICS")
    print("=" * 60)
    print(f"\nTotal Characters: {stats['total_characters']}")

    print("\nBy Element:")
    for element, count in sorted(stats['by_element'].items(), key=lambda x: -x[1]):
        print(f"  {element}: {count}")

    print("\nBy Rarity:")
    for rarity, count in sorted(stats['by_rarity'].items(), key=lambda x: -x[1]):
        print(f"  {rarity}-Star: {count}")

    print("\nBy Role:")
    for role, count in sorted(stats['by_role'].items(), key=lambda x: -x[1])[: 10]:
        print(f"  {role}: {count}")

    print("\nBy Character Type:")
    for char_type, count in sorted(stats['by_character_type'].items(), key=lambda x: -x[1]):
        print(f"  {char_type}: {count}")

    print("\nMissing Fields:")
    for field, count in stats['missing_fields'].items():
        print(f"  {field}: {count}")

    # Show sample
    print("\n" + "=" * 60)
    print("SAMPLE CLEANED DATA")
    print("=" * 60)

    if processed_data:
        # Find a good sample (with description and voice actors)
        sample = next((c for c in processed_data
                      if len(c.get('description', '')) > 100 and c.get('voice_actors')),
                     processed_data[0])

        print(f"\nCharacter: {sample['name']}")
        print(f"Element: {sample.get('element', 'N/A')}")
        print(f"Weapon: {sample.get('weapon', 'N/A')}")
        print(f"Rarity: {sample.get('rarity', 'N/A')}-Star")
        print(f"Region: {sample.get('region', 'N/A')}")
        print(f"Role: {sample.get('role_summary', 'N/A')}")
        print(f"Character Type: {sample.get('character_type', 'N/A')}")
        print(f"Release Date: {sample.get('release_date', 'N/A')}")
        print(f"How to Obtain: {', '.join(sample.get('how_to_obtain', ['N/A']))}")
        print(f"Event Wishes: {sample.get('event_wishes_count', 'N/A')}")
        print(f"Special Dish: {sample.get('special_dish', 'N/A')}")
        print(f"Voice Actors: {sample.get('voice_actors', {})}")
        print(f"\nDescription:")
        print(sample.get('description', 'N/A')[:500])


if __name__ == "__main__":
    main()