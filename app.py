from flask import Flask, request, jsonify, render_template
from config import Config
from database import db
from dialog_manager import dialog_manager
import requests
import json

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/')
def index():
    return 'Chatbot Kedai Ayam Merdeka is running!'

@app.route('/test-config')
def test_config():
    """Test endpoint untuk cek konfigurasi Telegram"""
    return jsonify({
        'telegram_token_set': bool(Config.TELEGRAM_BOT_TOKEN),
        'telegram_api_url': Config.TELEGRAM_API_URL
    })

@app.route('/test-webhook', methods=['POST'])
def test_webhook():
    """Test endpoint untuk simulasi webhook Telegram"""
    data = request.json
    print(f"\n{'='*50}")
    print(f"🧪 TEST WEBHOOK DITERIMA")
    print(f"{'='*50}")
    print(f"Data: {json.dumps(data, indent=2)}")
    return jsonify({'status': 'test received', 'data': data})

# ==================== WEBHOOK TELEGRAM ====================

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Menerima pesan masuk dari Telegram
    """
    try:
        data = request.json
        print(f"\n{'='*50}")
        print(f"📩 WEBHOOK DITERIMA")
        print(f"{'='*50}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        if not data:
            print("❌ Data kosong!")
            return jsonify({'status': 'no data'}), 200
            
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "")
            profile_name = message["from"].get("first_name", "Pelanggan")
            
            # Convert chat_id to string to match previous from_number logic
            from_number = str(chat_id)
            
            print(f"\n👤 Dari: {profile_name} ({from_number})")
            print(f"💬 Pesan: {text}")
            
            # Register/Update customer
            db.insert_or_update_pelanggan(from_number, profile_name)
            
            # Generate response from dialog manager
            response_text = dialog_manager.generate_response(from_number, text)
            print(f"\n🤖 Balasan: {response_text[:100]}...")
            
            # Send back to Telegram
            success = send_telegram_message(from_number, response_text)
            
            return jsonify({'status': 'success', 'sent': success}), 200
            
        return jsonify({'status': 'no message processing implementation matches'}), 200
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 200


def send_telegram_message(chat_id, text):
    """
    Mengirim pesan balik ke Telegram menggunakan Telegram Bot API
    """
    print(f"\n=== MENGIRIM PESAN ===")
    print(f"Token: {'SET' if Config.TELEGRAM_BOT_TOKEN else 'KOSONG'}")
    print(f"API URL: {Config.TELEGRAM_API_URL}")
    print(f"To: {chat_id}")
    print(f"Text: {text[:50]}...")
    
    if not Config.TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN belum dikonfigurasi!")
        return False
        
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    
    try:
        print(f"\nMengirim ke: {Config.TELEGRAM_API_URL}")
        response = requests.post(Config.TELEGRAM_API_URL, json=payload)
        response_data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response_data, indent=2)}")
        
        if response.status_code == 200 and response_data.get("ok"):
            print(f"✅ Pesan berhasil dikirim ke {chat_id}")
            return True
        else:
            print(f"❌ Error sending message: {response_data}")
            return False
    except Exception as e:
        print(f"❌ Exception while sending message: {e}")
        import traceback
        traceback.print_exc()
        return False


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id', 'default')
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    db.insert_or_update_pelanggan(user_id, "Test User")
    response = dialog_manager.generate_response(user_id, message)
    
    return jsonify({'response': response})

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/menu', methods=['GET', 'POST'])
def api_menu():
    if request.method == 'POST':
        data = request.json
        nama_menu = data.get('nama_menu')
        harga = data.get('harga')
        kategori = data.get('kategori')
        ketersediaan = data.get('ketersediaan', True)
        
        if not nama_menu or not harga:
            return jsonify({'error': 'nama_menu and harga are required'}), 400
        
        menu_id = db.insert_menu(nama_menu, harga, kategori, ketersediaan)
        
        if menu_id:
            return jsonify({'success': True, 'menu_id': menu_id}), 201
        else:
            return jsonify({'error': 'Failed to create menu'}), 500
    
    menus = db.get_all_menu()
    return jsonify(menus)

@app.route('/api/menu/<int:menu_id>', methods=['DELETE'])
def delete_menu(menu_id):
    cursor = db.connection.cursor()
    try:
        query = "DELETE FROM menu WHERE id_menu = %s"
        cursor.execute(query, (menu_id,))
        db.connection.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()

@app.route('/api/pesanan', methods=['GET'])
def api_pesanan():
    id_pelanggan = request.args.get('id_pelanggan')
    status_filter = request.args.get('status')
    
    if id_pelanggan:
        # Get orders for specific customer
        pesanan = db.get_pesanan_by_pelanggan(id_pelanggan)
    else:
        # Get all orders with optional status filter
        pesanan = db.get_all_pesanan(status_filter=status_filter)
    
    return jsonify(pesanan)

@app.route('/api/pesanan/<int:pesanan_id>/status', methods=['PUT'])
def update_pesanan_status(pesanan_id):
    data = request.json
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'error': 'status is required'}), 400
    
    if new_status not in ['dipesan', 'diproses', 'selesai', 'batal']:
        return jsonify({'error': 'Invalid status'}), 400
    
    success = db.update_status_pesanan(pesanan_id, new_status)
    
    if success:
        return jsonify({'success': True, 'message': f'Status updated to {new_status}'})
    else:
        return jsonify({'error': 'Failed to update status'}), 500

@app.route('/api/pelanggan', methods=['GET'])
def api_pelanggan():
    pelanggan = db.get_all_pelanggan()
    return jsonify(pelanggan)


@app.route('/api/init_db', methods=['POST'])
def init_db():
    try:
        db.create_database_and_tables()
        
        sample_menus = [
            ('Ayam Geprek', 15000, 'Ayam', True),
            ('Ayam Bakar', 18000, 'Ayam', True),
            ('Ayam Goreng', 15000, 'Ayam', True),
            ('Nasi', 5000, 'Lauk', True),
            ('Es Teh Manis', 5000, 'Minuman', True),
            ('Es Jeruk', 6000, 'Minuman', True),
            ('Es Campur', 12000, 'Minuman', True),
            ('Es Teler', 10000, 'Minuman', True),
            ('Tahu Crispy', 3000, 'Lauk', True),
            ('Tempe Crispy', 3000, 'Lauk', True)
        ]
        
        for menu in sample_menus:
            db.insert_menu(*menu)
        
        return jsonify({'success': True, 'message': 'Database initialized with sample data'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
