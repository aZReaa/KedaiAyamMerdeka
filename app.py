from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from functools import wraps
from config import Config
import os
import json
from decimal import Decimal
from datetime import datetime, date

print(f"[BOOT] app.py starting... (PID: {os.getpid()})")

# Lazy imports - only load heavy modules when needed
from database import db
from dialog_manager import dialog_manager
import requests
import json

print(f"[BOOT] All modules imported successfully!")

app = Flask(__name__)
app.config.from_object(Config)

@app.teardown_appcontext
def close_database_connection(_error=None):
    db.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

print(f"[BOOT] Flask app created and ready to serve!")

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
            
            # Generate response from dialog manager (with nama_pelanggan for logging)
            response_text = dialog_manager.generate_response(from_number, text, profile_name)
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
    user_name = data.get('user_name', 'Test User')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    db.insert_or_update_pelanggan(user_id, user_name)
    response = dialog_manager.generate_response(user_id, message, user_name)
    
    return jsonify({'response': response})

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = db.verify_admin_login(username, password)
        if admin:
            session['admin_id'] = admin['id_admin']
            session['admin_username'] = admin['username']
            session['admin_nama'] = admin['nama']
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='Username atau password salah!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

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
    cursor = db.get_cursor()
    if not cursor:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        query = "DELETE FROM menu WHERE id_menu = %s"
        cursor.execute(query, (menu_id,))
        db.commit()
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
    send_notification = data.get('send_notification', True)  # Option to notify customer
    
    if not new_status:
        return jsonify({'error': 'status is required'}), 400
    
    if new_status not in ['dipesan', 'diproses', 'selesai', 'batal']:
        return jsonify({'error': 'Invalid status'}), 400
    
    # Get order info before updating
    pesanan = db.get_pesanan_by_id(pesanan_id)
    
    success = db.update_status_pesanan(pesanan_id, new_status)
    
    if success:
        response_data = {'success': True, 'message': f'Status updated to {new_status}'}
        
        # If status changed to 'selesai' and notification enabled, trigger feedback request
        if new_status == 'selesai' and send_notification and pesanan:
            id_pelanggan = pesanan.get('id_pelanggan')
            if id_pelanggan:
                feedback_message = dialog_manager.request_feedback(id_pelanggan, pesanan_id)
                # Send notification to customer
                notification_sent = send_telegram_message(id_pelanggan, feedback_message)
                response_data['notification_sent'] = notification_sent
                response_data['feedback_requested'] = True
        
        return jsonify(response_data)
    else:   
        return jsonify({'error': 'Failed to update status'}), 500

@app.route('/api/pelanggan', methods=['GET'])
def api_pelanggan():
    pelanggan = db.get_all_pelanggan()
    return jsonify(pelanggan)


@app.route('/api/system/db-info', methods=['GET'])
def api_db_info():
    return jsonify({
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'database': Config.DB_NAME
    })


@app.route('/api/system/menu-debug', methods=['GET'])
def api_menu_debug():
    snapshot = db.get_menu_debug_snapshot()
    snapshot['config'] = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'database': Config.DB_NAME
    }
    return jsonify(snapshot)


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
        
        # Create default admin
        db.create_default_admin()
        
        return jsonify({'success': True, 'message': 'Database initialized with sample data and admin (admin/admin123)'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== CHAT ANALYTICS API ====================

@app.route('/api/analytics/chat', methods=['GET'])
def get_chat_analytics():
    """Get chat analytics for evaluation (Bab 4)"""
    try:
        from datetime import datetime, timedelta
        
        # Optional date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        analytics = db.get_chat_analytics(start_date, end_date)
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/chat-logs', methods=['GET'])
def get_chat_logs():
    """Get raw chat logs for manual evaluation"""
    try:
        limit = request.args.get('limit', 1000, type=int)
        logs = db.get_chat_logs_for_evaluation(limit)
        
        # Convert datetime to string for JSON serialization
        for log in logs:
            if log.get('waktu_interaksi'):
                log['waktu_interaksi'] = log['waktu_interaksi'].isoformat()
        
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/confusion-matrix', methods=['GET'])
def get_confusion_matrix_data():
    """Get data for confusion matrix (predicted vs actual)"""
    try:
        data = db.get_intent_confusion_matrix_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['GET', 'POST'])
def handle_feedback():
    """Handle feedback submission and retrieval"""
    if request.method == 'POST':
        try:
            data = request.json
            success = db.save_feedback(
                id_pelanggan=data.get('id_pelanggan'),
                id_pesanan=data.get('id_pesanan'),
                rating=data.get('rating'),
                saran=data.get('saran')
            )
            if success:
                return jsonify({'success': True, 'message': 'Feedback saved'})
            else:
                return jsonify({'error': 'Failed to save feedback'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        # GET - get feedback stats
        try:
            show_details = request.args.get('details', 'false').lower() == 'true'
            stats = db.get_feedback_stats()
            
            if show_details:
                # Add rating distribution
                rating_dist = db.get_feedback_rating_distribution()
                stats['rating_distribution'] = rating_dist
            
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[BOOT] Starting Flask on port {port}...")
    app.run(debug=False, host='0.0.0.0', port=port)
