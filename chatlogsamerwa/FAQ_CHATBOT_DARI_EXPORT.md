# FAQ Chatbot Dari Export Chat Pelanggan

## Ringkasan Data

- Sumber analisis: 18 file chat WhatsApp pelanggan di folder `chatlogsamerwa`
- Total pesan pelanggan yang terbaca: 742 pesan
- Tema paling sering muncul:
  - Sambal/varian rasa: 71 pesan, muncul di 11 file
  - Pembayaran: 55 pesan, muncul di 8 file
  - Bagian ayam: 50 pesan, muncul di 11 file
  - Pengantaran/pengambilan: 46 pesan, muncul di 9 file
  - Nasi/lauk tambahan: 38 pesan, muncul di 10 file
  - Cek stok/kesiapan menu: 37 pesan, muncul di 11 file
  - Jam buka/waktu siap: 18 pesan, muncul di 8 file
  - Custom order: 8 pesan, muncul di 3 file

## Temuan Utama

- Pelanggan sangat sering memakai bahasa pendek/lokal seperti `ready`, `open`, `mauka`, `pesanka`, `buka ki`, `otw`, `tf`, `rek`, `sambel`, `paha atas`, `paha bawah`.
- Pelanggan jarang menyebut nama menu lengkap dengan format rapi. Mereka lebih sering langsung menyebut kebutuhan seperti bagian ayam, sambal, nasi, dan cara ambil.
- Banyak pelanggan menganggap pemesanan itu fleksibel:
  - bisa pilih bagian ayam
  - bisa pilih sambal berbeda per porsi
  - bisa tambah sambal
  - bisa tanpa nasi
  - bisa minta sambal dipisah atau dicampur
  - bisa minta saus
- FAQ pembayaran harus hati-hati karena data rekening di chat export tidak konsisten. Ada lebih dari satu nomor/metode yang dipakai.

## FAQ Utama

### 1. Apakah menu ready / masih ada?

- Contoh ucapan pelanggan:
  - `ready ayam bkr kah`
  - `masih ada kak?`
  - `open mi kah kak?`
  - `masih adakah kak?`
- Jawaban chatbot yang disarankan:
  - `Iya kak, [menu] ready. Mau pesan berapa?`
  - `Maaf kak, [menu] habis. Kalau mau, saya bantu cek menu lain yang ready.`
- Catatan knowledge:
  - bot harus bisa paham `ready`, `open`, `masi ada`, `masih ada`, `habis`
  - bot sebaiknya bisa jawab per menu, bukan jawaban umum

### 2. Menu apa saja yang ready?

- Contoh ucapan pelanggan:
  - `apapa sj menu yg ready`
  - `bisa liat menu nya kk?`
  - `menu yg ready`
- Jawaban chatbot yang disarankan:
  - `Menu yang ready saat ini: [daftar menu ready]. Mau pilih yang mana kak?`
- Catatan knowledge:
  - jangan hanya kirim semua menu kalau stok real-time tidak sama
  - kalau ada menu habis, bot harus bisa bilang jelas

### 3. Bisa pilih bagian ayam?

- Contoh ucapan pelanggan:
  - `paha ada?`
  - `3 dadanya dan 1 sayapnya`
  - `paha atas 1`
  - `bagian dadanya pke nasi`
  - `sayap mo kk`
- Jawaban chatbot yang disarankan:
  - `Bisa kak. Untuk [menu], bagian yang tersedia sekarang: [dada/paha atas/paha bawah/sayap]. Mau yang mana?`
- Catatan knowledge:
  - bagian ayam yang sering disebut pelanggan:
    - dada
    - paha
    - paha atas
    - paha bawah
    - sayap
  - bot harus bisa menangani kondisi stok bagian tertentu habis

### 4. Sambal apa yang tersedia?

- Contoh ucapan pelanggan:
  - `pake sambel ijo`
  - `sambel merah`
  - `sambel bawang`
  - `hijau`
  - `bawang`
- Jawaban chatbot yang disarankan:
  - `Pilihan sambal yang tersedia: sambal bawang, sambal ijo, sambal merah. Mau yang mana kak?`
- Catatan knowledge:
  - pelanggan lebih sering menulis `sambel` daripada `sambal`
  - `ijo`, `hijau`, `bawang`, `merah` harus dibaca sebagai pilihan sambal

### 5. Bisa beda sambal per porsi?

- Contoh ucapan pelanggan:
  - `satu pake sambel bawang, satu pake sambel ijo`
  - `sambal ijo 2, sambal merah 1`
  - `satu sambenya sambel bawang, satunya sambel ijo`
- Jawaban chatbot yang disarankan:
  - `Bisa kak. Saya catat per porsinya ya: [rincian sambal per item].`
- Catatan knowledge:
  - ini sangat sering terjadi
  - bot idealnya tidak memaksa satu jenis sambal untuk semua item

### 6. Bisa tambah sambal?

- Contoh ucapan pelanggan:
  - `extra sambel`
  - `tambah sambal ijo 1`
  - `tambah sambal merah 1`
  - `yg smbel bawangnya extra le kak`
- Jawaban chatbot yang disarankan:
  - `Bisa kak. Extra sambal [biaya jika ada]. Mau tambah berapa cup?`
- Catatan knowledge:
  - dari chat asli ada kasus extra sambal dikenakan biaya
  - nominal harus diambil dari aturan owner terbaru

### 7. Pakai nasi atau tidak?

- Contoh ucapan pelanggan:
  - `pake nasi`
  - `ndak pake nasi`
  - `tanpa nasi`
  - `bda pake nasi`
  - `nasi telur sambel ijo`
- Jawaban chatbot yang disarankan:
  - `Baik kak. Saya catat [pakai nasi/tanpa nasi].`
- Catatan knowledge:
  - banyak pelanggan tidak menyebut nasi di awal
  - bot perlu aktif konfirmasi `pakai nasi atau tidak`

### 8. Ada lauk tambahan seperti telur, tahu, tempe?

- Contoh ucapan pelanggan:
  - `ready telur crispy??`
  - `telur 2`
  - `tahu tempe kak tapi pake nasi bsa kah??`
  - `nasi telur`
- Jawaban chatbot yang disarankan:
  - `Ada kak, [menu/lauk] tersedia. Mau pesan berapa?`
- Catatan knowledge:
  - pelanggan tidak hanya pesan ayam
  - bot perlu paham kombinasi lauk + nasi

### 9. Berapa lama pesanan siap?

- Contoh ucapan pelanggan:
  - `berapa lama kak`
  - `belum masak kak?`
  - `slesai mi kah kakak?`
  - `jam brapa kira kira ready kak`
- Jawaban chatbot yang disarankan:
  - `Sekitar [estimasi] lagi siap kak. Nanti saya kabari kalau sudah jadi.`
- Catatan knowledge:
  - pelanggan cukup sering menunggu dan follow-up
  - bot idealnya punya jawaban status `sementara digoreng`, `sekitar 10-15 menit`, `siap mi`

### 10. Bisa diantar atau harus diambil?

- Contoh ucapan pelanggan:
  - `bisa di antar kan ka`
  - `di kurirkan sj`
  - `nnti di ambil`
  - `kesitu ka ambil`
  - `bisa delivery`
- Jawaban chatbot yang disarankan:
  - `Bisa kak [diantar/diambil]. Untuk lokasi [area], ongkirnya [nominal/kebijakan].`
  - `Kalau mau ambil sendiri juga bisa. Nanti saya kabari kalau sudah siap.`
- Catatan knowledge:
  - banyak chat bercampur antara kurir, antar sendiri, dan pickup
  - aturan antar masih terlihat manual dan situasional

### 11. Ongkir berapa?

- Contoh ucapan pelanggan:
  - `totalnya brp, dek? Dsinipi sy kasi ongkirnya`
  - `brp total dgn ongkirnya ksana`
  - `ongkir 10`
- Jawaban chatbot yang disarankan:
  - `Untuk lokasi [lokasi], estimasi ongkir [nominal]. Jadi totalnya [nominal].`
- Catatan knowledge:
  - ongkir terlihat tidak flat
  - FAQ harus memakai aturan jarak/area yang jelas dari owner

### 12. Jam buka jam berapa?

- Contoh ucapan pelanggan:
  - `jam berapa nnti buka kk?`
  - `buka ki kak?`
  - `masih buka ga kak`
  - `habis jumatan baru buka kakak`
- Jawaban chatbot yang disarankan:
  - `Jam buka hari ini [jam]. Kalau mau, saya bisa bantu cek menu yang sudah ready juga.`
- Catatan knowledge:
  - ada pola khusus seperti buka lebih lambat atau setelah jumatan
  - FAQ jam buka harus mengikuti operasional nyata, bukan angka statis saja

### 13. Bisa bayar transfer / QRIS?

- Contoh ucapan pelanggan:
  - `nnti sy tf`
  - `bisa byr qris kk?`
  - `tabe nomor rek ta`
  - `bank apa ini kak`
  - `coba ta Poto kan ka qris ta`
- Jawaban chatbot yang disarankan:
  - `Bisa kak, pembayaran tersedia via [transfer/QRIS/tunai]. Kalau mau transfer atau QRIS, saya kirim detailnya ya.`
- Catatan knowledge:
  - metode pembayaran yang muncul di chat:
    - transfer bank
    - QRIS
    - tunai
  - nomor rekening dan nama rekening belum konsisten antar chat, jadi wajib divalidasi owner sebelum dipakai chatbot

### 14. Berapa total pembayaran?

- Contoh ucapan pelanggan:
  - `brp smua kak`
  - `totalnya brp`
  - `brp total dgn ongkirnya`
- Jawaban chatbot yang disarankan:
  - `Total pesanan kak [rincian item] adalah Rp [total].`
- Catatan knowledge:
  - bot harus bisa hitung total item + extra sambal + ongkir bila ada

### 15. Bisa request custom?

- Contoh ucapan pelanggan:
  - `sambelnya langsung campur sja di ayamnya`
  - `kasi satu sj box`
  - `saus saja`
  - `jangan hangus sekali bakarnya kak`
  - `pisah sja kak`
- Jawaban chatbot yang disarankan:
  - `Bisa kak, saya catat request khususnya: [custom request].`
- Catatan knowledge:
  - custom request yang nyata dari chat:
    - sambal dicampur ke ayam
    - sambal dipisah
    - satu box / pisah box
    - saus sebagai pengganti sambal
    - jangan terlalu gosong

## Bank Frasa Yang Perlu Dipahami Chatbot

### Cek stok

- `ready`
- `ready mi`
- `ready miki`
- `ready kah`
- `open`
- `open mi kah`
- `masi ada`
- `masih adakah`
- `habis`

### Pemesanan

- `pesanka`
- `mauka`
- `mauka pesan`
- `mka pesan`
- `bungkus`
- `order`

### Pembayaran

- `tf`
- `transfer`
- `rek`
- `nomor rek`
- `bank apa ini`
- `qris`
- `barcode`

### Antar / ambil

- `diantar`
- `kurir`
- `ambil`
- `jemput`
- `otw`
- `singgahka ambil`

## Data Yang Wajib Dipastikan Owner Sebelum FAQ Dipakai Penuh

- daftar menu aktif yang benar
- sambal yang benar-benar tersedia
- biaya extra sambal
- aturan nasi termasuk/tidak
- aturan bagian ayam dan stoknya
- jam buka aktual, termasuk kondisi khusus seperti habis jumatan
- cakupan antar dan ongkir
- metode pembayaran resmi
- nomor rekening resmi
- QRIS yang resmi
- nama pemilik rekening yang benar

## Prioritas FAQ Untuk Chatbot

Urutan prioritas implementasi yang paling penting:

1. Cek stok menu
2. Pilih sambal
3. Pilih bagian ayam
4. Antar atau ambil
5. Pembayaran
6. Nasi / tanpa nasi
7. Estimasi waktu siap
8. Custom order

## Kesimpulan

Chat pelanggan menunjukkan bahwa chatbot harus lebih kuat di bahasa informal lokal, bukan cuma bahasa Indonesia formal. Fokus utama bukan sekadar mengenali nama menu, tetapi memahami konteks operasional nyata:

- apakah menu ready
- bagian ayam apa yang tersedia
- sambal apa dan berapa
- pakai nasi atau tidak
- diantar atau diambil
- bayar pakai apa
- kapan siap

Kalau FAQ ini dijadikan basis knowledge chatbot, maka akurasi percakapan akan jauh lebih dekat dengan pola chat pelanggan sebenarnya.
