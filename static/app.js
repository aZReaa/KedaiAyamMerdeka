const loadedTabs = new Set();

function setText(ids, value) {
    ids.forEach((id) => {
        const node = document.getElementById(id);
        if (node) {
            node.textContent = value;
        }
    });
}

function formatCurrency(value) {
    const amount = Number(value || 0);
    return `Rp ${amount.toLocaleString("id-ID")}`;
}

function formatDateTime(value) {
    if (!value) {
        return "-";
    }

    const date = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString("id-ID", {
        dateStyle: "medium",
        timeStyle: "short"
    });
}

function updateSyncStamp(label) {
    setText(["globalLastUpdated"], `${label} • ${formatDateTime(new Date())}`);
}

function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) {
        return;
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    window.setTimeout(() => {
        toast.remove();
    }, 3200);
}

function setTableEmptyState(tbodyId, colspan, message) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) {
        return;
    }

    tbody.innerHTML = `<tr class="empty-state"><td colspan="${colspan}">${message}</td></tr>`;
}

function getActiveTab() {
    return document.querySelector(".tab-content.active")?.id || "dashboard";
}

function loadTabData(tabId, force = false) {
    const loaders = {
        dashboard: () => loadDashboardData(force),
        menu: () => loadMenu(force),
        pesanan: () => loadAllPesanan(force),
        analytics: () => loadAnalytics(force)
    };

    const shouldAlwaysRefresh = tabId === "dashboard";
    if (!force && !shouldAlwaysRefresh && loadedTabs.has(tabId)) {
        return;
    }

    const loader = loaders[tabId];
    if (loader) {
        loader();
        loadedTabs.add(tabId);
    }
}

function showTab(tabId) {
    document.querySelectorAll(".tab-content").forEach((content) => {
        content.classList.toggle("active", content.id === tabId);
    });

    document.querySelectorAll(".tab-btn").forEach((button) => {
        button.classList.toggle("active", button.dataset.tab === tabId);
    });

    loadTabData(tabId);
}

function bindTabButtons() {
    document.querySelectorAll(".tab-btn").forEach((button) => {
        button.addEventListener("click", () => showTab(button.dataset.tab));
    });
}

function bindQuickActions() {
    document.querySelectorAll("[data-switch-tab]").forEach((button) => {
        button.addEventListener("click", () => showTab(button.dataset.switchTab));
    });
}

function loadDatabaseInfo() {
    axios.get("/api/system/db-info")
        .then((response) => {
            const info = response.data || {};
            const target = `${info.host || "-"}:${info.port || "-"} / ${info.database || "-"}`;
            setText(["activeDatabaseTarget", "dashboardDatabaseTarget"], target);
        })
        .catch((error) => {
            console.error("Error loading database info:", error);
            setText(["activeDatabaseTarget", "dashboardDatabaseTarget"], "Tidak diketahui");
        });
}

function updateMenuSummary(menuItems) {
    const total = menuItems.length;
    const available = menuItems.filter((item) => item.ketersediaan).length;
    const unavailable = total - available;

    setText(["menuCount", "summaryMenuTotal"], total);
    setText(["availableMenuCount", "summaryMenuAvailable"], available);
    setText(["summaryMenuUnavailable"], unavailable);
    setText(["menuStatusText"], `${total} item dimuat`);
}

function renderMenuTable(menuItems) {
    const tbody = document.getElementById("menuTableBody");
    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";

    if (menuItems.length === 0) {
        setTableEmptyState("menuTableBody", 6, "Belum ada menu yang tersimpan.");
        return;
    }

    menuItems.forEach((menu, index) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td data-label="No">${index + 1}</td>
            <td data-label="Nama menu">${menu.nama_menu}</td>
            <td data-label="Harga">${formatCurrency(menu.harga)}</td>
            <td data-label="Kategori">${menu.kategori || "-"}</td>
            <td data-label="Status"><span class="status-badge ${menu.ketersediaan ? "status-selesai" : "status-batal"}">${menu.ketersediaan ? "Tersedia" : "Nonaktif"}</span></td>
            <td data-label="Aksi">
                <button class="delete-btn" type="button" onclick="deleteMenu(${menu.id_menu})">Hapus</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function fetchMenuData({ renderTable = true, syncLabel = "Menu diperbarui", showErrorToast = true } = {}) {
    return axios.get("/api/menu")
        .then((response) => {
            const menuItems = response.data || [];
            updateMenuSummary(menuItems);

            if (renderTable) {
                renderMenuTable(menuItems);
            }

            updateSyncStamp(syncLabel);
            return menuItems;
        })
        .catch((error) => {
            console.error("Error loading menu:", error);
            if (renderTable) {
                setText(["menuStatusText"], "Gagal memuat menu");
            }
            if (showErrorToast) {
                showToast("Menu gagal dimuat.", "error");
            }
            throw error;
        });
}

function loadMenu(force = false) {
    return fetchMenuData({
        renderTable: true,
        syncLabel: force ? "Menu disegarkan" : "Menu dimuat"
    });
}

function loadMenuSummary() {
    return fetchMenuData({
        renderTable: false,
        syncLabel: "Ringkasan menu diperbarui",
        showErrorToast: false
    });
}

function updateOrderSummary(orderItems) {
    const counts = {
        dipesan: 0,
        menunggu_konfirmasi_admin: 0,
        menunggu_pembayaran: 0,
        diproses: 0,
        selesai: 0,
        batal: 0,
        ditolak_admin: 0
    };

    orderItems.forEach((item) => {
        if (counts[item.status] !== undefined) {
            counts[item.status] += 1;
        }
    });

    const total = orderItems.length;
    const active = counts.dipesan + counts.menunggu_konfirmasi_admin + counts.menunggu_pembayaran + counts.diproses;

    setText(["dashboardActiveOrders", "activeOrdersCount"], active);
    setText(["completedOrderCount", "orderDoneCount"], counts.selesai);
    setText(["orderCount"], total);
    setText(["orderPendingCount"], counts.dipesan + counts.menunggu_konfirmasi_admin);
    setText(["orderAwaitingPaymentCount"], counts.menunggu_pembayaran);
    setText(["orderProcessingCount"], counts.diproses);
    setText(["orderCancelledCount"], counts.batal + counts.ditolak_admin);
    setText(["orderStatusText"], `${total} pesanan dimuat`);
}

function renderPesananTable(data) {
    const tbody = document.getElementById("pesananTableBody");
    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";

    if (data.length === 0) {
        setTableEmptyState("pesananTableBody", 10, "Tidak ada pesanan yang cocok.");
        return;
    }

    data.forEach((pesanan) => {
        const row = document.createElement("tr");
        const namaPelanggan = pesanan.nama_pelanggan || "Pelanggan";
        const statusClass = `status-${pesanan.status}`;
        const paymentStatus = pesanan.payment_status || "pending";
        const paymentClass = `payment-${paymentStatus.replace(/_/g, "-")}`;
        const statusLabelMap = {
            dipesan: "Menunggu admin",
            menunggu_konfirmasi_admin: "Menunggu admin",
            menunggu_pembayaran: "Menunggu pembayaran",
            diproses: "Diproses",
            selesai: "Selesai",
            batal: "Batal",
            ditolak_admin: "Ditolak admin"
        };
        const paymentLabelMap = {
            not_requested: "Belum diminta",
            pending: "Menunggu bukti",
            proof_submitted: "Menunggu verifikasi",
            verified: "Terverifikasi",
            rejected: "Ditolak"
        };
        const effectivePaymentStatus = ["dipesan", "menunggu_konfirmasi_admin", "ditolak_admin"].includes(pesanan.status)
            ? "not_requested"
            : paymentStatus;
        const effectivePaymentClass = effectivePaymentStatus === "not_requested"
            ? "payment-not-requested"
            : paymentClass;
        const paymentLabel = paymentLabelMap[effectivePaymentStatus] || effectivePaymentStatus;
        const statusLabel = statusLabelMap[pesanan.status] || pesanan.status;

        let actionButtons = '<span class="muted-meta">Tidak ada aksi</span>';
        if (pesanan.status === "dipesan" || pesanan.status === "menunggu_konfirmasi_admin") {
            actionButtons = `
                <div class="action-stack">
                    <button class="action-btn success" type="button" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'menunggu_pembayaran')">Setujui</button>
                    <button class="action-btn danger" type="button" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'ditolak_admin')">Tolak</button>
                </div>
            `;
        } else if (pesanan.status === "menunggu_pembayaran") {
            if (paymentStatus === "proof_submitted") {
                actionButtons = `
                    <div class="action-stack">
                        <button class="action-btn success" type="button" onclick="verifyPayment(${pesanan.id_pesanan})">Verifikasi bayar</button>
                        <button class="action-btn danger" type="button" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'batal')">Batalkan</button>
                    </div>
                `;
            } else {
                actionButtons = `
                    <div class="action-stack">
                        <span class="muted-meta">Menunggu bukti bayar</span>
                        <button class="action-btn danger" type="button" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'batal')">Batalkan</button>
                    </div>
                `;
            }
        } else if (pesanan.status === "diproses") {
            actionButtons = `
                <div class="action-stack">
                    <button class="action-btn success" type="button" onclick="updateOrderStatus(${pesanan.id_pesanan}, 'selesai')">Selesaikan</button>
                </div>
            `;
        }

        const proofButton = pesanan.payment_proof_file_id
            ? `<button class="action-btn secondary" type="button" onclick="openPaymentProof(${pesanan.id_pesanan})">Lihat bukti</button>`
            : '<span class="muted-meta">Belum ada</span>';

        row.innerHTML = `
            <td data-label="ID">#${pesanan.id_pesanan}</td>
            <td data-label="Pelanggan">${namaPelanggan}</td>
            <td data-label="ID chat">${pesanan.id_pelanggan || "-"}</td>
            <td data-label="Detail">${pesanan.detail_pesanan || "-"}</td>
            <td data-label="Total">${formatCurrency(pesanan.total_harga)}</td>
            <td data-label="Status"><span class="status-badge ${statusClass}">${statusLabel}</span></td>
            <td data-label="Pembayaran"><span class="status-badge ${effectivePaymentClass}">${paymentLabel}</span></td>
            <td data-label="Bukti">${proofButton}</td>
            <td data-label="Waktu">${formatDateTime(pesanan.waktu_pesan)}</td>
            <td data-label="Aksi">${actionButtons}</td>
        `;
        tbody.appendChild(row);
    });
}

function fetchPesanan(url, { renderTable = true, syncLabel = "Pesanan diperbarui", showErrorToast = true } = {}) {
    return axios.get(url)
        .then((response) => {
            const data = response.data || [];
            updateOrderSummary(data);

            if (renderTable) {
                renderPesananTable(data);
            }

            updateSyncStamp(syncLabel);
            return data;
        })
        .catch((error) => {
            console.error("Error loading pesanan:", error);
            if (renderTable) {
                setText(["orderStatusText"], "Gagal memuat pesanan");
            }
            if (showErrorToast) {
                showToast("Pesanan gagal dimuat.", "error");
            }
            throw error;
        });
}

function loadAllPesanan(force = false) {
    const statusFilter = document.getElementById("statusFilter")?.value || "";
    let url = "/api/pesanan";

    if (statusFilter) {
        url += `?status=${encodeURIComponent(statusFilter)}`;
    }

    return fetchPesanan(url, {
        renderTable: true,
        syncLabel: force ? "Pesanan disegarkan" : "Pesanan dimuat"
    });
}

function loadOrderSummary() {
    const statusFilter = document.getElementById("statusFilter")?.value || "";
    let url = "/api/pesanan";

    if (statusFilter) {
        url += `?status=${encodeURIComponent(statusFilter)}`;
    }

    return fetchPesanan(url, {
        renderTable: false,
        syncLabel: "Ringkasan pesanan diperbarui",
        showErrorToast: false
    });
}

function loadPesananByCustomer() {
    const pelangganId = document.getElementById("pelanggan_id")?.value.trim();

    if (!pelangganId) {
        showToast("Masukkan ID pelanggan lebih dulu.", "info");
        return Promise.resolve();
    }

    return fetchPesanan(`/api/pesanan?id_pelanggan=${encodeURIComponent(pelangganId)}`, {
        renderTable: true,
        syncLabel: `Pesanan pelanggan ${pelangganId} dimuat`
    });
}

function updateChatSummary(data) {
    const totalInteractions = data.total_interactions || 0;
    const averageConfidence = data.average_confidence ? `${(data.average_confidence * 100).toFixed(1)}%` : "0%";

    setText(["totalInteractions", "analyticsTotalInteractions"], totalInteractions);
    setText(["avgConfidence", "analyticsAvgConfidence"], averageConfidence);
}

function renderIntentDistribution(data) {
    const tbody = document.querySelector("#intentDistributionTable tbody");
    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";
    if (!data.intent_distribution || data.intent_distribution.length === 0) {
        tbody.innerHTML = '<tr class="empty-state"><td colspan="3">Belum ada data intent.</td></tr>';
        return;
    }

    const total = data.total_interactions || 1;
    data.intent_distribution.forEach((item) => {
        const percentage = ((item.count / total) * 100).toFixed(1);
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${item.intent_terdeteksi}</td>
            <td>${item.count}</td>
            <td>${percentage}%</td>
        `;
        tbody.appendChild(row);
    });
}

function renderConfidenceDistribution(data) {
    const tbody = document.querySelector("#confidenceDistributionTable tbody");
    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";
    if (!data.confidence_distribution || data.confidence_distribution.length === 0) {
        tbody.innerHTML = '<tr class="empty-state"><td colspan="2">Belum ada data tingkat keyakinan.</td></tr>';
        return;
    }

    data.confidence_distribution.forEach((item) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${item.confidence_level}</td>
            <td>${item.count}</td>
        `;
        tbody.appendChild(row);
    });
}

function fetchChatStats({ renderTables = true, showErrorToast = true } = {}) {
    return axios.get("/api/analytics/chat")
        .then((response) => {
            const data = response.data || {};
            updateChatSummary(data);

            if (renderTables) {
                renderIntentDistribution(data);
                renderConfidenceDistribution(data);
            }

            return data;
        })
        .catch((error) => {
            console.error("Error loading analytics:", error);
            if (showErrorToast) {
                showToast("Analitik chat gagal dimuat.", "error");
            }
            throw error;
        });
}

function loadChatStats() {
    return fetchChatStats({ renderTables: true });
}

function loadChatSummary() {
    return fetchChatStats({ renderTables: false, showErrorToast: false });
}

function loadFeedbackStats() {
    return axios.get("/api/feedback")
        .then((response) => {
            const data = response.data || {};
            const average = data.average_rating ? `${data.average_rating} / 5` : "-";

            setText(["totalFeedback", "analyticsTotalFeedback"], data.total_feedback || 0);
            setText(["avgRating", "heroAvgRating"], average);
            return data;
        })
        .catch((error) => {
            console.error("Error loading feedback stats:", error);
            showToast("Statistik feedback gagal dimuat.", "error");
            throw error;
        });
}

function loadFeedbackDetails() {
    return axios.get("/api/feedback?details=true")
        .then((response) => {
            const data = response.data || {};
            const tbody = document.querySelector("#ratingDistributionTable tbody");
            if (!tbody) {
                return data;
            }

            tbody.innerHTML = "";
            if (!data.rating_distribution) {
                tbody.innerHTML = '<tr class="empty-state"><td colspan="3">Belum ada feedback pelanggan.</td></tr>';
                return data;
            }

            const total = data.total_feedback || 1;
            for (let i = 5; i >= 1; i -= 1) {
                const count = data.rating_distribution[i] || 0;
                const percentage = ((count / total) * 100).toFixed(1);
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${i} / 5</td>
                    <td>${count}</td>
                    <td>${percentage}%</td>
                `;
                tbody.appendChild(row);
            }

            return data;
        })
        .catch((error) => {
            console.error("Error loading feedback details:", error);
            showToast("Sebaran feedback gagal dimuat.", "error");
            throw error;
        });
}

function loadChatLogs(force = false) {
    return axios.get("/api/analytics/chat-logs?limit=50")
        .then((response) => {
            const logs = response.data || [];
            const tbody = document.querySelector("#chatLogsTable tbody");
            if (!tbody) {
                return logs;
            }

            tbody.innerHTML = "";

            if (logs.length === 0) {
                tbody.innerHTML = '<tr class="empty-state"><td colspan="6">Belum ada chat log.</td></tr>';
                return logs;
            }

            logs.forEach((log) => {
                const row = document.createElement("tr");
                const confidence = log.confidence_score ? `${(log.confidence_score * 100).toFixed(1)}%` : "-";

                row.innerHTML = `
                    <td>${formatDateTime(log.waktu_interaksi)}</td>
                    <td>${log.nama_pelanggan || "-"}</td>
                    <td title="${log.pesan_masuk || ""}">${log.pesan_masuk || "-"}</td>
                    <td>${log.intent_terdeteksi || "-"}</td>
                    <td>${confidence}</td>
                    <td title="${log.pesan_keluar || ""}">${log.pesan_keluar || "-"}</td>
                `;
                tbody.appendChild(row);
            });

            if (force) {
                updateSyncStamp("Chat log disegarkan");
            }

            return logs;
        })
        .catch((error) => {
            console.error("Error loading chat logs:", error);
            showToast("Chat log gagal dimuat.", "error");
            throw error;
        });
}

function loadAnalytics(force = false) {
    return Promise.all([
        fetchChatStats({ renderTables: true }),
        loadFeedbackStats(),
        loadFeedbackDetails(),
        loadChatLogs()
    ])
        .then(() => {
            updateSyncStamp(force ? "Analitik disegarkan" : "Analitik dimuat");
        });
}

function loadDashboardData(force = false) {
    return Promise.all([
        loadMenuSummary(),
        loadOrderSummary(),
        loadFeedbackStats(),
        loadChatSummary()
    ])
        .then(() => {
            updateSyncStamp(force ? "Dashboard disegarkan" : "Dashboard dimuat");
        })
        .catch((error) => {
            console.error("Error loading dashboard:", error);
        });
}

function deleteMenu(menuId) {
    if (!confirm("Hapus menu ini?")) {
        return;
    }

    axios.delete(`/api/menu/${menuId}`)
        .then(() => {
            showToast(`Menu #${menuId} sudah dihapus.`, "success");
            loadDashboardData(true);
            loadMenu(true);
        })
        .catch((error) => {
            console.error("Error deleting menu:", error);
            showToast("Menu gagal dihapus.", "error");
        });
}

function updateOrderStatus(orderId, newStatus) {
    const statusLabelMap = {
        menunggu_konfirmasi_admin: "menunggu admin",
        menunggu_pembayaran: "menunggu pembayaran",
        diproses: "diproses",
        selesai: "selesai",
        batal: "batal",
        ditolak_admin: "ditolak admin"
    };
    let confirmMessage = `Ubah status pesanan #${orderId} menjadi ${statusLabelMap[newStatus] || newStatus}?`;

    if (newStatus === "selesai") {
        confirmMessage += "\n\nPelanggan akan menerima permintaan feedback.";
    } else if (newStatus === "menunggu_pembayaran") {
        confirmMessage += "\n\nPelanggan akan menerima instruksi pembayaran.";
    } else if (newStatus === "ditolak_admin") {
        confirmMessage += "\n\nPelanggan akan diberi tahu bahwa pesanan tidak bisa dipenuhi.";
    }

    if (!confirm(confirmMessage)) {
        return;
    }

    axios.put(`/api/pesanan/${orderId}/status`, { status: newStatus, send_notification: true })
        .then((response) => {
            let message = `Status pesanan #${orderId} diperbarui.`;
            if (response.data.feedback_requested) {
                message += " Permintaan feedback juga dikirim.";
            }

            showToast(message, "success");
            loadDashboardData(true);
            loadAllPesanan(true);
        })
        .catch((error) => {
            console.error("Error updating status:", error);
            showToast("Status pesanan gagal diubah.", "error");
        });
}

function verifyPayment(orderId) {
    if (!confirm(`Verifikasi pembayaran untuk pesanan #${orderId}?`)) {
        return;
    }

    axios.put(`/api/pesanan/${orderId}/payment/verify`)
        .then(() => {
            showToast(`Pembayaran pesanan #${orderId} sudah diverifikasi.`, "success");
            loadDashboardData(true);
            loadAllPesanan(true);
        })
        .catch((error) => {
            console.error("Error verifying payment:", error);
            showToast("Verifikasi pembayaran gagal.", "error");
        });
}

function openPaymentProof(orderId) {
    const modal = document.getElementById("paymentProofModal");
    const frame = document.getElementById("paymentProofFrame");
    const image = document.getElementById("paymentProofImage");
    const fallback = document.getElementById("paymentProofFallback");
    const link = document.getElementById("paymentProofLink");
    const proofUrl = `/api/pesanan/${orderId}/payment-proof`;

    if (!modal || !frame || !image || !fallback || !link) {
        window.open(proofUrl, "_blank", "noopener,noreferrer");
        return;
    }

    closePaymentProofModal();
    modal.hidden = false;
    document.body.classList.add("modal-open");

    axios.get(proofUrl, { responseType: "blob" })
        .then((response) => {
            const blob = response.data;
            const objectUrl = URL.createObjectURL(blob);
            const contentType = (blob.type || response.headers["content-type"] || "").toLowerCase();
            const disposition = response.headers["content-disposition"] || "";
            const filenameMatch = disposition.match(/filename=\"?([^"]+)\"?/i);
            const filename = filenameMatch ? filenameMatch[1].toLowerCase() : "";

            modal.dataset.objectUrl = objectUrl;
            link.href = objectUrl;
            link.download = filename || `payment-proof-${orderId}`;

            image.hidden = true;
            image.removeAttribute("src");
            frame.hidden = true;
            frame.src = "about:blank";
            fallback.hidden = true;

            const isImage = contentType.startsWith("image/") || /\.(png|jpg|jpeg|webp|gif)$/i.test(filename);
            const isPdf = contentType.includes("pdf") || /\.pdf$/i.test(filename);

            if (isImage) {
                image.src = objectUrl;
                image.hidden = false;
                return;
            }

            if (isPdf) {
                frame.src = objectUrl;
                frame.hidden = false;
                return;
            }

            fallback.hidden = false;
        })
        .catch((error) => {
            console.error("Error opening payment proof:", error);
            showToast("Bukti pembayaran gagal dimuat.", "error");
            closePaymentProofModal();
        });
}

function closePaymentProofModal() {
    const modal = document.getElementById("paymentProofModal");
    const frame = document.getElementById("paymentProofFrame");
    const image = document.getElementById("paymentProofImage");
    const fallback = document.getElementById("paymentProofFallback");
    const link = document.getElementById("paymentProofLink");

    const objectUrl = modal?.dataset?.objectUrl;
    if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
        delete modal.dataset.objectUrl;
    }

    if (frame) {
        frame.src = "about:blank";
        frame.hidden = true;
    }

    if (image) {
        image.removeAttribute("src");
        image.hidden = true;
    }

    if (fallback) {
        fallback.hidden = true;
    }

    if (link) {
        link.removeAttribute("href");
    }

    if (modal) {
        modal.hidden = true;
    }

    document.body.classList.remove("modal-open");
}

function loadPesanan() {
    return loadPesananByCustomer();
}

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closePaymentProofModal();
    }
});

function initDatabase() {
    if (!confirm("Isi ulang database dengan data contoh?")) {
        return;
    }

    axios.post("/api/init_db")
        .then((response) => {
            showToast(response.data.message || "Database berhasil diisi ulang.", "success");
            loadedTabs.clear();
            loadDatabaseInfo();
            loadTabData(getActiveTab(), true);
            loadDashboardData(true);
        })
        .catch((error) => {
            console.error("Error initializing database:", error);
            showToast("Database gagal diisi ulang.", "error");
        });
}

function exportFeedback() {
    axios.get("/api/feedback?details=true")
        .then((response) => {
            const data = response.data || {};
            let csv = "Rating,Jumlah,Persentase\n";
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

            downloadBlob(csv, "feedback_evaluasi.csv");
            showToast("File feedback berhasil diunduh.", "success");
        })
        .catch((error) => {
            console.error("Error exporting feedback:", error);
            showToast("File feedback gagal diunduh.", "error");
        });
}

function exportChatLogs() {
    axios.get("/api/analytics/chat-logs?limit=10000")
        .then((response) => {
            const logs = response.data || [];
            let csv = "Waktu,ID Pelanggan,Nama,Pesan Masuk,Intent,Confidence,Entities,Pesan Keluar\n";

            logs.forEach((log) => {
                csv += `"${log.waktu_interaksi || ""}","${log.id_pelanggan || ""}","${log.nama_pelanggan || ""}","${log.pesan_masuk || ""}","${log.intent_terdeteksi || ""}","${log.confidence_score || ""}","${log.entities_extracted || ""}","${log.pesan_keluar || ""}"\n`;
            });

            downloadBlob(csv, "chat_logs_evaluasi.csv");
            showToast("Chat log berhasil diunduh.", "success");
        })
        .catch((error) => {
            console.error("Error exporting chat logs:", error);
            showToast("Chat log gagal diunduh.", "error");
        });
}

function exportConfusionMatrix() {
    axios.get("/api/analytics/confusion-matrix")
        .then((response) => {
            const data = response.data || [];
            let csv = "ID Log,Pesan Masuk,Intent Terdeteksi,Confidence,Intent Actual\n";

            data.forEach((item) => {
                csv += `"${item.id_log || ""}","${item.pesan_masuk || ""}","${item.intent_terdeteksi || ""}","${item.confidence_score || ""}",""\n`;
            });

            downloadBlob(csv, "confusion_matrix_data.csv");
            showToast("Confusion matrix berhasil diunduh.", "success");
        })
        .catch((error) => {
            console.error("Error exporting confusion matrix:", error);
            showToast("Confusion matrix gagal diunduh.", "error");
        });
}

function downloadBlob(content, filename) {
    const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
}

function bindMenuForm() {
    const form = document.getElementById("menuForm");
    if (!form) {
        return;
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();

        const nama_menu = document.getElementById("nama_menu").value;
        const harga = document.getElementById("harga").value;
        const kategori = document.getElementById("kategori").value;
        const ketersediaan = document.getElementById("ketersediaan").checked;

        axios.post("/api/menu", {
            nama_menu,
            harga,
            kategori,
            ketersediaan
        })
            .then(() => {
                showToast("Menu baru sudah disimpan.", "success");
                form.reset();
                document.getElementById("ketersediaan").checked = true;
                loadDashboardData(true);
                loadMenu(true);
            })
            .catch((error) => {
                console.error("Error adding menu:", error);
                showToast("Menu gagal disimpan.", "error");
            });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindTabButtons();
    bindQuickActions();
    bindMenuForm();
    loadDatabaseInfo();
    loadTabData(getActiveTab(), true);
});
