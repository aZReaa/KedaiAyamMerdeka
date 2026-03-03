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
    
    def extract_entities(self, text: str) -> Dict:
        entities = {
            "NAMA_MENU": None,
            "JUMLAH": None,
            "JENIS_SAMBAL": None,
            "ITEMS": []
        }
        
        text_lower = text.lower()
        
        # Pisahkan berdasarkan kata hubung
        separators = r'\bdan\b|\bsama\b|\bdengan\b|\bterus\b|\bkasih\b|,|&|\+'
        parts = re.split(separators, text_lower)
        
        # Menu keywords - more comprehensive
        menu_keywords = [
            "ayam geprek", "ayam bakar", "ayam goreng", "ayam crispy", "ayam penyet",
            "nasi putih", "nasi", 
            "es teh manis", "es teh", "es jeruk", "es campur", "es teler", "es kelapa",
            "tahu crispy", "tahu goreng", "tahu",
            "tempe crispy", "tempe goreng", "tempe",
            "sate ayam", "sate"
        ]
        
        # Sambal keywords
        sambal_keywords = ["sambal ijo", "sambal hijau", "sambal bawang", "sambal terasi", 
                          "sambal kecap", "sambal matah", "tanpa sambal", "tidak pakai sambal"]
                          
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
            
            # Use fuzzy matching for menu items, but strictly validate short matches
            best_menu_match = process.extractOne(part, menu_keywords, scorer=fuzz.token_set_ratio)
            
            # Jika part terlalu pendek atau sekadar "ayam", token_set_ratio bisa memberikan false positive tinggi
            # Contoh: "pesan ayam" -> "ayam penyet" = 100
            # Oleh karena itu, kita verifikasi menggunakan token_sort_ratio atau substring
            
            is_valid_menu = False
            if best_menu_match and best_menu_match[1] >= 75:
                matched_menu = best_menu_match[0]
                
                # Filter strict untuk mencegah false positive
                # Misalnya "ayam" saja di input, cocok 100 ngawur ke "ayam geprek"
                # Kita cek berapa persen kata dari matched_menu ada di input part
                matched_words = matched_menu.split()
                part_words = part.split()
                
                # Check if at least the main defining word is present (e.g., 'geprek' in 'ayam geprek')
                direct_match_score = fuzz.ratio(part, matched_menu)
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
                
            best_sambal_match = process.extractOne(part, sambal_keywords, scorer=fuzz.token_set_ratio)
            if best_sambal_match and best_sambal_match[1] >= 80:
                item_entity["JENIS_SAMBAL"] = best_sambal_match[0].replace("sambal hijau", "sambal ijo")
            
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
