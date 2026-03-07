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
    let confirmMessage = `Ubah status pesanan #${orderId} menjadi "${newStatus}"?`;
    
    if (newStatus === 'selesai') {
        confirmMessage += '\n\n✉️ Notifikasi feedback akan dikirim ke pelanggan.';
    }
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    axios.put(`/api/pesanan/${orderId}/status`, { status: newStatus, send_notification: true })
        .then(response => {
            let message = 'Status pesanan berhasil diubah!';
            if (response.data.feedback_requested) {
                message += '\n\n✉️ Permintaan feedback telah dikirim ke pelanggan.';
            }
            alert(message);
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
    loadAnalytics(); // Load analytics on page load
});

// ==================== ANALYTICS FUNCTIONS ====================

function loadAnalytics() {
    loadChatStats();
    loadFeedbackStats();
    loadFeedbackDetails();
}

function loadChatStats() {
    axios.get('/api/analytics/chat')
        .then(response => {
            const data = response.data;
            
            // Update summary cards
            document.getElementById('totalInteractions').textContent = data.total_interactions || 0;
            document.getElementById('avgConfidence').textContent = data.average_confidence ? 
                (data.average_confidence * 100).toFixed(1) + '%' : '0%';
            
            // Update intent distribution table
            const intentTbody = document.querySelector('#intentDistributionTable tbody');
            intentTbody.innerHTML = '';
            if (data.intent_distribution) {
                const total = data.total_interactions || 1;
                data.intent_distribution.forEach(item => {
                    const percentage = ((item.count / total) * 100).toFixed(1);
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.intent_terdeteksi}</td>
                        <td>${item.count}</td>
                        <td>${percentage}%</td>
                    `;
                    intentTbody.appendChild(row);
                });
            }
            
            // Update confidence distribution table
            const confTbody = document.querySelector('#confidenceDistributionTable tbody');
            confTbody.innerHTML = '';
            if (data.confidence_distribution) {
                data.confidence_distribution.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.confidence_level}</td>
                        <td>${item.count}</td>
                    `;
                    confTbody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Error loading analytics:', error);
        });
}

function loadFeedbackStats() {
    axios.get('/api/feedback')
        .then(response => {
            const data = response.data;
            document.getElementById('totalFeedback').textContent = data.total_feedback || 0;
            document.getElementById('avgRating').textContent = data.average_rating ? 
                data.average_rating + ' / 5.0 ⭐' : '-';
        })
        .catch(error => {
            console.error('Error loading feedback stats:', error);
        });
}

function loadFeedbackDetails() {
    axios.get('/api/feedback?details=true')
        .then(response => {
            const data = response.data;
            // Display rating distribution in table
            const tbody = document.querySelector('#ratingDistributionTable tbody');
            if (tbody && data.rating_distribution) {
                tbody.innerHTML = '';
                const total = data.total_feedback || 1;
                for (let i = 5; i >= 1; i--) {
                    const count = data.rating_distribution[i] || 0;
                    const percentage = ((count / total) * 100).toFixed(1);
                    const stars = '⭐'.repeat(i);
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${stars}</td>
                        <td>${count}</td>
                        <td>${percentage}%</td>
                    `;
                    tbody.appendChild(row);
                }
            }
        })
        .catch(error => {
            console.error('Error loading feedback details:', error);
        });
}

function exportFeedback() {
    axios.get('/api/feedback?details=true')
        .then(response => {
            const data = response.data;
            
            // Create CSV content
            let csv = 'Rating,Jumlah,Pleasantage\\n';
            const total = data.total_feedback || 1;
            for (let i = 5; i >= 1; i--) {
                const count = data.rating_distribution[i] || 0;
                const percentage = ((count / total) * 100).toFixed(1);
                csv += `${i},${count},${percentage}%\\n`;
            }
            csv += `\\nTotal Feedback,${data.total_feedback}\\n`;
            csv += `Average Rating,${data.average_rating}\\n`;
            csv += `Positive (4-5),${data.positive}\\n`;
            csv += `Neutral (3),${data.neutral}\\n`;
            csv += `Negative (1-2),${data.negative}\\n`;
            
            // Download
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'feedback_evaluasi.csv';
            a.click();
        })
        .catch(error => {
            console.error('Error exporting feedback:', error);
        });
}

function loadChatLogs() {
    axios.get('/api/analytics/chat-logs?limit=50')
        .then(response => {
            const logs = response.data;
            const tbody = document.querySelector('#chatLogsTable tbody');
            tbody.innerHTML = '';
            
            logs.forEach(log => {
                const row = document.createElement('tr');
                const waktu = new Date(log.waktu_interaksi).toLocaleString('id-ID');
                const confidence = log.confidence_score ? (log.confidence_score * 100).toFixed(1) + '%' : '-';
                
                row.innerHTML = `
                    <td>${waktu}</td>
                    <td>${log.nama_pelanggan}</td>
                    <td title="${log.pesan_masuk}">${log.pesan_masuk}</td>
                    <td>${log.intent_terdeteksi}</td>
                    <td>${confidence}</td>
                    <td title="${log.pesan_keluar}">${log.pesan_keluar}</td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading chat logs:', error);
        });
}

function exportChatLogs() {
    axios.get('/api/analytics/chat-logs?limit=10000')
        .then(response => {
            const logs = response.data;
            
            // Convert to CSV
            let csv = 'Waktu,ID Pelanggan,Nama,Pesan Masuk,Intent,Confidence,Entities,Pesan Keluar\\n';
            logs.forEach(log => {
                csv += `"${log.waktu_interaksi}","${log.id_pelanggan}","${log.nama_pelanggan}","${log.pesan_masuk}","${log.intent_terdeteksi}","${log.confidence_score}","${log.entities_extracted}","${log.pesan_keluar}"\\n`;
            });
            
            // Download
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'chat_logs_evaluasi.csv';
            a.click();
        })
        .catch(error => {
            console.error('Error exporting chat logs:', error);
        });
}

function exportConfusionMatrix() {
    axios.get('/api/analytics/confusion-matrix')
        .then(response => {
            const data = response.data;
            
            // Convert to CSV format for confusion matrix
            let csv = 'ID Log,Pesan Masuk,Intent Terdeteksi (Predicted),Confidence,Intent Actual (Untuk Evaluasi Manual)\\n';
            data.forEach(item => {
                csv += `"${item.id_log}","${item.pesan_masuk}","${item.intent_terdeteksi}","${item.confidence_score}",""\\n`;
            });
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'confusion_matrix_data.csv';
            a.click();
        })
        .catch(error => {
            console.error('Error exporting confusion matrix:', error);
        });
}
