from config import Config
from database import db
from nlu import nlu
import random
import re
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
    
    def generate_response(self, user_id: str, message: str, nama_pelanggan: str = "Pelanggan") -> str:
        'Main response generator with improved flow handling and chat logging.'
        try:
            state = self.get_user_state(user_id)
            state_before = state['state']
            intent, entities = nlu.process(message)
            
            print(f"[DEBUG] User: {user_id} | State: {state['state']} | Intent: {intent} | Entities: {entities}")
            
            response = None
            
            # Global intents - berlaku di semua state kecuali idle (ditangani sendiri)
            if state['state'] != 'idle':
                if intent == 'salam':
                    self.reset_user_state(user_id)
                    greeting = self._get_time_greeting()
                    response = f"{greeting}\n\nAda yang bisa dibantu? \n\n Ketik *pesan* untuk mulai memesan\n Ketik *menu* untuk lihat daftar menu"
                elif intent == 'terima_kasih':
                    self.reset_user_state(user_id)
                    response = self._get_response(intent)
            
            if response is None:
                if state['state'] == 'idle':
                    response = self._handle_idle_state(user_id, intent, entities, message)
                elif state['state'] == 'asking_menu':
                    response = self._handle_asking_menu_state(user_id, state, intent, entities, message)
                elif state['state'] == 'asking_quantity':
                    response = self._handle_asking_quantity_state(user_id, state, intent, entities, message)
                elif state['state'] == 'asking_sambal':
                    response = self._handle_asking_sambal_state(user_id, state, intent, entities, message)
                elif state['state'] == 'asking_time':
                    response = self._handle_asking_time_state(user_id, state, intent, entities, message)
                elif state['state'] == 'confirming':
                    response = self._handle_confirming_state(user_id, state, intent, entities, message)
                elif state['state'] == 'awaiting_payment':
                    response = self._handle_awaiting_payment_state(user_id, state, intent, entities, message)
                elif state['state'] == 'modifying':
                    response = self._handle_modifying_state(user_id, state, intent, entities, message)
                elif state['state'] == 'asking_feedback':
                    response = self._handle_asking_feedback_state(user_id, state, intent, entities, message)
                else:
                    response = "Maaf, saya tidak mengerti. Ketik 'menu' untuk melihat daftar menu ya kak!"
            
            # Get state after processing
            state_after = self.get_user_state(user_id)['state']
            
            # Calculate confidence score (based on fuzzy matching score from NLU)
            confidence = self._calculate_confidence(intent, entities)
            
            # Log the interaction
            db.log_chat_interaction(
                id_pelanggan=user_id,
                nama_pelanggan=nama_pelanggan,
                pesan_masuk=message,
                intent_terdeteksi=intent,
                confidence_score=confidence,
                entities_extracted=entities,
                pesan_keluar=response,
                state_sebelumnya=state_before,
                state_setelahnya=state_after
            )
            
            return response
        except Exception as e:
            print(f"[ERROR] generate_response: {e}")
            import traceback
            traceback.print_exc()
            return "Maaf kak, ada sedikit gangguan. Coba ulangi pesanan kakak ya!"
    
    def _calculate_confidence(self, intent: str, entities: dict) -> float:
        'Calculate confidence score based on intent and entities.'
        # Base confidence
        confidence = 0.7
        
        # Boost if entities found
        if entities.get('NAMA_MENU'):
            confidence += 0.15
        if entities.get('JUMLAH'):
            confidence += 0.05
        if entities.get('JENIS_SAMBAL'):
            confidence += 0.05
        
        # Unknown intent reduces confidence
        if intent == 'unknown':
            confidence = 0.3
        
        return min(confidence, 1.0)
    
    def _handle_idle_state(self, user_id: str, intent: str, entities: dict, message: str) -> str:
        'Handle user input when in idle state.'

        direct_menu = db.get_menu_by_name(message.strip())
        if direct_menu and intent in ['pesan_menu', 'unknown', 'konfirmasi']:
            direct_entities = {
                'NAMA_MENU': message.strip(),
                'JUMLAH': entities.get('JUMLAH'),
                'JENIS_SAMBAL': entities.get('JENIS_SAMBAL'),
                'ITEMS': [{
                    'NAMA_MENU': message.strip(),
                    'JUMLAH': entities.get('JUMLAH'),
                    'JENIS_SAMBAL': entities.get('JENIS_SAMBAL')
                }],
                'WAKTU_PENGAMBILAN': entities.get('WAKTU_PENGAMBILAN')
            }
            return self._start_ordering_flow(user_id, direct_entities)
        
        # If menu entity detected, start ordering flow
        if entities.get('NAMA_MENU'):
            return self._start_ordering_flow(user_id, entities)
        
        if intent == 'salam':
            greeting = self._get_time_greeting()
            return f"{greeting}\n\nAda yang bisa dibantu? \n\n Ketik *pesan* untuk mulai memesan\n Ketik *menu* untuk lihat daftar menu\n Jam operasional: {Config.JAM_BUKA} - {Config.JAM_TUTUP}"
        
        elif intent == 'terima_kasih':
            return self._get_response(intent)
        
        elif intent == 'pesan_menu':
            menu_list = self._format_menu_list()
            self.update_user_state(user_id, 'asking_menu', {})
            return f"Siap kak! Mau pesan apa?\n\n{menu_list}\n\n *Contoh:* Ayam Geprek, Es Teh Manis"
        
        elif intent == 'cek_ketersediaan':
            if entities.get('NAMA_MENU'):
                menu = db.get_menu_by_name(entities['NAMA_MENU'])
                if menu:
                    return f"[OK] *{menu['nama_menu']}* tersedia kak!\nHarga: Rp {menu['harga']:,}\n\nMau pesan? Ketik 'pesan {menu['nama_menu']}'"
                else:
                    return "Maaf kak, menu tersebut tidak tersedia "
            else:
                return "Menu apa yang mau dicek kak?"
        
        elif intent == 'cek_status':
            pesanan = db.get_last_pesanan(user_id)
            if pesanan:
                status_emoji = {'dipesan': '', 'diproses': '', 'selesai': '[OK]', 'batal': '[X]'}
                emoji = status_emoji.get(pesanan['status'], '')
                return f"{emoji} *Status Pesanan #{pesanan['id_pesanan']}*\n\nDetail: {pesanan['detail_pesanan']}\nTotal: Rp {pesanan['total_harga']:,}\nStatus: *{pesanan['status'].upper()}*"
            else:
                return "Kakak belum memiliki pesanan aktif. Mau pesan sekarang? Ketik 'pesan'"
        
        elif intent == 'info_promo':
            return self._get_response(intent) if self._get_response(intent) != "Maaf, saya tidak mengerti." else " Promo: Beli 2 Ayam Geprek GRATIS Es Teh Manis!"
        
        elif intent == 'info_jam':
            return f" *Jam Operasional Kedai Ayam Merdeka*\n\nSetiap Hari: {Config.JAM_BUKA} - {Config.JAM_TUTUP}"
        
        elif intent == 'info_pembayaran':
            return self._get_payment_info()
        
        elif intent == 'rekomendasi_menu':
            menus = db.get_all_menu()
            if menus:
                menu = random.choice(menus)
                return f" *Rekomendasi Hari Ini:*\n\n*{menu['nama_menu']}*\nHarga: Rp {menu['harga']:,}\n\nMau pesan kak? Ketik 'pesan {menu['nama_menu']}'"
            return "Menu belum tersedia saat ini."
        
        elif intent == 'ubah_pesanan':
            pesanan = db.get_last_pesanan(user_id)
            if pesanan and pesanan['status'] == 'dipesan':
                self.update_user_state(user_id, 'modifying', {'id_pesanan': pesanan['id_pesanan']})
                return f"Pesanan #{pesanan['id_pesanan']} akan diubah.\nDetail: {pesanan['detail_pesanan']}\n\nMau ganti jadi apa kak?"
            elif pesanan:
                return "Maaf kak, pesanan sudah diproses "
            return "Kakak belum punya pesanan aktif."
        
        elif intent == 'batalkan_pesanan' or intent == 'pembatalan':
            pesanan = db.get_last_pesanan(user_id)
            if pesanan and pesanan['status'] == 'dipesan':
                db.update_status_pesanan(pesanan['id_pesanan'], 'batal')
                self.reset_user_state(user_id)
                return f"[X] Pesanan #{pesanan['id_pesanan']} dibatalkan.\n\nMau pesan lagi? Ketik 'menu'"
            elif pesanan:
                return "Maaf kak, pesanan sudah diproses "
            return "Kakak belum punya pesanan aktif."
        
        elif intent == 'konfirmasi_pembayaran':
            pesanan = db.get_last_pesanan(user_id)
            if pesanan and pesanan['status'] == 'dipesan':
                db.update_status_pesanan(pesanan['id_pesanan'], 'diproses')
                return f"[OK] *Pembayaran Dikonfirmasi!*\n\nPesanan #{pesanan['id_pesanan']} sedang diproses.\nEstimasi 15-30 menit.\n\nTerima kasih! "
            return "Kakak belum punya pesanan yang menunggu pembayaran."
        
        elif intent == 'tanya_harga':
            return f"Berikut daftar harga:\n\n{self._format_menu_list()}"
        
        elif intent == 'delivery':
            return " *Layanan Delivery*\n\nRadius: 5km\nOngkir: Rp 5.000 - Rp 15.000\n\nMau pesan delivery? Ketik 'pesan'"
        
        elif intent in ['lokasi', 'komplain', 'menu_pedas', 'chitchat_baik']:
            response = self._get_response(intent)
            if response != "Maaf, saya tidak mengerti.":
                return response
        
        # Fallback - jangan dump menu, arahkan user
        return "Maaf kak, saya belum mengerti \n\nCoba ketik salah satu:\n *menu* - lihat daftar menu\n *pesan* - mulai memesan\n *lokasi* - alamat kedai\n *jam* - jam operasional"
    
    def _start_ordering_flow(self, user_id: str, entities: dict) -> str:
        'Start the ordering flow with multi-item support.'
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
            return f"Maaf kak, menu *{nf_msg}* tidak tersedia \n\n{self._format_menu_list()}"
            
        msg_prefix = ""
        if not_found:
            msg_prefix = f"Maaf kak, menu *{', '.join(not_found)}* tidak tersedia jadi tidak kami masukkan ya.\n\n"
            
        # Check if any item needs sambal
        for idx, cart_item in enumerate(cart):
            menu_name = cart_item['menu_detail']['nama_menu'].lower()
            needs_sambal = any(m in menu_name for m in self.MENU_NEED_SAMBAL)
            if needs_sambal and not self._menu_has_embedded_sambal(menu_name) and not cart_item.get('JENIS_SAMBAL'):
                self.update_user_state(user_id, 'asking_sambal', {'cart_index': idx, 'cart': cart, 'waktu': entities.get('WAKTU_PENGAMBILAN')}, cart=cart)
                return msg_prefix + self._ask_sambal_preference(cart_item['menu_detail']['nama_menu'], cart_item['JUMLAH'])
        
        # Check if time is provided, if not ask for it
        waktu = entities.get('WAKTU_PENGAMBILAN')
        if not waktu:
            self.update_user_state(user_id, 'asking_time', {'cart': cart}, cart=cart)
            return msg_prefix + self._ask_pickup_time()
                
        return msg_prefix + self._go_to_confirmation(user_id, cart, waktu)
    
    def _handle_asking_menu_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        'Handle when bot is asking for menu choice.'
        if intent == 'pembatalan' or intent == 'batalkan_pesanan':
            self.reset_user_state(user_id)
            return "Oke kak, batal dulu ya. Kalau mau pesan lagi tinggal ketik 'pesan' "

        menu = db.get_menu_by_name(message.strip())
        if menu:
            direct_entities = {
                'NAMA_MENU': message.strip(),
                'JUMLAH': entities.get('JUMLAH'),
                'JENIS_SAMBAL': entities.get('JENIS_SAMBAL'),
                'ITEMS': [{
                    'NAMA_MENU': message.strip(),
                    'JUMLAH': entities.get('JUMLAH'),
                    'JENIS_SAMBAL': entities.get('JENIS_SAMBAL')
                }],
                'WAKTU_PENGAMBILAN': entities.get('WAKTU_PENGAMBILAN')
            }
            return self._start_ordering_flow(user_id, direct_entities)
        
        if entities.get('NAMA_MENU'):
            return self._start_ordering_flow(user_id, entities)
        
        return f"Maaf kak, menu tidak ditemukan \n\nSilakan pilih dari:\n{self._format_menu_list()}"
    
    def _handle_asking_quantity_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        # Kept for backward compatibility but bypassed by _start_ordering_flow defaulting JUMLAH to 1
        return self._start_ordering_flow(user_id, entities)

    def _menu_has_embedded_sambal(self, menu_name: str) -> bool:
        'Return True when the menu name already contains a specific sambal variant.'
        if not menu_name:
            return False

        menu_lower = menu_name.lower()
        embedded_keywords = [
            'sambal bawang',
            'sambal ijo',
            'sambal hijau',
            'sambal merah',
            'sambal terasi',
            'sambal matah',
            'tanpa sambal'
        ]
        if any(keyword in menu_lower for keyword in embedded_keywords):
            return True

        bare_variant_pattern = r'(?:\+|\s)(bawang|ijo|hijau|merah|terasi|matah)\s*$'
        return re.search(bare_variant_pattern, menu_lower) is not None

    def _extract_sambal_choice(self, message: str) -> str | None:
        'Resolve user sambal choice from raw message with strict validation.'
        msg_lower = re.sub(r'[^a-z0-9\s]', ' ', message.lower())
        msg_lower = re.sub(r'\s+', ' ', msg_lower).strip()

        if not msg_lower or msg_lower == 'sambal':
            return None

        number_match = re.search(r'\b([1-5])\b', msg_lower)
        if number_match:
            return self.SAMBAL_OPTIONS[int(number_match.group(1)) - 1]

        alias_map = {
            'sambal bawang': ['sambal bawang', 'bawang'],
            'sambal ijo': ['sambal ijo', 'sambal hijau', 'ijo', 'hijau'],
            'sambal terasi': ['sambal terasi', 'terasi'],
            'sambal matah': ['sambal matah', 'matah'],
            'tanpa sambal': [
                'tanpa sambal',
                'tanpa',
                'tidak pakai sambal',
                'ga pakai sambal',
                'gak pakai sambal',
                'nggak pakai sambal',
                'no sambal'
            ]
        }

        for canonical, aliases in alias_map.items():
            for alias in sorted(aliases, key=len, reverse=True):
                pattern = r'(?<!\w)' + re.escape(alias).replace(r'\ ', r'\s+') + r'(?!\w)'
                if re.search(pattern, msg_lower):
                    return canonical

        return None
    
    def _handle_asking_sambal_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        'Handle when bot is asking for sambal preference.'
        state_data = state['data']
        cart = state.get('cart', [])
        idx = state_data.get('cart_index', 0)
        
        print(f"[DEBUG] Asking Sambal - Message: '{message}'")
        
        if intent == 'pembatalan' or intent == 'batalkan_pesanan':
            self.reset_user_state(user_id)
            return "Oke kak, batal dulu ya. Kalau mau pesan lagi tinggal ketik 'pesan' "
        
        sambal = self._extract_sambal_choice(message)
        
        if not sambal:
            if idx < len(cart):
                cart_item = cart[idx]
                menu_name = cart_item['menu_detail']['nama_menu']
                jumlah = cart_item['JUMLAH']
                lines = [
                    "Maaf kak, pilihan sambal tidak valid ",
                    "",
                    self._ask_sambal_preference(menu_name, jumlah),
                    "",
                    " *Tip:* Balas dengan angka (1-5) atau nama sambal (contoh: \"bawang\" atau \"ijo\")"
                ]
                return "\n".join(lines)
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
            if needs_sambal and not self._menu_has_embedded_sambal(menu_name) and not cart_item.get('JENIS_SAMBAL'):
                self.update_user_state(user_id, 'asking_sambal', {'cart_index': next_idx, 'cart': cart, 'waktu': state_data.get('waktu')}, cart=cart)
                return self._ask_sambal_preference(cart_item['menu_detail']['nama_menu'], cart_item['JUMLAH'])
        
        # Check if time was provided earlier or ask now
        waktu = state_data.get('waktu')
        if not waktu:
            self.update_user_state(user_id, 'asking_time', {'cart': cart}, cart=cart)
            return self._ask_pickup_time()
                
        # All complete
        return self._go_to_confirmation(user_id, cart, waktu)
    
    def _ask_sambal_preference(self, menu_name: str, jumlah: str) -> str:
        'Generate sambal preference question.'
        options = ""
        for i, opt in enumerate(self.SAMBAL_OPTIONS, 1):
            emoji = "" if "sambal" in opt and opt != "tanpa sambal" else ""
            options += f"{i}. {opt.title()} {emoji}\n"
        
        lines = [
            f"*{menu_name}* x {jumlah} porsi ",
            "",
            " Mau pakai sambal apa kak?",
            "",
            options.rstrip(),
            "Balas dengan angka (1-5) atau nama sambalnya"
        ]
        return "\n".join(lines)
    
    def _ask_pickup_time(self) -> str:
        'Generate pickup time question.'
        lines = [
            " *KAPAN PESANAN DIAMBIL?*",
            "",
            "Pilih salah satu:",
            "- *Sekarang* - Pesanan langsung disiapkan",
            "- *Jam 12:00* - Spesifik waktu (contoh)",
            "- *30 menit lagi* - Waktu relatif",
            "- *Pagi/Siang/Sore/Malam* - Perkiraan waktu",
            "",
            " Contoh: 'jam 12 siang' atau '1 jam lagi'"
        ]
        return "\n".join(lines)
    def _handle_asking_time_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        'Handle when bot is asking for pickup time.'
        state_data = state['data']
        cart = state.get('cart', [])
        
        if intent == 'pembatalan' or intent == 'batalkan_pesanan':
            self.reset_user_state(user_id)
            return "Oke kak, batal dulu ya. Kalau mau pesan lagi tinggal ketik 'pesan' "
        
        # Try to extract time from message
        waktu = entities.get('WAKTU_PENGAMBILAN')
        
        # If not extracted by NLU, try manual parsing
        if not waktu:
            msg_lower = message.lower().strip()
            # Direct keyword matching
            if any(word in msg_lower for word in ['sekarang', 'langsung', 'segera']):
                waktu = {"type": "immediate", "value": "immediate", "formatted": "Sekarang"}
            elif 'pagi' in msg_lower:
                waktu = {"type": "specific", "value": "09:00", "formatted": "09:00"}
            elif 'siang' in msg_lower:
                waktu = {"type": "specific", "value": "12:00", "formatted": "12:00"}
            elif 'sore' in msg_lower:
                waktu = {"type": "specific", "value": "15:00", "formatted": "15:00"}
            elif 'malam' in msg_lower:
                waktu = {"type": "specific", "value": "19:00", "formatted": "19:00"}
        
        if not waktu:
            lines = [
                "Maaf kak, waktu tidak dikenali",
                "",
                self._ask_pickup_time(),
                "",
                "*Tip:* Balas dengan 'sekarang', 'jam 12', atau '1 jam lagi'"
            ]
            return "\n".join(lines)
        
        # Save time and go to confirmation
        return self._go_to_confirmation(user_id, cart, waktu)
    
    def _go_to_confirmation(self, user_id: str, cart: list, waktu: dict = None) -> str:
        'Generate confirmation message and update state.'
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
            
        detail_text = "\n".join([f"- {d}" for d in details])
        
        # Format time display
        waktu_text = "Sekarang"
        if waktu:
            waktu_text = waktu.get('formatted', 'Sekarang')
        
        # Save to state with time
        state_data = {
            'total_harga': total_harga,
            'details_list': details,
            'detail_text': detail_text,
            'waktu_pengambilan': waktu
        }
        self.update_user_state(user_id, 'confirming', state_data, cart=cart)
        
        lines = [
            " *KONFIRMASI PESANAN*",
            "",
            detail_text,
            f"Rp Total: Rp {total_harga:,}",
            f" Waktu Ambil: {waktu_text}",
            "",
            "----------------",
            "[OK] Balas *YA* untuk konfirmasi",
            "[X] Balas *BATAL* untuk membatalkan",
            " Balas *TAMBAH* jika ada yang kurang"
        ]
        return "\n".join(lines)
    
    def _handle_confirming_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        'Handle order confirmation.'
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
            waktu = state_data.get('waktu_pengambilan')
            
            full_detail = ", ".join(details_list)
            
            # Create order with pickup time
            waktu_formatted = waktu.get('formatted') if waktu else 'Sekarang'
            tipe_pengambilan = waktu.get('type') if waktu else 'immediate'
            
            pesanan_id = db.create_pesanan(
                user_id, 
                full_detail, 
                total, 
                waktu_pengambilan=waktu_formatted,
                tipe_pengambilan=tipe_pengambilan
            )
            
            self.update_user_state(user_id, 'awaiting_payment', {'id_pesanan': pesanan_id, 'total': total, 'detail': detail_text})
            
            # Format time for display
            waktu_display = waktu_formatted if waktu_formatted else 'Sekarang'
            
            lines = [
                "[OK] *PESANAN BERHASIL DIBUAT!*",
                "",
                f" ID Pesanan: #{pesanan_id}",
                f" Waktu Ambil: {waktu_display}",
                "",
                detail_text,
                f"Rp Total: Rp {total:,}",
                "",
                "----------------",
                self._get_payment_info(),
                "",
                "> Setelah transfer, kirim *'SUDAH BAYAR'* ya kak!"
            ]
            return "\n".join(lines)
        
        # User cancels
        elif intent == 'pembatalan' or intent == 'batalkan_pesanan' or msg_lower in ['batal', 'tidak', 'no', 'cancel', 'gak jadi', 'n']:
            self.reset_user_state(user_id)
            return "[X] Pesanan dibatalkan.\n\nMau pesan lagi? Ketik 'menu' "
            
        else:
            return "Mohon konfirmasi pesanan:\n\n[OK] Balas *YA* untuk memproses pesanan\n[X] Balas *BATAL* untuk membatalkan\n Balas *TAMBAH* jika ada yang kurang"
    
    def _handle_awaiting_payment_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        'Handle payment confirmation state.'
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
            
            lines = [
                "[OK] *PEMBAYARAN DIKONFIRMASI!*",
                "",
                f"Pesanan #{pesanan_id} sedang diproses",
                "Estimasi: 15-30 menit",
                "",
                "Terima kasih sudah memesan di Kedai Ayam Merdeka!",
                "Ditunggu orderan berikutnya ya kak!"
            ]
            return "\n".join(lines)
        
        # Priority 2: Check for payment-related keywords
        payment_keywords = ['bayar', 'transfer', 'tf', 'lunas', 'sudah bayar', 'udah bayar', 'sudah tf', 'udah tf']
        if any(keyword in msg_lower for keyword in payment_keywords):
            pesanan_id = state_data.get('id_pesanan')
            print(f"[DEBUG] Payment confirmed via keyword for order #{pesanan_id}")
            
            if pesanan_id:
                db.update_status_pesanan(pesanan_id, 'diproses')
            
            self.reset_user_state(user_id)
            
            lines = [
                "[OK] *PEMBAYARAN DIKONFIRMASI!*",
                "",
                f"Pesanan #{pesanan_id} sedang diproses",
                "Estimasi: 15-30 menit",
                "",
                "Terima kasih sudah memesan di Kedai Ayam Merdeka!",
                "Ditunggu orderan berikutnya ya kak!"
            ]
            return "\n".join(lines)
        
        # Check for payment info request
        elif intent == 'info_pembayaran' or 'cara' in msg_lower or 'gimana' in msg_lower or 'rekening' in msg_lower:
            return self._get_payment_info()
        
        # Check for cancellation
        elif intent == 'pembatalan' or intent == 'batalkan_pesanan' or 'batal' in msg_lower:
            pesanan_id = state_data.get('id_pesanan')
            if pesanan_id:
                db.update_status_pesanan(pesanan_id, 'batal')
            self.reset_user_state(user_id)
            return f"[X] Pesanan #{pesanan_id} dibatalkan.\n\nMau pesan lagi? Ketik 'menu' "
        
        # Default: remind about payment
        else:
            total = state_data.get('total', 0)
            detail = state_data.get('detail', '')
            pesanan_id = state_data.get('id_pesanan', '')
            
            lines = [
                "*MENUNGGU PEMBAYARAN*",
                "",
                f"Pesanan #{pesanan_id}",
                detail,
                f"Rp Total: Rp {total:,}",
                "",
                self._get_payment_info(),
                "",
                "> Kirim *'SUDAH BAYAR'* setelah transfer ya kak!"
            ]
            return "\n".join(lines)
    
    def _handle_modifying_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        'Handle order modification.'
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
        return f"[OK] Pesanan diubah!\n\nDetail: {detail}\nTotal: Rp {total:,}\n\nSilakan lanjutkan pembayaran."
    
    def _handle_asking_feedback_state(self, user_id: str, state: dict, intent: str, entities: dict, message: str) -> str:
        'Handle feedback collection after order completion.'
        state_data = state['data']
        pesanan_id = state_data.get('id_pesanan')
        
        # Check if user provided rating
        rating = None
        msg_lower = message.lower().strip()
        
        # Try to extract rating from intent or message
        if intent == 'rating':
            # Extract number from message
            numbers = re.findall(r'\d', message)
            if numbers:
                rating = int(numbers[0])
        
        # Direct number check
        if rating is None:
            if msg_lower in ['1', 'satu']:
                rating = 1
            elif msg_lower in ['2', 'dua']:
                rating = 2
            elif msg_lower in ['3', 'tiga']:
                rating = 3
            elif msg_lower in ['4', 'empat']:
                rating = 4
            elif msg_lower in ['5', 'lima']:
                rating = 5
        
        # If this is the first feedback message (asking for rating)
        if state_data.get('feedback_stage') == 'asking_rating':
            if rating and 1 <= rating <= 5:
                # Save rating and ask for additional feedback
                state_data['rating'] = rating
                state_data['feedback_stage'] = 'asking_comment'
                self.update_user_state(user_id, 'asking_feedback', state_data)
                
                # Thank user based on rating
                if rating >= 4:
                    thanks = "Makasih banyak kak! "
                elif rating >= 3:
                    thanks = "Terima kasih kak! "
                else:
                    thanks = "Terima kasih kak, kami akan berusaha lebih baik "
                
                lines = [thanks, "", "Ada saran atau komentar untuk kami?", 'Ketik pesan kakak atau balas "tidak ada" kalau sudah cukup']
                return "\n".join(lines)
            else:
                lines = [
                    "Maaf kak, format rating tidak valid",
                    "",
                    "*BERI RATING* (1-5)",
                    "- 1 = Sangat Kurang Puas",
                    "- 2 = Kurang Puas",
                    "- 3 = Cukup Puas",
                    "- 4 = Puas",
                    "- 5 = Sangat Puas",
                    "",
                    "Balas dengan angka 1-5 ya kak!"
                ]
                return "\n".join(lines)
        
        # If asking for comment
        elif state_data.get('feedback_stage') == 'asking_comment':
            saran = message if message.lower() not in ['tidak ada', 'sudah', 'cukup', 'selesai', 'ga ada', 'gak ada'] else None
            rating = state_data.get('rating')
            
            # Save feedback to database
            if rating:
                db.save_feedback(user_id, pesanan_id, rating, saran)
            
            self.reset_user_state(user_id)
            
            lines = [
                "*TERIMA KASIH ATAS FEEDBACKNYA!*",
                "",
                "Komentar kakak sangat berarti untuk perbaikan layanan kami.",
                "",
                "Mau pesan lagi? Ketik *menu* kapan saja ya kak!"
            ]
            return "\n".join(lines)
        
        # Default fallback
        self.reset_user_state(user_id)
        return "Terima kasih kak! Ditunggu orderan berikutnya ya "
    
    def request_feedback(self, user_id: str, pesanan_id: int) -> str:
        'Called by admin/API when order status is updated to selesai. Returns message to send to user asking for feedback'
        # Set state to asking feedback
        self.update_user_state(user_id, 'asking_feedback', {
            'id_pesanan': pesanan_id,
            'feedback_stage': 'asking_rating'
        })
        
        lines = [
            "*PESANAN SELESAI!*",
            "",
            "Terima kasih sudah memesan di Kedai Ayam Merdeka!",
            "",
            "*MOHON BERI RATING* (1-5)",
            "- 1 = Sangat Kurang Puas",
            "- 2 = Kurang Puas",
            "- 3 = Cukup Puas",
            "- 4 = Puas",
            "- 5 = Sangat Puas",
            "",
            "Balas dengan angka 1-5 ya kak!"
        ]
        return "\n".join(lines)
    
    def _get_response(self, intent: str) -> str:
        'Get random response for intent from JSON.'
        for intent_data in nlu.intents["intents"]:
            if intent_data["tag"] == intent:
                if not intent_data["responses"]:
                    return "Maaf, saya tidak mengerti."
                return random.choice(intent_data["responses"])
        return "Maaf, saya tidak mengerti."
    
    def _format_menu_list(self) -> str:
        'Format menu list with categories.'
        menus = db.get_all_menu()
        if not menus:
            return "Menu belum tersedia."
        
        categories = {}
        for menu in menus:
            cat = menu.get('kategori', 'Lainnya') or 'Lainnya'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(menu)
        
        menu_text = " *MENU KEDAI AYAM MERDEKA*\n"
        
        for cat, items in categories.items():
            menu_text += f"\n*{cat}:*\n"
            for item in items:
                menu_text += f"- {item['nama_menu']} - Rp {item['harga']:,}\n"
        
        return menu_text
    
    def _get_payment_info(self) -> str:
        'Return payment information.'
        lines = [
            "*METODE PEMBAYARAN*",
            "",
            "Bank BCA: 1234567890",
            "OVO/GoPay: 081234567890",
            "a.n. Kedai Ayam Merdeka"
        ]
        return "\n".join(lines)
    
    def _get_time_greeting(self) -> str:
        'Get greeting based on current time.'
        hour = datetime.now().hour
        
        if 5 <= hour < 11:
            greeting = "Selamat pagi"
        elif 11 <= hour < 15:
            greeting = "Selamat siang"
        elif 15 <= hour < 18:
            greeting = "Selamat sore"
        else:
            greeting = "Selamat malam"
        
        return f"{greeting} kak! Selamat datang di Kedai Ayam Merdeka "

dialog_manager = DialogManager()
