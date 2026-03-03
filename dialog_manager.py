from config import Config
from database import db
from nlu import nlu
import random
from datetime import datetime

class DialogManager:
    def __init__(self):
        # Menu yang perlu tanya sambal
        self.MENU_NEED_SAMBAL = ['ayam geprek', 'ayam bakar', 'ayam goreng', 'ayam penyet', 'ayam crispy']
        
        # Pilihan sambal
        self.SAMBAL_OPTIONS = ['sambal bawang', 'sambal ijo', 'sambal terasi', 'sambal matah', 'tanpa sambal']
    
    def get_user_state(self, user_id: str) -> dict:
        return db.get_user_state(user_id)
    
    def update_user_state(self, user_id: str, state: str, data: dict = None, cart: list = None):
        db.update_user_state(user_id, state, data, cart)
    
    def reset_user_state(self, user_id: str):
        db.reset_user_state(user_id)
    
    def generate_response(self, user_id: str, message: str) -> str:
        """Main response generator with improved flow handling."""
        try:
            state = self.get_user_state(user_id)
            intent, entities = nlu.process(message)
            
            print(f"[DEBUG] User: {user_id} | State: {state['state']} | Intent: {intent} | Entities: {entities}")
            
            # Global intents — berlaku di semua state kecuali idle (ditangani sendiri)
            if state['state'] != 'idle':
                if intent == 'salam':
                    self.reset_user_state(user_id)
                    greeting = self._get_time_greeting()
                    return f"{greeting}\n\nAda yang bisa dibantu? 😊\n\n💡 Ketik *pesan* untuk mulai memesan\n📋 Ketik *menu* untuk lihat daftar menu"
                elif intent == 'terima_kasih':
                    self.reset_user_state(user_id)
                    return self._get_response(intent)
            
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
            return f"{greeting}\n\nAda yang bisa dibantu? 😊\n\n💡 Ketik *pesan* untuk mulai memesan\n📋 Ketik *menu* untuk lihat daftar menu\n⏰ Jam operasional: {Config.JAM_BUKA} - {Config.JAM_TUTUP}"
        
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
        
        # Fallback — jangan dump menu, arahkan user
        return "Maaf kak, saya belum mengerti 😅\n\nCoba ketik salah satu:\n📋 *menu* — lihat daftar menu\n🛒 *pesan* — mulai memesan\n📍 *lokasi* — alamat kedai\n⏰ *jam* — jam operasional"
    
    def _start_ordering_flow(self, user_id: str, entities: dict) -> str:
        """Start the ordering flow with multi-item support."""
        items = entities.get('ITEMS', [])
        
        if not items and entities.get('NAMA_MENU'):
            items = [{
                'NAMA_MENU': entities.get('NAMA_MENU'),
                'JUMLAH': entities.get('JUMLAH'),
                'JENIS_SAMBAL': entities.get('JENIS_SAMBAL')
            }]
            
        if not items:
            return "Maaf kak, pesanan tidak terbaca. Mau pesan apa?"
            
        state = self.get_user_state(user_id)
        cart = state.get('cart', [])
        if state['state'] not in ['asking_menu', 'confirming']:
            cart = []
            
        not_found = []
        
        for item in items:
            menu_name = item.get('NAMA_MENU')
            if not menu_name: continue
            
            menu = db.get_menu_by_name(menu_name)
            if not menu:
                not_found.append(menu_name)
            else:
                cart.append({
                    'menu_detail': menu,
                    'JUMLAH': item.get('JUMLAH') or '1',
                    'JENIS_SAMBAL': item.get('JENIS_SAMBAL')
                })
                
        if not cart:
            nf_msg = ", ".join(not_found)
            return f"Maaf kak, menu *{nf_msg}* tidak tersedia 😔\n\n{self._format_menu_list()}"
            
        msg_prefix = ""
        if not_found:
            msg_prefix = f"Maaf kak, menu *{', '.join(not_found)}* tidak tersedia jadi tidak kami masukkan ya.\n\n"
            
        # Check if any item needs sambal
        for idx, cart_item in enumerate(cart):
            menu_name = cart_item['menu_detail']['nama_menu'].lower()
            needs_sambal = any(m in menu_name for m in self.MENU_NEED_SAMBAL)
            if needs_sambal and not cart_item.get('JENIS_SAMBAL'):
                self.update_user_state(user_id, 'asking_sambal', {'cart_index': idx}, cart=cart)
                return msg_prefix + self._ask_sambal_preference(cart_item['menu_detail']['nama_menu'], cart_item['JUMLAH'])
                
        return msg_prefix + self._go_to_confirmation(user_id, cart)
    
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
        # Kept for backward compatibility but bypassed by _start_ordering_flow defaulting JUMLAH to 1
        return self._start_ordering_flow(user_id, entities)
    
    def _handle_asking_sambal_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        """Handle when bot is asking for sambal preference."""
        state_data = state['data']
        cart = state.get('cart', [])
        idx = state_data.get('cart_index', 0)
        
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
                    val = int(nums[0]) - 1
                    if 0 <= val < len(self.SAMBAL_OPTIONS):
                        sambal = self.SAMBAL_OPTIONS[val]
                        print(f"[DEBUG] Sambal selected by number: {val+1} -> {sambal}")
        
        if not sambal:
            if idx < len(cart):
                cart_item = cart[idx]
                menu_name = cart_item['menu_detail']['nama_menu']
                jumlah = cart_item['JUMLAH']
                return f"""Maaf kak, pilihan sambal tidak valid 😅

{self._ask_sambal_preference(menu_name, jumlah)}

💡 *Tip:* Balas dengan angka (1-5) atau nama sambal (contoh: "bawang" atau "ijo")"""
            else:
                return "Maaf kak, pesanan tidak valid."
        
        print(f"[DEBUG] Sambal confirmed: {sambal}")
        if idx < len(cart):
            cart[idx]['JENIS_SAMBAL'] = sambal
            
        # Check if there are other items needing sambal
        for next_idx in range(idx + 1, len(cart)):
            cart_item = cart[next_idx]
            menu_name = cart_item['menu_detail']['nama_menu'].lower()
            needs_sambal = any(m in menu_name for m in self.MENU_NEED_SAMBAL)
            if needs_sambal and not cart_item.get('JENIS_SAMBAL'):
                self.update_user_state(user_id, 'asking_sambal', {'cart_index': next_idx}, cart=cart)
                return self._ask_sambal_preference(cart_item['menu_detail']['nama_menu'], cart_item['JUMLAH'])
                
        # All complete
        return self._go_to_confirmation(user_id, cart)
    
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
    
    def _go_to_confirmation(self, user_id: str, cart: list) -> str:
        """Generate confirmation message and update state."""
        if not cart:
            self.reset_user_state(user_id)
            return "Keranjang kosong."
            
        total_harga = 0
        details = []
        
        for item in cart:
            menu = item['menu_detail']
            jumlah = int(item['JUMLAH']) if str(item['JUMLAH']).isdigit() else 1
            sambal = item.get('JENIS_SAMBAL', '')
            
            subtotal = menu['harga'] * jumlah
            total_harga += subtotal
            
            detail_str = f"{jumlah} {menu['nama_menu']}"
            if sambal: detail_str += f" ({sambal.title()})"
            details.append(detail_str)
            
        detail_text = "\n".join([f"• {d}" for d in details])
        
        # Save to state
        self.update_user_state(user_id, 'confirming', {
            'total_harga': total_harga,
            'details_list': details,
            'detail_text': detail_text
        }, cart=cart)
        
        return f"""📝 *KONFIRMASI PESANAN*

{detail_text}
💰 Total: Rp {total_harga:,}

━━━━━━━━━━━━━━━━
✅ Balas *YA* untuk konfirmasi
❌ Balas *BATAL* untuk membatalkan
🛒 Balas *TAMBAH* jika ada yang kurang"""
    
    def _handle_confirming_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        """Handle order confirmation."""
        state_data = state['data']
        msg_lower = message.lower().strip()
        
        # User wants to add more
        if 'tambah' in msg_lower or 'pesan lagi' in msg_lower or entities.get('ITEMS'):
            if entities.get('ITEMS'):
                return self._start_ordering_flow(user_id, entities)
            else:
                return f"Boleh kak, mau tambah pesanan apa?\n\n{self._format_menu_list()}"
                
        # User confirms
        if intent == 'konfirmasi' or msg_lower in ['ya', 'yes', 'iya', 'ok', 'oke', 'siap', 'lanjut', 'gas', 'y', 'betul']:
            total = state_data.get('total_harga', 0)
            detail_text = state_data.get('detail_text', '')
            details_list = state_data.get('details_list', [])
            
            full_detail = ", ".join(details_list)
            
            pesanan_id = db.create_pesanan(user_id, full_detail, total)
            
            self.update_user_state(user_id, 'awaiting_payment', {'id_pesanan': pesanan_id, 'total': total, 'detail': detail_text})
            
            return f"""✅ *PESANAN BERHASIL DIBUAT!*

📋 ID Pesanan: #{pesanan_id}

{detail_text}
💰 Total: Rp {total:,}

━━━━━━━━━━━━━━━━
{self._get_payment_info()}

📲 Setelah transfer, kirim *'SUDAH BAYAR'* ya kak!"""
        
        # User cancels
        elif intent == 'pembatalan' or intent == 'batalkan_pesanan' or msg_lower in ['batal', 'tidak', 'no', 'cancel', 'gak jadi', 'n']:
            self.reset_user_state(user_id)
            return "❌ Pesanan dibatalkan.\n\nMau pesan lagi? Ketik 'menu' 😊"
            
        else:
            return "Mohon konfirmasi pesanan:\n\n✅ Balas *YA* untuk memproses pesanan\n❌ Balas *BATAL* untuk membatalkan\n🛒 Balas *TAMBAH* jika ada yang kurang"
    
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
