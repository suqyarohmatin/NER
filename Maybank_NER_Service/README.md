# Maybank Article NER Service

Proyek ini merupakan prototipe **Named Entity Recognition (NER)** untuk artikel media online Maybank. Proyek mengikuti studi kasus: profil data, anotasi rentang teks, pembagian train/validation/test berdasarkan identitas artikel, adaptasi model NER, evaluasi exact-span, API JSON, antarmuka web, dan pengujian.

> **Penting:** model `en_core_web_sm` yang digunakan sebagai baseline terutama ditujukan untuk bahasa Inggris. Proyek ini memulai eksperimen dengan artikel berbahasa Inggris (`language` berisi `en`). Artikel Melayu, Mandarin, atau bahasa lain tidak digunakan dalam pelatihan awal dan perlu model/anotasi yang sesuai jika ingin didukung secara serius.
>
> **Penting 2:** hasil prediksi model hanya saran anotasi. Periksa dan koreksi sendiri label serta offset. Jangan menganggap kolom `entities` pada CSV sebagai label benar tanpa validasi.

## 1. Struktur folder

```text
Maybank_NER_Service/
├── README.md
├── requirements.txt
├── .gitignore
├── COLAB_GUIDE.md
├── data/
│   ├── raw/                 # masukkan CSV asli di sini (tidak ikut dibagikan)
│   ├── processed/           # hasil pembersihan
│   ├── annotations/         # anotasi yang sudah ditinjau manusia
│   └── splits/              # train.jsonl, validation.jsonl, test.jsonl
├── models/trained/          # model hasil pelatihan (dibuat otomatis)
├── reports/                 # laporan audit dan evaluasi
├── src/
│   ├── prepare_data.py
│   ├── make_annotation_template.py
│   ├── validate_annotations.py
│   ├── split_data.py
│   ├── train_model.py
│   ├── evaluate_model.py
│   └── app.py
├── templates/index.html
└── tests/test_api.py
```

CSV mentah dan model hasil training sengaja tidak disertakan di arsip proyek. Letakkan file CSV milikmu di `data/raw/`; jangan membuat salinan kedua artikel di repository GitHub.

## 2. Label yang dipakai

| Label | Makna | Contoh umum |
|---|---|---|
| `PERSON` | Nama orang | nama direktur atau pejabat |
| `ORG` | Organisasi/perusahaan | Maybank, CIMB Group |
| `GPE` | Negara/kota/wilayah politik | Malaysia, Kuala Lumpur |
| `LOC` | Lokasi geografis lain | nama fitur geografis |
| `DATE` | Tanggal/waktu | 7 October 2026 |
| `EVENT` | Peristiwa bernama | nama acara khusus |

Gunakan label yang konsisten. Model baseline spaCy mungkin tidak mengenali `EVENT`; label ini dapat dipelajari jika contoh beranotasi cukup. Jangan memberi label `EVENT` pada setiap kata umum yang sekadar menyebut kejadian.

## 3. Menyiapkan data

1. Buat folder `data/raw/`.
2. Salin semua CSV Maybank yang menjadi bagian tugas ke folder tersebut. CSV harus dipisahkan titik koma (`;`).
3. Instal dependency dan model baseline:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. Audit dan bersihkan data:

```bash
python src/prepare_data.py
```

Skrip menampilkan jumlah baris awal, duplikasi, judul/isi kosong, distribusi bahasa, dan jumlah artikel unik. Hasil tersimpan di `data/processed/articles_clean.csv` dan `reports/data_audit.json`.

Skrip menghapus apostrof tunggal di awal nilai jika ditemukan karena ekspor yang diberikan memiliki awalan tersebut. Skrip menghapus duplikasi `original_id` dengan mempertahankan kemunculan pertama. Periksa laporan audit dan jelaskan keputusan ini dalam laporan tugas.

## 4. Membuat dan meninjau anotasi

Jalankan:

```bash
python src/make_annotation_template.py --n 100
```

File `data/annotations/annotation_template.jsonl` berisi hingga 100 artikel bahasa Inggris dan saran entitas dari model baseline. Setiap artikel memiliki `original_id`, `source_name`, `title`, `body`, `text`, `entities`, dan `reviewed`.

**Wajib ditinjau manusia:**

- Periksa apakah setiap span benar-benar entitas.
- Tambahkan entitas yang terlewat dan hapus prediksi salah.
- Pastikan `start` dan `end` adalah offset karakter pada `text` gabungan (`title + "\n" + body`), `start` inklusif dan `end` eksklusif.
- Periksa ejaan, tanda baca, dan label.
- Setelah seluruh entitas untuk artikel tersebut diperiksa, ubah `reviewed` menjadi `true`.
- Simpan hasil sebagai `data/annotations/annotated.jsonl`.

Contoh satu baris JSONL (satu objek JSON per baris):

```json
{"original_id":"id-artikel-1","source_name":"media.example","title":"Maybank appoints Aisha Tan","body":"Maybank said Aisha Tan will lead the team in Malaysia.","text":"Maybank appoints Aisha Tan\nMaybank said Aisha Tan will lead the team in Malaysia.","entities":[{"start":0,"end":7,"label":"ORG"},{"start":17,"end":26,"label":"PERSON"},{"start":27,"end":34,"label":"ORG"},{"start":40,"end":49,"label":"PERSON"},{"start":72,"end":80,"label":"GPE"}],"reviewed":true}
```

Contoh tersebut hanya menunjukkan format. **Offset contoh wajib dihitung/ditinjau berdasarkan teks persisnya; jangan menyalin contoh ini sebagai label dataset.**

Untuk evaluasi yang layak, anotasi setidaknya 70 artikel bila memungkinkan, agar split test 15% dapat mendekati atau melebihi 10 artikel. Pastikan test mencakup nama berulang, tanda baca, artikel tanpa entitas, dan kasus sulit. Jangan memakai hasil test untuk mengubah model atau aturan setelah evaluasi final.

## 5. Validasi anotasi dan membagi data

```bash
python src/validate_annotations.py
python src/split_data.py --seed 42 --train 0.70 --val 0.15 --test 0.15
```

Skrip hanya menerima artikel `reviewed: true`, memvalidasi offset, dan membagi berdasarkan `original_id`. Hasil tersimpan di `data/splits/train.jsonl`, `validation.jsonl`, dan `test.jsonl`.

Jika skrip memberi tahu ada offset tidak valid, perbaiki JSONL. Jangan melanjutkan training sebelum validasi berhasil.

## 6. Melatih/adaptasi model

```bash
python src/train_model.py --epochs 20
```

Skrip memulai dari model pretrained `en_core_web_sm`, mengadaptasi komponen NER memakai anotasi train, memilih model terbaik berdasarkan exact-span F1 pada validation, lalu menyimpan model ke `models/trained/`. Training dari dataset kecil bisa tidak stabil; catat jumlah dokumen/span, epoch, seed, durasi, dan label yang jarang muncul.

## 7. Evaluasi baseline dan model terlatih

```bash
python src/evaluate_model.py --split validation
python src/evaluate_model.py --split test
```

Laporan tersimpan di `reports/evaluation_validation.json` dan `reports/evaluation_test.json`. Metrik menggunakan **exact-span matching**: prediksi harus memiliki batas awal, batas akhir, dan label yang sama dengan anotasi. Laporan berisi precision, recall, F1 keseluruhan, metrik per label, perbandingan baseline vs trained, serta contoh false positive/false negative.

Jalankan evaluasi test setelah model final dipilih. Jangan mengubah model berdasarkan hasil test; bila melakukan perubahan, buat test set baru atau jelaskan keterbatasan eksperimen.

## 8. Menjalankan aplikasi web lokal

```bash
python -m uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload
```

Buka `http://127.0.0.1:8000` di browser. Dokumentasi API otomatis tersedia di `http://127.0.0.1:8000/docs` dan pemeriksaan layanan di `http://127.0.0.1:8000/health`. Jika `models/trained/` belum tersedia, aplikasi memakai baseline `en_core_web_sm` dan menandainya di metadata. Untuk demo final tugas, latih model terlebih dahulu agar layanan menggunakan model terlatih yang dievaluasi.

### API

`POST /extract-entities`

Request JSON:

```json
{
  "title": "Maybank expands digital services",
  "body": "Maybank announced a new service in Malaysia."
}
```

Respons berisi `entities` (text, label, start, end) dan `meta` (jumlah entitas, model, apakah model terlatih). Offset dihitung pada teks gabungan `title + "\n" + body`.

Contoh curl:

```bash
curl -X POST http://127.0.0.1:8000/extract-entities \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Maybank expands digital services\",\"body\":\"Maybank announced a new service in Malaysia.\"}"
```

API menolak JSON rusak, title/body kosong, title/body bukan string, dan input yang total panjangnya melebihi batas 50.000 karakter.

## 9. Pengujian

```bash
pytest -q
```

Tes memeriksa input normal, title kosong, body kosong, tipe data salah, JSON tidak valid, teks terlalu panjang, Unicode, dan offset entitas berulang.

## 10. Hal yang harus dilaporkan

- jumlah CSV dan baris yang dibaca;
- jumlah duplikasi dan baris yang dihapus;
- jumlah judul/body kosong dan distribusi bahasa;
- jumlah dokumen dan span untuk train/validation/test;
- skema label dan cara anotasi diperiksa;
- model baseline, model terlatih, versi dependency, seed, epoch, durasi;
- precision, recall, F1 exact-span keseluruhan dan per label pada validation dan test;
- baseline vs trained;
- minimal tiga contoh kesalahan FP/FN;
- apakah test pernah digunakan untuk tuning;
- batasan bahasa, ketidakseimbangan label, bias, hak cipta, dan penggunaan teks artikel.

## Batasan

- `en_core_web_sm` adalah model bahasa Inggris; hasil untuk bahasa Melayu/Mandarin tidak dijamin.
- Model tidak akan otomatis menjadi akurat hanya karena kode berhasil berjalan. Kualitas sangat bergantung pada anotasi yang benar dan cukup beragam.
- Model pretrained dan saran otomatis tidak menggantikan tinjauan manusia untuk label evaluasi.


## Menjalankan versi FastAPI

Aktifkan virtual environment, instal dependensi, lalu jalankan `python -m uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload`. Buka `http://127.0.0.1:8000` untuk UI, `/docs` untuk Swagger UI, dan `/health` untuk status model. API tetap menyediakan `POST /extract-entities` dengan format JSON yang sama.
