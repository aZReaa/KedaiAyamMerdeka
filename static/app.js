function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(tabId).classList.add('active');
    event.target.classList.add('active');
}

function loadMenu() {
    axios.get('/api/menu')
        .then(response => {
            const tbody = document.getElementById('menuTableBody');
            tbody.innerHTML = '';
            
            response.data.forEach(menu => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${menu.id_menu}</td>
                    <td>${menu.nama_menu}</td>
                    <td>Rp ${parseInt(menu.harga).toLocaleString()}</td>
                    <td>${menu.kategori || '-'}</td>
                    <td>${menu.ketersediaan ? '✅' : '❌'}</td>
                    <td>
                        <button class="delete-btn" onclick="deleteMenu(${menu.id_menu})">Hapus</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading menu:', error);
            alert('Gagal memuat menu');
        });
}

document.getElementById('menuForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const nama_menu = document.getElementById('nama_menu').value;
    const harga = document.getElementById('harga').value;
    const kategori = document.getElementById('kategori').value;
    const ketersediaan = document.getElementById('ketersediaan').checked;
    
    axios.post('/api/menu', {
        nama_menu,
        harga,
        kategori,
        ketersediaan
    })
    .then(response => {
        alert('Menu berhasil ditambahkan!');
        this.reset();
        loadMenu();
    })
    .catch(error => {
        console.error('Error adding menu:', error);
        alert('Gagal menambahkan menu');
    });
});

function deleteMenu(menuId) {
    if (confirm('Yakin ingin menghapus menu ini?')) {
        axios.delete(`/api/menu/${menuId}`)
            .then(response => {
                alert('Menu berhasil dihapus!');
                loadMenu();
            })
            .catch(error => {
                console.error('Error deleting menu:', error);
                alert('Gagal menghapus menu');
            });
    }
}

function loadAllPesanan() {
    const statusFilter = document.getElementById('statusFilter').value;
    
    let url = '/api/pesanan';
    if (statusFilter) {
        url += `?status=${statusFilter}`;
    }
    
    axios.get(url)
        .then(response => {
            displayPesanan(response.data);
        })
        .catch(error => {
            console.error('Error loading pesanan:', error);
            alert('Gagal memuat pesanan');
        });
}

function loadPesananByCustomer() {
    const id_pelanggan = document.getElementById('pelanggan_id').value;
    
    if (!id_pelanggan) {
        alert('Masukkan No. WA pelanggan');
        return;
    }
    
    axios.get(`/api/pesanan?id_pelanggan=${id_pelanggan}`)
        .then(response => {
            displayPesanan(response.data);
        })
        .catch(error => {
            console.error('Error loading pesanan:', error);
            alert('Gagal memuat pesanan');
        });
}

function displayPesanan(data) {
    const tbody = document.getElementById('pesananTableBody');
    tbody.innerHTML = '';
    
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">Tidak ada pesanan ditemukan</td></tr>';
        return;
    }
    
    data.forEach(pesanan => {
        const row = document.createElement('tr');
        const waktu = new Date(pesanan.waktu_pesan).toLocaleString('id-ID');
        const namaPelanggan = pesanan.nama_pelanggan || 'Unknown';
        
        // Status badge
        const statusClass = `status-${pesanan.status}`;
        const statusBadge = `<span class="status-badge ${statusClass}">${pesanan.status.toUpperCase()}</span>`;
        
        // Action buttons
        let actionButtons = '';
        if (pesanan.status === 'dipesan') {
            actionButtons = `
                <button class="action-btn success" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'diproses')">✓ Proses</button>
                <button class="action-btn danger" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'batal')">✗ Batal</button>
            `;
        } else if (pesanan.status === 'diproses') {
            actionButtons = `
                <button class="action-btn success" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'selesai')">✓ Selesai</button>
            `;
        }
        
        row.innerHTML = `
            <td>${pesanan.id_pesanan}</td>
            <td>${namaPelanggan}</td>
            <td>${pesanan.id_pelanggan}</td>
            <td>${pesanan.detail_pesanan}</td>
            <td>Rp ${parseInt(pesanan.total_harga).toLocaleString()}</td>
            <td>${statusBadge}</td>
            <td>${waktu}</td>
            <td>${actionButtons}</td>
        `;
        tbody.appendChild(row);
    });
}

function updateOrderStatus(orderId, newStatus) {
    if (!confirm(`Ubah status pesanan #${orderId} menjadi "${newStatus}"?`)) {
        return;
    }
    
    axios.put(`/api/pesanan/${orderId}/status`, { status: newStatus })
        .then(response => {
            alert('Status pesanan berhasil diubah!');
            loadAllPesanan(); // Refresh the list
        })
        .catch(error => {
            console.error('Error updating status:', error);
            alert('Gagal mengubah status pesanan');
        });
}

// Legacy function for backward compatibility
function loadPesanan() {
    loadPesananByCustomer();
}


function addChatMessage(message, isUser = false) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user' : 'bot'}`;
    messageDiv.textContent = message;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById('chatMessage');
    const message = input.value.trim();
    
    if (!message) return;
    
    addChatMessage(message, true);
    input.value = '';
    
    axios.post('/chat', {
        user_id: 'test_user',
        message: message
    })
    .then(response => {
        addChatMessage(response.data.response, false);
    })
    .catch(error => {
        console.error('Error sending message:', error);
        addChatMessage('Maaf, terjadi kesalahan. Silakan coba lagi.', false);
    });
}

document.getElementById('chatMessage').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

function initDatabase() {
    if (confirm('Initialize database with sample data? This will create tables and add sample menus.')) {
        axios.post('/api/init_db')
            .then(response => {
                alert(response.data.message);
                loadMenu();
            })
            .catch(error => {
                console.error('Error initializing database:', error);
                alert('Gagal menginisialisasi database');
            });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadMenu();
    loadAllPesanan(); // Auto-load all orders on page load
    addChatMessage('Halo! Selamat datang di Chatbot Kedai Ayam Merdeka. Ketik pesan untuk memulai percakapan!', false);
});
