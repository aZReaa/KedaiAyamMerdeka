function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach((content) => {
        content.classList.toggle('active', content.id === tabId);
    });

    document.querySelectorAll('.tab-btn').forEach((button) => {
        button.classList.toggle('active', button.dataset.tab === tabId);
    });
}

function bindTabButtons() {
    document.querySelectorAll('.tab-btn').forEach((button) => {
        button.addEventListener('click', () => showTab(button.dataset.tab));
    });
}

function formatCurrency(value) {
    const amount = Number(value || 0);
    return `Rp ${amount.toLocaleString('id-ID')}`;
}

function formatDateTime(value) {
    if (!value) {
        return '-';
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString('id-ID');
}

function updateSyncStamp(label) {
    const stamp = `${label} | ${new Date().toLocaleTimeString('id-ID')}`;
    const globalNode = document.getElementById('globalLastUpdated');
    if (globalNode) {
        globalNode.textContent = stamp;
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) {
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    window.setTimeout(() => {
        toast.remove();
    }, 3000);
}

function setTableEmptyState(tbodyId, colspan, message) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) {
        return;
    }

    tbody.innerHTML = `<tr class="empty-state"><td colspan="${colspan}">${message}</td></tr>`;
}

function updateMenuSummary(menuItems) {
    const total = menuItems.length;
    const available = menuItems.filter((item) => item.ketersediaan).length;
    const unavailable = total - available;

    document.getElementById('menuCount').textContent = total;
    document.getElementById('availableMenuCount').textContent = available;
    document.getElementById('summaryMenuTotal').textContent = total;
    document.getElementById('summaryMenuAvailable').textContent = available;
    document.getElementById('summaryMenuUnavailable').textContent = unavailable;
    document.getElementById('menuStatusText').textContent = `${total} item dimuat`;
}

function updateOrderSummary(orderItems) {
    const counts = {
        dipesan: 0,
        diproses: 0,
        selesai: 0,
        batal: 0
    };

    orderItems.forEach((item) => {
        if (counts[item.status] !== undefined) {
            counts[item.status] += 1;
        }
    });

    const total = orderItems.length;
    const active = counts.dipesan + counts.diproses;

    document.getElementById('orderCount').textContent = total;
    document.getElementById('completedOrderCount').textContent = counts.selesai;
    document.getElementById('activeOrdersCount').textContent = active;
    document.getElementById('orderPendingCount').textContent = counts.dipesan;
    document.getElementById('orderProcessingCount').textContent = counts.diproses;
    document.getElementById('orderDoneCount').textContent = counts.selesai;
    document.getElementById('orderCancelledCount').textContent = counts.batal;
    document.getElementById('orderStatusText').textContent = `${total} pesanan dimuat`;
}

function loadMenu() {
    axios.get('/api/menu')
        .then((response) => {
            const tbody = document.getElementById('menuTableBody');
            const menuItems = response.data || [];
            tbody.innerHTML = '';

            if (menuItems.length === 0) {
                setTableEmptyState('menuTableBody', 6, 'Belum ada data menu.');
                updateMenuSummary([]);
                updateSyncStamp('Menu kosong');
                return;
            }

            menuItems.forEach((menu) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>#${menu.id_menu}</td>
                    <td>${menu.nama_menu}</td>
                    <td>${formatCurrency(menu.harga)}</td>
                    <td>${menu.kategori || '-'}</td>
                    <td><span class="status-badge ${menu.ketersediaan ? 'status-selesai' : 'status-batal'}">${menu.ketersediaan ? 'Tersedia' : 'Nonaktif'}</span></td>
                    <td>
                        <button class="delete-btn" type="button" onclick="deleteMenu(${menu.id_menu})">Hapus</button>
                    </td>
                `;
                tbody.appendChild(row);
            });

            updateMenuSummary(menuItems);
            updateSyncStamp('Menu diperbarui');
        })
        .catch((error) => {
            console.error('Error loading menu:', error);
            document.getElementById('menuStatusText').textContent = 'Gagal memuat menu';
            showToast('Gagal memuat menu.', 'error');
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
        .then(() => {
            showToast('Menu berhasil ditambahkan.', 'success');
            this.reset();
            document.getElementById('ketersediaan').checked = true;
            loadMenu();
        })
        .catch((error) => {
            console.error('Error adding menu:', error);
            showToast('Gagal menambahkan menu.', 'error');
        });
});

function deleteMenu(menuId) {
    if (!confirm('Yakin ingin menghapus menu ini?')) {
        return;
    }

    axios.delete(`/api/menu/${menuId}`)
        .then(() => {
            showToast(`Menu #${menuId} dihapus.`, 'success');
            loadMenu();
        })
        .catch((error) => {
            console.error('Error deleting menu:', error);
            showToast('Gagal menghapus menu.', 'error');
        });
}

function loadAllPesanan() {
    const statusFilter = document.getElementById('statusFilter').value;
    let url = '/api/pesanan';

    if (statusFilter) {
        url += `?status=${encodeURIComponent(statusFilter)}`;
    }

    axios.get(url)
        .then((response) => {
            displayPesanan(response.data || []);
            updateSyncStamp('Pesanan diperbarui');
        })
        .catch((error) => {
            console.error('Error loading pesanan:', error);
            document.getElementById('orderStatusText').textContent = 'Gagal memuat pesanan';
            showToast('Gagal memuat pesanan.', 'error');
        });
}

function loadPesananByCustomer() {
    const pelangganId = document.getElementById('pelanggan_id').value.trim();

    if (!pelangganId) {
        showToast('Masukkan ID pelanggan terlebih dahulu.', 'info');
        return;
    }

    axios.get(`/api/pesanan?id_pelanggan=${encodeURIComponent(pelangganId)}`)
        .then((response) => {
            displayPesanan(response.data || []);
            updateSyncStamp(`Pesanan pelanggan ${pelangganId}`);
        })
        .catch((error) => {
            console.error('Error loading pesanan:', error);
            showToast('Gagal memuat pesanan pelanggan.', 'error');
        });
}

function displayPesanan(data) {
    const tbody = document.getElementById('pesananTableBody');
    tbody.innerHTML = '';

    if (data.length === 0) {
        setTableEmptyState('pesananTableBody', 8, 'Tidak ada pesanan yang cocok dengan filter saat ini.');
        updateOrderSummary([]);
        return;
    }

    data.forEach((pesanan) => {
        const row = document.createElement('tr');
        const namaPelanggan = pesanan.nama_pelanggan || 'Pelanggan';
        const statusClass = `status-${pesanan.status}`;

        let actionButtons = '<span class="muted-meta">Tidak ada aksi</span>';
        if (pesanan.status === 'dipesan') {
            actionButtons = `
                <div class="action-stack">
                    <button class="action-btn success" type="button" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'diproses')">Proses</button>
                    <button class="action-btn danger" type="button" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'batal')">Batalkan</button>
                </div>
            `;
        } else if (pesanan.status === 'diproses') {
            actionButtons = `
                <div class="action-stack">
                    <button class="action-btn success" type="button" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'selesai')">Tandai selesai</button>
                </div>
            `;
        }

        row.innerHTML = `
            <td>#${pesanan.id_pesanan}</td>
            <td>${namaPelanggan}</td>
            <td>${pesanan.id_pelanggan || '-'}</td>
            <td>${pesanan.detail_pesanan || '-'}</td>
            <td>${formatCurrency(pesanan.total_harga)}</td>
            <td><span class="status-badge ${statusClass}">${pesanan.status}</span></td>
            <td>${formatDateTime(pesanan.waktu_pesan)}</td>
            <td>${actionButtons}</td>
        `;
        tbody.appendChild(row);
    });

    updateOrderSummary(data);
}

function updateOrderStatus(orderId, newStatus) {
    let confirmMessage = `Ubah status pesanan #${orderId} menjadi "${newStatus}"?`;

    if (newStatus === 'selesai') {
        confirmMessage += '\n\nPermintaan feedback akan dikirim ke pelanggan.';
    }

    if (!confirm(confirmMessage)) {
        return;
    }

    axios.put(`/api/pesanan/${orderId}/status`, { status: newStatus, send_notification: true })
        .then((response) => {
            let message = `Status pesanan #${orderId} diperbarui.`;
            if (response.data.feedback_requested) {
                message += ' Permintaan feedback juga dikirim.';
            }
            showToast(message, 'success');
            loadAllPesanan();
        })
        .catch((error) => {
            console.error('Error updating status:', error);
            showToast('Gagal mengubah status pesanan.', 'error');
        });
}

function loadPesanan() {
    loadPesananByCustomer();
}

function initDatabase() {
    if (!confirm('Initialize database dengan sample data?')) {
        return;
    }

    axios.post('/api/init_db')
        .then((response) => {
            showToast(response.data.message || 'Database berhasil diinisialisasi.', 'success');
            loadMenu();
        })
        .catch((error) => {
            console.error('Error initializing database:', error);
            showToast('Gagal menginisialisasi database.', 'error');
        });
}

function loadAnalytics() {
    loadChatStats();
    loadFeedbackStats();
    loadFeedbackDetails();
    loadChatLogs();
}

function loadChatStats() {
    axios.get('/api/analytics/chat')
        .then((response) => {
            const data = response.data || {};

            document.getElementById('totalInteractions').textContent = data.total_interactions || 0;
            document.getElementById('avgConfidence').textContent = data.average_confidence ?
                `${(data.average_confidence * 100).toFixed(1)}%` : '0%';

            const intentTbody = document.querySelector('#intentDistributionTable tbody');
            intentTbody.innerHTML = '';
            if (data.intent_distribution && data.intent_distribution.length > 0) {
                const total = data.total_interactions || 1;
                data.intent_distribution.forEach((item) => {
                    const percentage = ((item.count / total) * 100).toFixed(1);
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.intent_terdeteksi}</td>
                        <td>${item.count}</td>
                        <td>${percentage}%</td>
                    `;
                    intentTbody.appendChild(row);
                });
            } else {
                intentTbody.innerHTML = '<tr class="empty-state"><td colspan="3">Belum ada data intent.</td></tr>';
            }

            const confTbody = document.querySelector('#confidenceDistributionTable tbody');
            confTbody.innerHTML = '';
            if (data.confidence_distribution && data.confidence_distribution.length > 0) {
                data.confidence_distribution.forEach((item) => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.confidence_level}</td>
                        <td>${item.count}</td>
                    `;
                    confTbody.appendChild(row);
                });
            } else {
                confTbody.innerHTML = '<tr class="empty-state"><td colspan="2">Belum ada data confidence.</td></tr>';
            }
        })
        .catch((error) => {
            console.error('Error loading analytics:', error);
            showToast('Gagal memuat analytics chat.', 'error');
        });
}

function loadFeedbackStats() {
    axios.get('/api/feedback')
        .then((response) => {
            const data = response.data || {};
            const average = data.average_rating ? `${data.average_rating} / 5` : '-';

            document.getElementById('totalFeedback').textContent = data.total_feedback || 0;
            document.getElementById('avgRating').textContent = average;
            document.getElementById('heroAvgRating').textContent = average;
        })
        .catch((error) => {
            console.error('Error loading feedback stats:', error);
            showToast('Gagal memuat statistik feedback.', 'error');
        });
}

function loadFeedbackDetails() {
    axios.get('/api/feedback?details=true')
        .then((response) => {
            const data = response.data || {};
            const tbody = document.querySelector('#ratingDistributionTable tbody');
            tbody.innerHTML = '';

            if (!data.rating_distribution) {
                tbody.innerHTML = '<tr class="empty-state"><td colspan="3">Belum ada data feedback.</td></tr>';
                return;
            }

            const total = data.total_feedback || 1;
            for (let i = 5; i >= 1; i -= 1) {
                const count = data.rating_distribution[i] || 0;
                const percentage = ((count / total) * 100).toFixed(1);
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${i} / 5</td>
                    <td>${count}</td>
                    <td>${percentage}%</td>
                `;
                tbody.appendChild(row);
            }
        })
        .catch((error) => {
            console.error('Error loading feedback details:', error);
            showToast('Gagal memuat distribusi feedback.', 'error');
        });
}

function loadChatLogs() {
    axios.get('/api/analytics/chat-logs?limit=50')
        .then((response) => {
            const logs = response.data || [];
            const tbody = document.querySelector('#chatLogsTable tbody');
            tbody.innerHTML = '';

            if (logs.length === 0) {
                tbody.innerHTML = '<tr class="empty-state"><td colspan="6">Belum ada chat log.</td></tr>';
                return;
            }

            logs.forEach((log) => {
                const row = document.createElement('tr');
                const confidence = log.confidence_score ? `${(log.confidence_score * 100).toFixed(1)}%` : '-';

                row.innerHTML = `
                    <td>${formatDateTime(log.waktu_interaksi)}</td>
                    <td>${log.nama_pelanggan || '-'}</td>
                    <td title="${log.pesan_masuk || ''}">${log.pesan_masuk || '-'}</td>
                    <td>${log.intent_terdeteksi || '-'}</td>
                    <td>${confidence}</td>
                    <td title="${log.pesan_keluar || ''}">${log.pesan_keluar || '-'}</td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch((error) => {
            console.error('Error loading chat logs:', error);
            showToast('Gagal memuat chat log.', 'error');
        });
}

function exportFeedback() {
    axios.get('/api/feedback?details=true')
        .then((response) => {
            const data = response.data || {};
            let csv = 'Rating,Jumlah,Persentase\n';
            const total = data.total_feedback || 1;

            for (let i = 5; i >= 1; i -= 1) {
                const count = data.rating_distribution[i] || 0;
                const percentage = ((count / total) * 100).toFixed(1);
                csv += `${i},${count},${percentage}%\n`;
            }

            csv += `\nTotal Feedback,${data.total_feedback || 0}\n`;
            csv += `Average Rating,${data.average_rating || 0}\n`;
            csv += `Positive (4-5),${data.positive || 0}\n`;
            csv += `Neutral (3),${data.neutral || 0}\n`;
            csv += `Negative (1-2),${data.negative || 0}\n`;

            downloadBlob(csv, 'feedback_evaluasi.csv');
            showToast('Export feedback selesai.', 'success');
        })
        .catch((error) => {
            console.error('Error exporting feedback:', error);
            showToast('Gagal export feedback.', 'error');
        });
}

function exportChatLogs() {
    axios.get('/api/analytics/chat-logs?limit=10000')
        .then((response) => {
            const logs = response.data || [];
            let csv = 'Waktu,ID Pelanggan,Nama,Pesan Masuk,Intent,Confidence,Entities,Pesan Keluar\n';

            logs.forEach((log) => {
                csv += `"${log.waktu_interaksi || ''}","${log.id_pelanggan || ''}","${log.nama_pelanggan || ''}","${log.pesan_masuk || ''}","${log.intent_terdeteksi || ''}","${log.confidence_score || ''}","${log.entities_extracted || ''}","${log.pesan_keluar || ''}"\n`;
            });

            downloadBlob(csv, 'chat_logs_evaluasi.csv');
            showToast('Export chat logs selesai.', 'success');
        })
        .catch((error) => {
            console.error('Error exporting chat logs:', error);
            showToast('Gagal export chat logs.', 'error');
        });
}

function exportConfusionMatrix() {
    axios.get('/api/analytics/confusion-matrix')
        .then((response) => {
            const data = response.data || [];
            let csv = 'ID Log,Pesan Masuk,Intent Terdeteksi,Confidence,Intent Actual\n';

            data.forEach((item) => {
                csv += `"${item.id_log || ''}","${item.pesan_masuk || ''}","${item.intent_terdeteksi || ''}","${item.confidence_score || ''}",""\n`;
            });

            downloadBlob(csv, 'confusion_matrix_data.csv');
            showToast('Export confusion matrix selesai.', 'success');
        })
        .catch((error) => {
            console.error('Error exporting confusion matrix:', error);
            showToast('Gagal export confusion matrix.', 'error');
        });
}

function downloadBlob(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
}

document.addEventListener('DOMContentLoaded', () => {
    bindTabButtons();
    loadMenu();
    loadAllPesanan();
    loadAnalytics();
});
