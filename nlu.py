import spacy
import json
import re
from typing import Dict, List, Tuple
import os
from thefuzz import fuzz, process

print(f"[BOOT] Initializing NLU module... (PID: {os.getpid()})")

class NLU:
    def __init__(self):
        print(f"[BOOT] NLU __init__ called. Loading spaCy model...")
        try:
            self.nlp = spacy.load("xx_ent_wiki_sm")
            print(f"[BOOT] spaCy model loaded successfully!")
        except Exception as e:
            print(f"[BOOT] FATAL ERROR loading spaCy: {e}")
            self.nlp = None
        
        print(f"[BOOT] Loading intents...")
        self.intents = self._load_intents()
        print(f"[BOOT] NLU Initialization complete.")
    
    def _load_intents(self) -> Dict:
        try:
            with open('nlp_data/intents.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_intents()
    
    def _get_default_intents(self) -> Dict:
        return {"intents": []}
    
    def classify_intent(self, text: str) -> str:
        """
        Classify user intent with priority for ordering-related intents.
        Uses longest pattern match strategy with priority weighting.
        """
        text_lower = text.lower().strip()
        normalized_text = re.sub(r'[^a-z0-9\s]', ' ', text_lower)
        normalized_text = re.sub(r'\s+', ' ', normalized_text).strip()

        if not normalized_text or len(normalized_text) <= 1:
            return "unknown"
        
        # Priority order: ordering > specific queries > generic responses
        priority_tags = ['pesan_menu', 'cek_ketersediaan', 'cek_status', 'ubah_pesanan', 
                         'batalkan_pesanan', 'konfirmasi_pembayaran', 'info_pembayaran',
                         'rekomendasi_menu', 'info_promo', 'info_jam', 'lokasi', 'komplain',
                         'salam', 'terima_kasih', 'konfirmasi', 'pembatalan']
        
        best_match = "unknown"
        best_score = 0
        best_priority = 999
        
        for intent in self.intents["intents"]:
            tag = intent["tag"]
            tag_priority = priority_tags.index(tag) if tag in priority_tags else 50
            
            if not intent["patterns"]:
                continue
                
            # Gunakan token_set_ratio agar frase urutan kebalik atau typo tetap terdeteksi
            match = process.extractOne(text_lower, intent["patterns"], scorer=fuzz.token_set_ratio)
            if match:
                score = match[1]
                if score > best_score or (score == best_score and tag_priority < best_priority):
                    best_match = tag
                    best_score = score
                    best_priority = tag_priority
        
        # Ambang batas skor minimal untuk menghindari salah maksud (false positive)
        if best_score < 70:
            return "unknown"
            
        return best_match
    
    def __init__(self):
        print(f"[BOOT] NLU __init__ called. Loading spaCy model...")
        try:
            self.nlp = spacy.load("xx_ent_wiki_sm")
            print(f"[BOOT] spaCy model loaded successfully!")
        except Exception as e:
            print(f"[BOOT] FATAL ERROR loading spaCy: {e}")
            self.nlp = None
        
        print(f"[BOOT] Loading intents...")
        self.intents = self._load_intents()
        
        # Setup time extraction patterns
        self._setup_time_patterns()
        
        print(f"[BOOT] NLU Initialization complete.")
    
    def _setup_time_patterns(self):
        """Setup regex patterns for time extraction"""
        # Time keywords in Indonesian and regional (Bugis/Tae')
        self.time_keywords = {
            "sekarang": "immediate",
            "segera": "immediate",
            "langsung": "immediate",
            "nanti": "later",
            "besok": "tomorrow",
            "baja": "tomorrow",
            "pagi": "09:00",
            "elepun": "09:00",
            "siang": "12:00",
            "sore": "15:00",
            "malam": "19:00",
            "wenni": "19:00",
            "ma'benni": "19:00",
            "esso": "12:00"
        }
        
        # Regex patterns for time extraction
        self.time_patterns = [
            # Format: jam 12.30, jam 12:30, jam 12 30
            r'\bjam\s*(\d{1,2})[:\.\s]?(\d{2})?\s*(pagi|siang|sore|malam)?\b',
            # Format: pukul 12.30, pukul 12:30
            r'\bpukul\s*(\d{1,2})[:\.\s]?(\d{2})?\s*(pagi|siang|sore|malam)?\b',
            # Format: 12.30, 12:30 (with am/pm context)
            r'\b(\d{1,2})[:\.](\d{2})\s*(pagi|siang|sore|malam|am|pm)?\b',
            # Format: 30 menit lagi, 1 jam lagi
            r'\b(\d+)\s*(menit|jam)\s*lagi\b',
            # Format: setengah (12:30)
            r'\bsetengah\s*(\d{1,2})\s*(pagi|siang|sore|malam)?\b'
        ]

        self.menu_aliases = [
            ("ayam geprek", ["ayam geprek", "ayam gprek", "aym geprek", "geprek", "geprek ayam", "ayam gepreknya", "ayam geprekta", "gepreknya"]),
            ("ayam bakar", ["ayam bakar", "aym bakar", "ayam bkr", "aym bkr"]),
            ("ayam goreng", ["ayam goreng", "aym goreng"]),
            ("ayam crispy", ["ayam crispy", "ayam krispi", "ayam krispy", "krispi", "krispy"]),
            ("ayam penyet", ["ayam penyet", "penyet"]),
            ("nasi", ["nasi putih", "nasi"]),
            ("es teh manis", ["es teh manis", "es teh", "es te", "s teh", "este", "esteh", "teh es"]),
            ("es jeruk", ["es jeruk", "s jeruk", "es jruk"]),
            ("es campur", ["es campur", "s campur"]),
            ("es teler", ["es teler", "s teler"]),
            ("es kelapa", ["es kelapa", "s kelapa", "es klapa"]),
            ("tahu crispy", ["tahu crispy", "tahu krispi", "tahu goreng", "tahu"]),
            ("tempe crispy", ["tempe crispy", "tempe krispi", "tempe goreng", "tempe"]),
            ("sate ayam", ["sate ayam", "sate"])
        ]

        self.sambal_aliases = {
            "sambal bawang": ["sambal bawang", "sambel bawang", "bawang"],
            "sambal ijo": ["sambal ijo", "sambel ijo", "sambal hijau", "sambel hijau", "ijo", "hijau"],
            "sambal merah": ["sambal merah", "sambel merah", "merah"],
            "sambal terasi": ["sambal terasi", "sambel terasi", "terasi"],
            "sambal matah": ["sambal matah", "sambel matah", "matah"],
            "tanpa sambal": [
                "tanpa sambal",
                "tanpa sambel",
                "tanpa",
                "tidak pakai sambal",
                "tidak pakai sambel",
                "ga pakai sambal",
                "ga pakai sambel",
                "gak pakai sambal",
                "gak pakai sambel",
                "nggak pakai sambal",
                "nggak pakai sambel",
                "no sambal"
            ]
        }

    def _normalize_text(self, text: str) -> str:
        normalized = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
        return re.sub(r'\s+', ' ', normalized).strip()

    def _contains_phrase(self, text: str, phrase: str) -> bool:
        pattern = r'(?<!\w)' + re.escape(phrase).replace(r'\ ', r'\s+') + r'(?!\w)'
        return re.search(pattern, text) is not None

    def _extract_menu_from_part(self, part: str) -> str | None:
        normalized_part = self._normalize_text(part)
        if not normalized_part:
            return None

        for canonical_menu, aliases in self.menu_aliases:
            for alias in sorted(aliases, key=len, reverse=True):
                if self._contains_phrase(normalized_part, alias):
                    return canonical_menu

        return None

    def _extract_sambal_from_part(self, part: str) -> str | None:
        normalized_part = self._normalize_text(part)
        if not normalized_part or normalized_part == "sambal":
            return None

        for canonical_sambal, aliases in self.sambal_aliases.items():
            for alias in sorted(aliases, key=len, reverse=True):
                if self._contains_phrase(normalized_part, alias):
                    return canonical_sambal

        return None
    
    def extract_time(self, text: str) -> Dict:
        """
        Extract pickup time from text
        Returns: Dict with 'type', 'value', 'formatted', 'original'
        """
        text_lower = text.lower()

        # Try regex patterns
        for pattern in self.time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                
                # Pattern: jam/pukul HH:MM or HH:MM with am/pm
                if len(groups) >= 2 and groups[0] and groups[1]:
                    hour = int(groups[0])
                    minute = groups[1]
                    period = groups[2] if len(groups) > 2 and groups[2] else None
                    
                    # Handle am/pm conversion
                    if period:
                        if period in ['siang', 'sore'] and hour < 12:
                            hour += 12
                        elif period == 'malam' and hour < 12 and hour != 12:
                            hour += 12
                        elif period == 'pagi' and hour == 12:
                            hour = 0
                    
                    formatted_time = f"{hour:02d}:{minute}"
                    return {
                        "type": "specific",
                        "value": formatted_time,
                        "formatted": formatted_time,
                        "original": match.group(0)
                    }
                
                # Pattern: jam/pukul HH (without minutes)
                elif len(groups) >= 1 and groups[0]:
                    hour = int(groups[0])
                    period = groups[2] if len(groups) > 2 and groups[2] else None
                    
                    if period:
                        if period in ['siang', 'sore'] and hour < 12:
                            hour += 12
                        elif period == 'malam' and hour < 12 and hour != 12:
                            hour += 12
                        elif period == 'pagi' and hour == 12:
                            hour = 0
                    
                    formatted_time = f"{hour:02d}:00"
                    return {
                        "type": "specific",
                        "value": formatted_time,
                        "formatted": formatted_time,
                        "original": match.group(0)
                    }
                
                # Pattern: X menit/jam lagi
                elif len(groups) >= 2 and groups[1] in ['menit', 'jam']:
                    amount = int(groups[0])
                    unit = groups[1]
                    return {
                        "type": "relative",
                        "value": f"{amount}_{unit}",
                        "formatted": f"{amount} {unit} lagi",
                        "original": match.group(0)
                    }
                
                # Pattern: setengah X
                elif 'setengah' in match.group(0):
                    hour = int(groups[0]) if groups[0] else 12
                    period = groups[1] if len(groups) > 1 and groups[1] else None
                    
                    if period:
                        if period in ['siang', 'sore'] and hour < 12:
                            hour += 12
                    
                    formatted_time = f"{hour-1:02d}:30"
                    return {
                        "type": "specific",
                        "value": formatted_time,
                        "formatted": formatted_time,
                        "original": match.group(0)
                    }

        # Keyword fallback only after specific regex parsing fails.
        normalized_text = self._normalize_text(text)
        for keyword, time_type in self.time_keywords.items():
            normalized_keyword = self._normalize_text(keyword)
            if not normalized_keyword:
                continue

            pattern = r'(?<!\w)' + re.escape(normalized_keyword).replace(r'\ ', r'\s+') + r'(?!\w)'
            if not re.search(pattern, normalized_text):
                continue

            if time_type == "immediate":
                return {
                    "type": "immediate",
                    "value": "immediate",
                    "formatted": "Sekarang",
                    "original": keyword
                }
            elif time_type in ["tomorrow", "later"]:
                return {
                    "type": time_type,
                    "value": time_type,
                    "formatted": "Nanti",
                    "original": keyword
                }
            else:
                return {
                    "type": "specific",
                    "value": time_type,
                    "formatted": time_type,
                    "original": keyword
                }

        return None
    
    def extract_entities(self, text: str) -> Dict:
        entities = {
            "NAMA_MENU": None,
            "JUMLAH": None,
            "JENIS_SAMBAL": None,
            "WAKTU_PENGAMBILAN": None,
            "ITEMS": []
        }
        
        text_lower = text.lower()
        
        # Extract time first
        time_entity = self.extract_time(text)
        if time_entity:
            entities["WAKTU_PENGAMBILAN"] = time_entity
        
        # Pisahkan berdasarkan kata hubung
        separators = r'\bdan\b|\bsama\b|\bdengan\b|\bterus\b|\bkasih\b|,|&|\+'
        parts = re.split(separators, text_lower)
        
        # Menu keywords - more comprehensive
        menu_keywords = [
            "ayam geprek", "ayam bakar", "ayam goreng", "ayam crispy", "ayam penyet",
            "nasi",
            "es teh manis", "es teh", "es jeruk", "es campur", "es teler", "es kelapa",
            "tahu crispy", "tahu goreng", "tahu",
            "tempe crispy", "tempe goreng", "tempe",
            "sate ayam", "sate",
            "ayam gprek", "ayam bkr", "geprek", "ayam krispi", "ayam krispy",
            "ayam gepreknya", "ayam geprekta", "gepreknya", "este", "esteh", "s teh", "es te"
        ]
                          
        # Number extraction - ordinal words
        angka_ordinal = {
            "satu": "1", "dua": "2", "tiga": "3", "empat": "4", "lima": "5",
            "enam": "6", "tujuh": "7", "delapan": "8", "sembilan": "9", "sepuluh": "10",
            "seporsi": "1", "se porsi": "1", "sebungkus": "1", "segelas": "1"
        }
        
        for part in parts:
            part = part.strip()
            if not part: continue
            
            item_entity = {
                "NAMA_MENU": None,
                "JUMLAH": None,
                "JENIS_SAMBAL": None
            }

            item_entity["NAMA_MENU"] = self._extract_menu_from_part(part)
            item_entity["JENIS_SAMBAL"] = self._extract_sambal_from_part(part)
            
            # Use fuzzy matching for menu items, but strictly validate short matches
            if not item_entity["NAMA_MENU"]:
                best_menu_match = process.extractOne(part, menu_keywords, scorer=fuzz.token_set_ratio)
                
                # Jika part terlalu pendek atau sekadar "ayam", token_set_ratio bisa memberikan false positive tinggi
                # Contoh: "pesan ayam" -> "ayam penyet" = 100
                # Oleh karena itu, kita verifikasi menggunakan token_sort_ratio atau substring
                
                is_valid_menu = False
                if best_menu_match and best_menu_match[1] >= 75:
                    matched_menu = best_menu_match[0]
                    
                    # Filter strict untuk mencegah false positive
                    # Misalnya "ayam" saja di input, cocok 100 ngawur ke "ayam geprek"
                    matched_words = matched_menu.split()
                    token_sort_score = fuzz.token_sort_ratio(part, matched_menu)
                    
                    # If exact word is in string, or token sort is high enough
                    if any(mw in part for mw in matched_words) and (token_sort_score >= 60 or best_menu_match[1] >= 90):
                         # Prevent simple "ayam" from becoming specific "ayam geprek" unless "geprek" is present
                         if "ayam" in matched_menu and matched_menu != "ayam" and "ayam" in part and not any(w in part for w in matched_menu.split() if w != "ayam"):
                             pass # It's just generic 'ayam', not 'ayam geprek'
                         elif "es" in matched_menu and matched_menu != "es" and "es" in part and not any(w in part for w in matched_menu.split() if w != "es"):
                             pass
                         else:
                            is_valid_menu = True
                            
                    if is_valid_menu:
                        item_entity["NAMA_MENU"] = matched_menu
            
            for word, value in angka_ordinal.items():
                if word in part:
                    item_entity["JUMLAH"] = value
                    break
            
            if not item_entity["JUMLAH"]:
                numbers = re.findall(r'\d+', part)
                if numbers:
                    item_entity["JUMLAH"] = numbers[0]
                    
            if item_entity["NAMA_MENU"]:
                entities["ITEMS"].append(item_entity)
                
        # For backward compatibility
        if entities["ITEMS"]:
            entities["NAMA_MENU"] = entities["ITEMS"][0]["NAMA_MENU"]
            entities["JUMLAH"] = entities["ITEMS"][0]["JUMLAH"]
            entities["JENIS_SAMBAL"] = entities["ITEMS"][0]["JENIS_SAMBAL"]
            
        return entities
    
    def process(self, text: str) -> Tuple[str, Dict[str, str]]:
        intent = self.classify_intent(text)
        entities = self.extract_entities(text)
        
        # Smart override: if menu entity is detected, likely ordering intent
        # Jangan override salam/terima_kasih agar sapaan tetap dijawab sapaan
        if entities["NAMA_MENU"] and intent in ["unknown", "konfirmasi"]:
            intent = "pesan_menu"
        
        return intent, entities

nlu = NLU()
