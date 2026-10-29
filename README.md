# Article Named-Entity Recognition (NER) Service

Proyek ini dibangun untuk menerapkan teknik Named-Entity Recognition (NER), yaitu cabang Natural Language Processing (NLP) yang berfungsi mengidentifikasi dan mengelompokkan kata kunci penting dalam teks ke dalam kategori tertentu secara otomatis. Melalui antarmuka web dan RESTful API, sistem ini mengekstraksi entitas penting seperti nama tokoh (PERSON), institusi perbankan (ORG), lokasi (GPE), hingga tanggal (DATE) dari judul dan isi artikel berita keuangan tanpa perlu proses kurasi manual.

---

## Daftar Isi
1. [Tentang Proyek](#-tentang-proyek)
2. [Dataset](#-dataset)
3. [Alur Kerja](#-alur-kerja)
4. [Struktur Repositori](#-struktur-repositori)
5. [Evaluasi Model](#-evaluasi-model)
6. [Kasus Uji (Test Cases)](#-kasus-uji-test-cases)
7. [Tim Pengembang](#-tim-pengembang)

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

  
## 4. Struktur Repositori

```text
├── data/
│   ├── annotations/               # Data anotasi entitas acuan
│   └── readme.md                  # Dokumentasi panduan dataset
├── models/
│   └── trained/                   # Direktori artefak model hasil training
├── notebooks/
│   └── Maybank_NER_Workflow.ipynb # Eksplorasi data & pipeline pelatihan model
├── reports/
│   └── data_audit.json            # Laporan audit kualitas dan konsistensi data
├── src/
│   ├── __init__.py
│   ├── app.py                     # Entrypoint server backend API / Web UI
│   ├── audit_maybank_ner.py       # Script audit entitas Maybank NER
│   ├── check_article_encoding.py  # Pemeriksaan encoding karakter artikel
│   ├── compare_all_annotations.py # Komparasi seluruh versi anotasi
│   ├── compare_entity_differences.py
│   ├── compare_second_article.py
│   ├── evaluate_model.py          # Evaluasi metrik performa model (P, R, F1)
│   ├── export_reviewed.py         # Ekspor data anotasi hasil review
│   ├── fix_first_annotation.py    # Perbaikan anotasi artikel pertama
│   ├── fix_myor_klibor.py         # Normalisasi istilah finansial (MYOR/KLIBOR)
│   ├── fix_second_annotation.py   # Perbaikan anotasi artikel kedua
│   ├── make_annotation_template.py# Generator template anotasi entitas
│   ├── metrics.py                 # Perhitungan metrik evaluasi (exact span)
│   ├── prepare_data.py            # Pembersihan & preprocessing teks artikel
│   ├── review_annotations.py      # Script peninjauan anotasi entitas
│   ├── review_second_annotation.py
│   ├── save_first_review.py
│   ├── save_second_review.py
│   ├── show_article_chunks.py     # Pengecekan chunk / tokenisasi teks panjang
│   ├── split_data.py              # Pembagian dataset (Train/Val/Test)
│   ├── train_model.py             # Script pelatihan & adaptasi model spaCy
│   └── validate_annotations.py   # Validasi skema dan span karakter anotasi
├── templates/
│   └── index.html                 # Tampilan antarmuka web pengguna
├── tests/
│   └── test_api.py                # Pengujian otomatis endpoint API
├── .gitignore
├── COLAB_GUIDE.md                 # Panduan menjalankan aplikasi di Google Colab
├── README.md                      # Dokumentasi utama proyek
└── requirements.txt               # Daftar pustaka & dependensi Python
```

## 5. Evaluasi Model
Evaluasi model dihitung menggunakan skrip `src/evaluate_model.py` dan `src/metrics.py` pada data uji (*test set*) menggunakan metrik evaluasi pencocokan rentang karakter dan tipe label secara tepat. Bobot model hasil pelatihan dimuat dari direktori `models/trained/`.

| Metrik | Model Baseline | Model Terlatih |
|---|:---:|:---:|
| **Precision** | 0.180 |0.951|
| **Recall** | 0.578 | 0.985 |
| **F1-Score** | 0.274 | 0.968 |

### Temuan Evaluasi & Analisis Data:
- **Baseline vs. Adaptasi:** Model terlatih `ner_custom_v1` menunjukkan peningkatan kemampuan deteksi pada entitas spesifik domain perbankan dan singkatan korporat.
- **Span Boundary Error:** Kesalahan yang masih ditemukan umumnya berupa pemotongan batas teks (*boundary span*) pada nama entitas organisasi yang panjang atau bertingkat.
- **Kategori Tertinggi:** Entitas lokasi (`GPE`) dan orang (`PERSON`) memiliki tingkat akurasi paling stabil dibandingkan entitas lembaga perbankan kompleks (`ORG`).

## 6. Kasus Uji (Test Cases)

Pengujian sistem dilakukan secara otomatis menggunakan `pytest` (melalui berkas `tests/test_api.py`) untuk menguji endpoint API pada src/app.py, validasi skema input, serta ketepatan indeks rentang karakter entitas.

| No | Skenario Uji | Deskripsi Input | Hasil yang Diharapkan | Status |
|:--:|---|---|---|:--:|
| 1 | **Valid Normal Input** | Teks berita lengkap dengan nama bank, tokoh, dan kota | Status `200 OK`, entitas terdeteksi lengkap beserta offset `start` dan `end` | Passed |
| 2 | **Empty Input Validation** | `title` atau `body` berupa string kosong (`""`) | Status `422 Unprocessable Entity` / `400 Bad Request` dengan pesan error validasi | Passed |
| 3 | **Punctuation & Special Characters** | Nama institusi mengandung simbol (misal: `"CIMB-Niaga/Bhd."`) | Model tidak memotong rentang karakter (*span boundary*) tanda baca | Passed |
| 4 | **Repeated Entities** | Entitas yang sama muncul berulang kali di dalam teks artikel | Semua kemunculan terdeteksi dengan indeks karakter unik masing-masing | Passed |
| 5 | **Long Text Document** | Artikel berita panjang (> 1.500 kata) | Berhasil diproses tanpa kendala memori maupun *timeout* API | Passed |

## 7. Tim Pengembang

- Role 1 **(Data & Anotasi)**: Pembersihan dataset, validasi teks artikel, penyiapan anotasi label, dan audit konsistensi ground truth.
- Role 2 **(Model & Evaluasi)**: Pelatihan/adaptasi pipeline spaCy ner_custom_v1, tuning hyperparameter, serta evaluasi metrik (Precision, Recall, F1).
- Role 3 **(Layanan & Deployment)**: Pembuatan backend FastAPI, UI frontend, penanganan span offset, dan otomasi pengujian API via Pytest/Colab.

## 8. Link Demo Aplikasi
https://drive.google.com/file/d/15ClKoZ1C9es2hMk3H5aYSF_kRmjijAlq/view?usp=sharing
