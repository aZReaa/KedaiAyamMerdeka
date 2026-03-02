from config import Config
from database import db
from nlu import nlu
import random
from datetime import datetime

class DialogManager:
    def __init__(self):
        self.user_states = {}
        
        # Menu yang perlu tanya sambal
        self.MENU_NEED_SAMBAL = ['ayam geprek', 'ayam bakar', 'ayam goreng', 'ayam penyet', 'ayam crispy']
        
        # Pilihan sambal
        self.SAMBAL_OPTIONS = ['sambal bawang', 'sambal ijo', 'sambal terasi', 'sambal matah', 'tanpa sambal']
    
    def get_user_state(self, user_id: str) -> dict:
        if user_id not in self.user_states:
            self.user_states[user_id] = {
                'state': 'idle',
                'data': {},
                'cart': []
            }
        return self.user_states[user_id]
    
    def update_user_state(self, user_id: str, state: str, data: dict = None):
        if user_id not in self.user_states:
            self.user_states[user_id] = {'state': state, 'data': {}, 'cart': []}
        self.user_states[user_id]['state'] = state
        if data:
            self.user_states[user_id]['data'].update(data)
    
    def reset_user_state(self, user_id: str):
        self.user_states[user_id] = {
            'state': 'idle',
            'data': {},
            'cart': []
        }
    
    def generate_response(self, user_id: str, message: str) -> str:
        """Main response generator with improved flow handling."""
        try:
            state = self.get_user_state(user_id)
            intent, entities = nlu.process(message)
            
            print(f"[DEBUG] User: {user_id} | State: {state['state']} | Intent: {intent} | Entities: {entities}")
            
            if state['state'] == 'idle':
                return self._handle_idle_state(user_id, intent, entities, message)
            elif state['state'] == 'asking_menu':
                return self._handle_asking_menu_state(user_id, state, intent, entities, message)
            elif state['state'] == 'asking_quantity':
                return self._handle_asking_quantity_state(user_id, state, intent, entities, message)
            elif state['state'] == 'asking_sambal':
                return self._handle_asking_sambal_state(user_id, state, intent, entities, message)
            elif state['state'] == 'confirming':
                return self._handle_confirming_state(user_id, state, intent, entities, message)
            elif state['state'] == 'awaiting_payment':
                return self._handle_awaiting_payment_state(user_id, state, intent, entities, message)
            elif state['state'] == 'modifying':
                return self._handle_modifying_state(user_id, state, intent, entities, message)
            
            return "Maaf, saya tidak mengerti. Ketik 'menu' untuk melihat daftar menu ya kak!"
        except Exception as e:
            print(f"[ERROR] generate_response: {e}")
            return "Maaf kak, ada sedikit gangguan. Coba ulangi pesanan kakak ya!"
    
    def _handle_idle_state(self, user_id: str, intent: str, entities: dict, message: str) -> str:
        """Handle user input when in idle state."""
        
        # If menu entity detected, start ordering flow
        if entities.get('NAMA_MENU'):
            return self._start_ordering_flow(user_id, entities)
        
        if intent == 'salam':
            greeting = self._get_time_greeting()
            menu_list = self._format_menu_list()
            return f"{greeting}\n\n{menu_list}\n\n⏰ Jam Operasional: {Config.JAM_BUKA} - {Config.JAM_TUTUP}"
        
        elif intent == 'terima_kasih':
            return self._get_response(intent)
        
        elif intent == 'pesan_menu':
            menu_list = self._format_menu_list()
            self.update_user_state(user_id, 'asking_menu', {})
            return f"Siap kak! Mau pesan apa?\n\n{menu_list}\n\n💡 *Contoh:* Ayam Geprek, Es Teh Manis"
        
        elif intent == 'cek_ketersediaan':
            if entities.get('NAMA_MENU'):
                menu = db.get_menu_by_name(entities['NAMA_MENU'])
                if menu:
                    return f"✅ *{menu['nama_menu']}* tersedia kak!\nHarga: Rp {menu['harga']:,}\n\nMau pesan? Ketik 'pesan {menu['nama_menu']}'"
                else:
                    return "Maaf kak, menu tersebut tidak tersedia 😔"
            else:
                return "Menu apa yang mau dicek kak?"
        
        elif intent == 'cek_status':
            pesanan = db.get_last_pesanan(user_id)
            if pesanan:
                status_emoji = {'dipesan': '🕐', 'diproses': '👨‍🍳', 'selesai': '✅', 'batal': '❌'}
                emoji = status_emoji.get(pesanan['status'], '📋')
                return f"{emoji} *Status Pesanan #{pesanan['id_pesanan']}*\n\nDetail: {pesanan['detail_pesanan']}\nTotal: Rp {pesanan['total_harga']:,}\nStatus: *{pesanan['status'].upper()}*"
            else:
                return "Kakak belum memiliki pesanan aktif. Mau pesan sekarang? Ketik 'pesan'"
        
        elif intent == 'info_promo':
            return self._get_response(intent) if self._get_response(intent) != "Maaf, saya tidak mengerti." else "🎉 Promo: Beli 2 Ayam Geprek GRATIS Es Teh Manis!"
        
        elif intent == 'info_jam':
            return f"⏰ *Jam Operasional Kedai Ayam Merdeka*\n\nSetiap Hari: {Config.JAM_BUKA} - {Config.JAM_TUTUP}"
        
        elif intent == 'info_pembayaran':
            return self._get_payment_info()
        
        elif intent == 'rekomendasi_menu':
            menus = db.get_all_menu()
            if menus:
                menu = random.choice(menus)
                return f"🌟 *Rekomendasi Hari Ini:*\n\n*{menu['nama_menu']}*\nHarga: Rp {menu['harga']:,}\n\nMau pesan kak? Ketik 'pesan {menu['nama_menu']}'"
            return "Menu belum tersedia saat ini."
        
        elif intent == 'ubah_pesanan':
            pesanan = db.get_last_pesanan(user_id)
            if pesanan and pesanan['status'] == 'dipesan':
                self.update_user_state(user_id, 'modifying', {'id_pesanan': pesanan['id_pesanan']})
                return f"Pesanan #{pesanan['id_pesanan']} akan diubah.\nDetail: {pesanan['detail_pesanan']}\n\nMau ganti jadi apa kak?"
            elif pesanan:
                return "Maaf kak, pesanan sudah diproses 🙏"
            return "Kakak belum punya pesanan aktif."
        
        elif intent == 'batalkan_pesanan' or intent == 'pembatalan':
            pesanan = db.get_last_pesanan(user_id)
            if pesanan and pesanan['status'] == 'dipesan':
                db.update_status_pesanan(pesanan['id_pesanan'], 'batal')
                self.reset_user_state(user_id)
                return f"❌ Pesanan #{pesanan['id_pesanan']} dibatalkan.\n\nMau pesan lagi? Ketik 'menu'"
            elif pesanan:
                return "Maaf kak, pesanan sudah diproses 🙏"
            return "Kakak belum punya pesanan aktif."
        
        elif intent == 'konfirmasi_pembayaran':
            pesanan = db.get_last_pesanan(user_id)
            if pesanan and pesanan['status'] == 'dipesan':
                db.update_status_pesanan(pesanan['id_pesanan'], 'diproses')
                return f"✅ *Pembayaran Dikonfirmasi!*\n\nPesanan #{pesanan['id_pesanan']} sedang diproses.\nEstimasi 15-30 menit.\n\nTerima kasih! 🍗"
            return "Kakak belum punya pesanan yang menunggu pembayaran."
        
        elif intent == 'tanya_harga':
            return f"Berikut daftar harga:\n\n{self._format_menu_list()}"
        
        elif intent == 'delivery':
            return "🛵 *Layanan Delivery*\n\nRadius: 5km\nOngkir: Rp 5.000 - Rp 15.000\n\nMau pesan delivery? Ketik 'pesan'"
        
        elif intent in ['lokasi', 'komplain', 'menu_pedas', 'chitchat_baik']:
            response = self._get_response(intent)
            if response != "Maaf, saya tidak mengerti.":
                return response
        
        # Fallback
        menu_list = self._format_menu_list()
        return f"Halo kak! Ada yang bisa dibantu?\n\n{menu_list}\n\n💡 Ketik 'pesan' untuk mulai memesan!"
    
    def _start_ordering_flow(self, user_id: str, entities: dict) -> str:
        """Start the ordering flow with detected menu."""
        menu_name = entities.get('NAMA_MENU')
        jumlah = entities.get('JUMLAH')
        sambal = entities.get('JENIS_SAMBAL')
        
        menu = db.get_menu_by_name(menu_name)
        if not menu:
            return f"Maaf kak, *{menu_name}* tidak tersedia 😔\n\n{self._format_menu_list()}"
        
        state_data = {
            'NAMA_MENU': menu_name,
            'menu_detail': menu,
            'JUMLAH': jumlah,
            'JENIS_SAMBAL': sambal
        }
        
        # Check what info we still need
        if not jumlah:
            self.update_user_state(user_id, 'asking_quantity', state_data)
            return f"Oke, *{menu['nama_menu']}* ya kak! 👍\n\nMau pesan berapa porsi?"
        
        # Check if this menu needs sambal preference
        needs_sambal = any(m in menu_name.lower() for m in self.MENU_NEED_SAMBAL)
        if needs_sambal and not sambal:
            self.update_user_state(user_id, 'asking_sambal', state_data)
            return self._ask_sambal_preference(menu['nama_menu'], jumlah)
        
        # All info complete, go to confirmation
        return self._go_to_confirmation(user_id, state_data)
    
    def _handle_asking_menu_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        """Handle when bot is asking for menu choice."""
        if intent == 'pembatalan' or intent == 'batalkan_pesanan':
            self.reset_user_state(user_id)
            return "Oke kak, batal dulu ya. Kalau mau pesan lagi tinggal ketik 'pesan' 😊"
        
        if entities.get('NAMA_MENU'):
            return self._start_ordering_flow(user_id, entities)
        
        # User might type just the menu name
        menu = db.get_menu_by_name(message.strip())
        if menu:
            entities['NAMA_MENU'] = message.strip().lower()
            return self._start_ordering_flow(user_id, entities)
        
        return f"Maaf kak, menu tidak ditemukan 😔\n\nSilakan pilih dari:\n{self._format_menu_list()}"
    
    def _handle_asking_quantity_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        """Handle when bot is asking for quantity."""
        state_data = state['data']
        
        if intent == 'pembatalan' or intent == 'batalkan_pesanan':
            self.reset_user_state(user_id)
            return "Oke kak, batal dulu ya. Kalau mau pesan lagi tinggal ketik 'pesan' 😊"
        
        # Extract quantity from entities or message
        jumlah = entities.get('JUMLAH')
        if not jumlah:
            # Try to find number in message
            import re
            numbers = re.findall(r'\d+', message)
            if numbers:
                jumlah = numbers[0]
            else:
                # Check ordinal words
                ordinals = {'satu': '1', 'dua': '2', 'tiga': '3', 'empat': '4', 'lima': '5',
                           'enam': '6', 'tujuh': '7', 'delapan': '8', 'sembilan': '9', 'sepuluh': '10'}
                for word, num in ordinals.items():
                    if word in message.lower():
                        jumlah = num
                        break
        
        if not jumlah:
            return "Mau berapa porsi kak? Ketik angkanya ya (contoh: 1, 2, atau 3)"
        
        state_data['JUMLAH'] = jumlah
        menu_name = state_data.get('NAMA_MENU', '')
        
        # Check if need sambal
        needs_sambal = any(m in menu_name.lower() for m in self.MENU_NEED_SAMBAL)
        if needs_sambal and not state_data.get('JENIS_SAMBAL'):
            self.update_user_state(user_id, 'asking_sambal', state_data)
            menu = state_data.get('menu_detail', {})
            return self._ask_sambal_preference(menu.get('nama_menu', menu_name), jumlah)
        
        # Go to confirmation
        return self._go_to_confirmation(user_id, state_data)
    
    def _handle_asking_sambal_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        """Handle when bot is asking for sambal preference."""
        state_data = state['data']
        msg_lower = message.lower().strip()
        
        print(f"[DEBUG] Asking Sambal - Message: '{message}'")
        
        if intent == 'pembatalan' or intent == 'batalkan_pesanan':
            self.reset_user_state(user_id)
            return "Oke kak, batal dulu ya. Kalau mau pesan lagi tinggal ketik 'pesan' 😊"
        
        # Check for sambal entity from NLU
        sambal = entities.get('JENIS_SAMBAL')
        
        # Parse from message if not detected by NLU
        if not sambal:
            # Check for exact or partial match with sambal options
            for opt in self.SAMBAL_OPTIONS:
                # Full match: "sambal bawang"
                if opt in msg_lower:
                    sambal = opt
                    break
                # Partial match: "bawang", "ijo", "terasi"
                sambal_type = opt.replace('sambal ', '').replace('tanpa ', '')
                if sambal_type in msg_lower and len(sambal_type) > 2:
                    sambal = opt
                    break
            
            # Check for number selection (1-5)
            if not sambal:
                import re
                nums = re.findall(r'\d', message)
                if nums:
                    idx = int(nums[0]) - 1
                    if 0 <= idx < len(self.SAMBAL_OPTIONS):
                        sambal = self.SAMBAL_OPTIONS[idx]
                        print(f"[DEBUG] Sambal selected by number: {idx+1} -> {sambal}")
        
        # If still no sambal detected, ask again with hint
        if not sambal:
            menu_name = state_data.get('NAMA_MENU', '')
            jumlah = state_data.get('JUMLAH', '1')
            return f"""Maaf kak, pilihan sambal tidak valid 😅

{self._ask_sambal_preference(menu_name, jumlah)}

💡 *Tip:* Balas dengan angka (1-5) atau nama sambal (contoh: "bawang" atau "ijo")"""
        
        print(f"[DEBUG] Sambal confirmed: {sambal}")
        state_data['JENIS_SAMBAL'] = sambal
        return self._go_to_confirmation(user_id, state_data)
    
    def _ask_sambal_preference(self, menu_name: str, jumlah: str) -> str:
        """Generate sambal preference question."""
        options = ""
        for i, opt in enumerate(self.SAMBAL_OPTIONS, 1):
            emoji = "🌶️" if "sambal" in opt and opt != "tanpa sambal" else "🚫"
            options += f"{i}. {opt.title()} {emoji}\n"
        
        return f"""*{menu_name}* x {jumlah} porsi 👍

🌶️ Mau pakai sambal apa kak?

{options}
Balas dengan angka (1-5) atau nama sambalnya"""
    
    def _go_to_confirmation(self, user_id: str, state_data: dict) -> str:
        """Generate confirmation message and update state."""
        menu_name = state_data.get('NAMA_MENU')
        menu = state_data.get('menu_detail') or db.get_menu_by_name(menu_name)
        
        if not menu:
            self.reset_user_state(user_id)
            return "Maaf ada kesalahan. Silakan pesan ulang kak."
        
        jumlah = state_data.get('JUMLAH', '1')
        jumlah_int = int(jumlah) if str(jumlah).isdigit() else 1
        sambal = state_data.get('JENIS_SAMBAL', '')
        
        total = menu['harga'] * jumlah_int
        
        state_data['total_harga'] = total
        state_data['harga_satuan'] = menu['harga']
        state_data['menu_detail'] = menu
        state_data['JUMLAH'] = str(jumlah_int)
        
        self.update_user_state(user_id, 'confirming', state_data)
        
        sambal_text = f"\n🌶️ Sambal: {sambal.title()}" if sambal else ""
        
        return f"""📝 *KONFIRMASI PESANAN*

🍽️ Menu: {menu['nama_menu']}
📦 Jumlah: {jumlah_int} porsi{sambal_text}
💰 Total: Rp {total:,}

━━━━━━━━━━━━━━━━
✅ Balas *YA* untuk konfirmasi
❌ Balas *BATAL* untuk membatalkan"""
    
    def _handle_confirming_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        """Handle order confirmation."""
        state_data = state['data']
        msg_lower = message.lower().strip()
        
        # User confirms
        if intent == 'konfirmasi' or msg_lower in ['ya', 'yes', 'iya', 'ok', 'oke', 'siap', 'lanjut', 'gas', 'y']:
            menu = state_data.get('menu_detail', {})
            menu_name = menu.get('nama_menu', state_data.get('NAMA_MENU', ''))
            jumlah = state_data.get('JUMLAH', '1')
            sambal = state_data.get('JENIS_SAMBAL', '')
            total = state_data.get('total_harga', 0)
            
            detail = menu_name
            if sambal:
                detail += f" ({sambal})"
            detail += f" x {jumlah} porsi"
            
            pesanan_id = db.create_pesanan(user_id, detail, total)
            
            self.update_user_state(user_id, 'awaiting_payment', {'id_pesanan': pesanan_id, 'total': total, 'detail': detail})
            
            return f"""✅ *PESANAN BERHASIL DIBUAT!*

📋 ID Pesanan: #{pesanan_id}
🍽️ {detail}
💰 Total: Rp {total:,}

━━━━━━━━━━━━━━━━
{self._get_payment_info()}

📲 Setelah transfer, kirim *'SUDAH BAYAR'* ya kak!"""
        
        # User cancels
        elif intent == 'pembatalan' or intent == 'batalkan_pesanan' or msg_lower in ['batal', 'tidak', 'no', 'cancel', 'gak jadi', 'n']:
            self.reset_user_state(user_id)
            return "❌ Pesanan dibatalkan.\n\nMau pesan lagi? Ketik 'menu' 😊"
        
        # Change sambal
        elif 'ganti sambal' in msg_lower or 'ubah sambal' in msg_lower:
            self.update_user_state(user_id, 'asking_sambal', state_data)
            return self._ask_sambal_preference(state_data.get('NAMA_MENU', ''), state_data.get('JUMLAH', '1'))
        
        # Change quantity
        elif 'ganti jumlah' in msg_lower or 'ubah jumlah' in msg_lower:
            self.update_user_state(user_id, 'asking_quantity', state_data)
            return "Mau ganti jadi berapa porsi kak?"
        
        else:
            return "Mohon konfirmasi pesanan:\n\n✅ Balas *YA* untuk konfirmasi\n❌ Balas *BATAL* untuk membatalkan\n\n💡 Atau ketik 'ganti sambal'/'ganti jumlah' untuk mengubah"
    
    def _handle_awaiting_payment_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        """Handle payment confirmation state."""
        state_data = state['data']
        msg_lower = message.lower().strip()
        
        print(f"[DEBUG] Awaiting Payment - Intent: {intent}, Message: '{message}'")
        
        # Priority 1: Check intent first (most reliable)
        if intent == 'konfirmasi_pembayaran':
            pesanan_id = state_data.get('id_pesanan')
            print(f"[DEBUG] Payment confirmed via intent for order #{pesanan_id}")
            
            if pesanan_id:
                db.update_status_pesanan(pesanan_id, 'diproses')
            
            self.reset_user_state(user_id)
            
            return f"""✅ *PEMBAYARAN DIKONFIRMASI!*

Pesanan #{pesanan_id} sedang diproses 👨‍🍳
⏱️ Estimasi: 15-30 menit

Terima kasih sudah memesan di Kedai Ayam Merdeka! 🍗
Ditunggu orderan berikutnya ya kak!"""
        
        # Priority 2: Check for payment-related keywords
        payment_keywords = ['bayar', 'transfer', 'tf', 'lunas', 'sudah bayar', 'udah bayar', 'sudah tf', 'udah tf']
        if any(keyword in msg_lower for keyword in payment_keywords):
            pesanan_id = state_data.get('id_pesanan')
            print(f"[DEBUG] Payment confirmed via keyword for order #{pesanan_id}")
            
            if pesanan_id:
                db.update_status_pesanan(pesanan_id, 'diproses')
            
            self.reset_user_state(user_id)
            
            return f"""✅ *PEMBAYARAN DIKONFIRMASI!*

Pesanan #{pesanan_id} sedang diproses 👨‍🍳
⏱️ Estimasi: 15-30 menit

Terima kasih sudah memesan di Kedai Ayam Merdeka! 🍗
Ditunggu orderan berikutnya ya kak!"""
        
        # Check for payment info request
        elif intent == 'info_pembayaran' or 'cara' in msg_lower or 'gimana' in msg_lower or 'rekening' in msg_lower:
            return self._get_payment_info()
        
        # Check for cancellation
        elif intent == 'pembatalan' or intent == 'batalkan_pesanan' or 'batal' in msg_lower:
            pesanan_id = state_data.get('id_pesanan')
            if pesanan_id:
                db.update_status_pesanan(pesanan_id, 'batal')
            self.reset_user_state(user_id)
            return f"❌ Pesanan #{pesanan_id} dibatalkan.\n\nMau pesan lagi? Ketik 'menu' 😊"
        
        # Default: remind about payment
        else:
            total = state_data.get('total', 0)
            detail = state_data.get('detail', '')
            pesanan_id = state_data.get('id_pesanan', '')
            
            return f"""💳 *MENUNGGU PEMBAYARAN*

📋 Pesanan #{pesanan_id}
🍽️ {detail}
💰 Total: Rp {total:,}

{self._get_payment_info()}

📲 Kirim *'SUDAH BAYAR'* setelah transfer ya kak!"""
    
    def _handle_modifying_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        """Handle order modification."""
        if intent == 'pembatalan' or 'batal' in message.lower():
            self.reset_user_state(user_id)
            return "Modifikasi dibatalkan."
        
        state_data = state['data']
        
        if entities.get('NAMA_MENU'):
            state_data['NAMA_MENU'] = entities['NAMA_MENU']
        if entities.get('JUMLAH'):
            state_data['JUMLAH'] = entities['JUMLAH']
        
        menu_name = state_data.get('NAMA_MENU')
        jumlah = state_data.get('JUMLAH', '1')
        
        if menu_name:
            menu = db.get_menu_by_name(menu_name)
            if not menu:
                return f"Menu '{menu_name}' tidak tersedia."
            jumlah_int = int(jumlah) if str(jumlah).isdigit() else 1
            total = menu['harga'] * jumlah_int
            detail = f"{menu_name} x {jumlah_int}"
        else:
            return "Mau diubah jadi apa kak? Sebutkan menu dan jumlahnya."
        
        self.reset_user_state(user_id)
        return f"✅ Pesanan diubah!\n\nDetail: {detail}\nTotal: Rp {total:,}\n\nSilakan lanjutkan pembayaran."
    
    def _get_response(self, intent: str) -> str:
        """Get random response for intent from JSON."""
        for intent_data in nlu.intents["intents"]:
            if intent_data["tag"] == intent:
                if not intent_data["responses"]:
                    return "Maaf, saya tidak mengerti."
                return random.choice(intent_data["responses"])
        return "Maaf, saya tidak mengerti."
    
    def _format_menu_list(self) -> str:
        """Format menu list with categories."""
        menus = db.get_all_menu()
        if not menus:
            return "Menu belum tersedia."
        
        categories = {}
        for menu in menus:
            cat = menu.get('kategori', 'Lainnya') or 'Lainnya'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(menu)
        
        menu_text = "📋 *MENU KEDAI AYAM MERDEKA*\n"
        
        for cat, items in categories.items():
            menu_text += f"\n*{cat}:*\n"
            for item in items:
                menu_text += f"• {item['nama_menu']} - Rp {item['harga']:,}\n"
        
        return menu_text
    
    def _get_payment_info(self) -> str:
        """Return payment information."""
        return """💳 *METODE PEMBAYARAN*

🏦 Bank BCA: 1234567890
📱 OVO/GoPay: 081234567890
a.n. Kedai Ayam Merdeka"""
    
    def _get_time_greeting(self) -> str:
        """Get greeting based on current time."""
        hour = datetime.now().hour
        
        if 5 <= hour < 11:
            greeting = "Selamat pagi"
        elif 11 <= hour < 15:
            greeting = "Selamat siang"
        elif 15 <= hour < 18:
            greeting = "Selamat sore"
        else:
            greeting = "Selamat malam"
        
        return f"{greeting} kak! Selamat datang di Kedai Ayam Merdeka 🍗"

dialog_manager = DialogManager()
