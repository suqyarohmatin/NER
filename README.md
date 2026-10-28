# Article Named-Entity Recognition (NER) Service

Proyek ini dibangun untuk menerapkan teknik Named-Entity Recognition (NER), yaitu cabang Natural Language Processing (NLP) yang berfungsi mengidentifikasi dan mengelompokkan kata kunci penting dalam teks ke dalam kategori tertentu secara otomatis. Melalui antarmuka web dan RESTful API, sistem ini mengekstraksi entitas penting seperti nama tokoh (PERSON), institusi perbankan (ORG), lokasi (GPE), hingga tanggal (DATE) dari judul dan isi artikel berita keuangan tanpa perlu proses kurasi manual.

---

## Daftar Isi
1. [Tentang Proyek](#-tentang-proyek)
2. [Dataset](#-dataset)
3. [Arsitektur & Alur Kerja](#-arsitektur--alur-kerja)
4. [Struktur Repositori](#-struktur-repositori)
5. [Panduan Instalasi & Menjalankan](#-panduan-instalasi--menjalankan)
6. [Dokumentasi API](#-dokumentasi-api)
7. [Evaluasi Model](#-evaluasi-model)
8. [Kasus Uji (Test Cases)](#-kasus-uji-test-cases)
9. [Tim Pengembang](#-tim-pengembang)

---

## 1. Tentang Proyek

Proyek ini dibangun untuk menyelesaikan studi kasus ekstraksi entitas otomatis pada kumpulan artikel berita finansial. Sistem memproses teks artikel (judul dan isi), lalu mengidentifikasi rentang teks entitas beserta kategorinya seperti:
- `PERSON` (Nama orang/tokoh)
- `ORG` (Perusahaan, perbankan, institusi)
- `GPE` / `LOC` (Lokasi geografis, negara, kota)
- Label pendukung lainnya (misal: `DATE`, `NORP`)

---

## 2. Dataset

Dataset yang digunakan bersumber dari kliping artikel berita perbankan Malaysia (periode 7 September – 7 Oktober 2026) yang terbagi ke dalam 8 file CSV:
Dengan topik: 
1. `Hong Leong Bank`
2. `CIMB Group Malaysia`
3. `Public Bank Berhad`
4. `RHB Bank`
5. `MDV`
6. `Maybank CSR`
7. `Maybank Foundation`
8. `Maybank Group`

### Atribut Utama Dataset:
- `title`: Judul artikel
- `body`: Teks isi berita
- `language`: Bahasa artikel
- `entities`: Anotasi entitas acuan
- `original_id`, `source_name`, `date_published`: Metadata sumber artikel

---

## 3. Alur Kerja

Sistem ini memisahkan dua alur utama: **Pipeline Pengembangan Model (Offline/Training)** dan **Layanan Inferensi (Online/Serving)**.

### 1. Diagram Alur Kerja
```text
+-----------------------------------------------------------------------------+
|                 1. PIPELINE PENGEMBANGAN MODEL (OFFLINE)                    |
+-----------------------------------------------------------------------------+
  [8 File CSV Berita]
           |
           v
  [Pembersihan Teks & Format Dokumen]
           |
           v
  [Anotasi Entitas Acuan (Ground Truth)]
           |
           v
  [Pemisahan Data: Train (70%) | Val (15%) | Test (15%)]
           |
           +-------------------------------+
           |                               |
           v                               v
  [Training]                      [Pengujian Model]
           |                               |
           v                               v
  [Simpan Model Artifact] --------> [Evaluasi: P, R, F1]
           |
           | (Bobot model dimuat)
           v
+-----------------------------------------------------------------------------+
|                    2. LAYANAN INFERENSI (RUN-TIME / ONLINE)                 |
+-----------------------------------------------------------------------------+
  [Pengguna / Browser Web]
           |
           | 1. Kirim teks (Judul + Isi)
           v
  [Antarmuka Web (UI) / API Endpoint]
           |
           | 2. Validasi & kirim ke pipeline inferensi
           v
  [NER Inference Engine] <--- (Model Artifact)
           |
           | 3. Prediksi entitas & hitung indeks span karakter (start, end)
           v
  [Formatter JSON]
  { "text": "...", "label": "...", "start": 0, "end": 7 }
           |
           | 4. Menampilkan respon data
           v
  [Tampilan Hasil di UI (Highlight Teks)]
```
### 2. Penjelasan Tahapan Kerja

1. **Persiapan Data & Preprocessing**
   - **Pembersihan Teks:** Menangani data teks yang hilang (*missing values*), menghapus spasi redundan, dan menstandarisasi encoding non-ASCII.
   - **Penggabungan Konteks:** Menggabungkan judul (*title*) dan isi (*body*) artikel agar model membaca konteks berita secara utuh.
   - **Pemetaan Span Anotasi:** Menyesuaikan indeks karakter awal (*start*) dan akhir (*end*) entitas terhadap teks gabungan sebagai data acuan (*ground truth*).

2. **Pengembangan & Validasi Model**
   - **Pemisahan Data:** Membagi dataset menjadi *Train* (70%), *Validation* (15%), dan *Test* (15%) berbasis dokumen artikel untuk mencegah kebocoran data (*data leakage*).
   - **Baseline vs Adaptasi:** Menjalankan model dasar sebagai pembanding awal, lalu melatih atau menyesuaikan model dengan data anotasi domain perbankan.
   - **Evaluasi Ketat:** Mengukur performa menggunakan metrik *Precision*, *Recall*, dan *F1-score* dengan aturan pencocokan rentang karakter (*exact span matching*).

3. **Layanan Inferensi (Serving & API)**
   - **Validasi Input:** Server memvalidasi isi request untuk mencegah input kosong atau teks berlebih.
   - **Ekstraksi Span & Label:** Mesin inferensi memetakan token hasil prediksi kembali ke posisi indeks karakter asli dalam string dokumen.
   - **Integrasi Web UI:** Hasil ekstraksi dikembalikan dalam format JSON terstruktur untuk dirender langsung di antarmuka peramban (*highlight* warna berdasarkan jenis entitas).
