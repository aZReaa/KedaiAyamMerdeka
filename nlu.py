import spacy
import json
import re
from typing import Dict, List, Tuple

class NLU:
    def __init__(self):
        try:
            self.nlp = spacy.load("xx_ent_wiki_sm")
        except OSError:
            print("Model spaCy belum diinstall. Install dengan: python -m spacy download xx_ent_wiki_sm")
            self.nlp = None
        
        self.intents = self._load_intents()
    
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
            
            for pattern in intent["patterns"]:
                pattern_lower = pattern.lower()
                
                # Exact match gets highest score
                if text_lower == pattern_lower:
                    score = len(pattern) * 3
                # Pattern contained in text
                elif pattern_lower in text_lower:
                    score = len(pattern) * 2
                # Text contained in pattern (partial)
                elif text_lower in pattern_lower:
                    score = len(text_lower)
                else:
                    continue
                
                # Compare: prefer higher score, then higher priority (lower index)
                if score > best_score or (score == best_score and tag_priority < best_priority):
                    best_match = tag
                    best_score = score
                    best_priority = tag_priority
        
        return best_match
    
    def extract_entities(self, text: str) -> Dict[str, str]:
        entities = {
            "NAMA_MENU": None,
            "JUMLAH": None,
            "JENIS_SAMBAL": None
        }
        
        text_lower = text.lower()
        
        # Menu keywords - more comprehensive
        menu_keywords = [
            "ayam geprek", "ayam bakar", "ayam goreng", "ayam crispy", "ayam penyet",
            "nasi putih", "nasi", 
            "es teh manis", "es teh", "es jeruk", "es campur", "es teler", "es kelapa",
            "tahu crispy", "tahu goreng", "tahu",
            "tempe crispy", "tempe goreng", "tempe",
            "sate ayam", "sate"
        ]
        
        # Sort by length descending to match longer patterns first
        menu_keywords.sort(key=len, reverse=True)
        
        for menu in menu_keywords:
            if menu in text_lower:
                entities["NAMA_MENU"] = menu
                break
        
        # Sambal keywords
        sambal_keywords = ["sambal ijo", "sambal hijau", "sambal bawang", "sambal terasi", 
                          "sambal kecap", "sambal matah", "tanpa sambal", "tidak pakai sambal"]
        for sambal in sambal_keywords:
            if sambal in text_lower:
                entities["JENIS_SAMBAL"] = sambal.replace("sambal hijau", "sambal ijo")
                break
        
        # Number extraction - ordinal words
        angka_ordinal = {
            "satu": "1", "dua": "2", "tiga": "3", "empat": "4", "lima": "5",
            "enam": "6", "tujuh": "7", "delapan": "8", "sembilan": "9", "sepuluh": "10",
            "seporsi": "1", "se porsi": "1", "sebuah": "1"
        }
        
        for word, value in angka_ordinal.items():
            if word in text_lower:
                entities["JUMLAH"] = value
                break
        
        # Numeric extraction (override ordinal if explicit number found)
        numbers = re.findall(r'\d+', text)
        if numbers:
            entities["JUMLAH"] = numbers[0]
        
        return entities
    
    def process(self, text: str) -> Tuple[str, Dict[str, str]]:
        intent = self.classify_intent(text)
        entities = self.extract_entities(text)
        
        # Smart override: if menu entity is detected, likely ordering intent
        if entities["NAMA_MENU"] and intent in ["unknown", "konfirmasi", "salam"]:
            intent = "pesan_menu"
        
        return intent, entities

nlu = NLU()
