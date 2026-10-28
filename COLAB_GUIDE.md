# Panduan menjalankan pipeline di Google Colab

1. Upload/unzip folder `Maybank_NER_Service` ke `MyDrive`.
2. Masukkan file CSV Maybank ke folder `Maybank_NER_Service/data/raw/`. Jangan mengubah delimiter CSV asli.
3. Buka notebook Colab, jalankan:

```python
from google.colab import drive
drive.mount('/content/drive')
%cd /content/drive/MyDrive/Maybank_NER_Service
!pip install -r requirements.txt
!python -m spacy download en_core_web_sm
```

4. Jalankan satu per satu:

```python
!python src/prepare_data.py
!python src/make_annotation_template.py --n 100
```

5. Buka `data/annotations/annotation_template.jsonl` menggunakan editor teks yang menjaga JSONL, tinjau semua saran entitas, dan simpan sebagai `annotated.jsonl` dengan `reviewed: true` untuk setiap artikel yang benar-benar sudah diperiksa. Jangan menandai `true` tanpa memeriksa label dan offset.
6. Lanjutkan:

```python
!python src/validate_annotations.py
!python src/split_data.py --seed 42 --train 0.70 --val 0.15 --test 0.15
!python src/train_model.py --epochs 20
!python src/evaluate_model.py --split validation
!python src/evaluate_model.py --split test
```

7. Untuk API/web, download folder proyek ke komputer dan ikuti bagian menjalankan aplikasi pada README. Atau jalankan aplikasi dari Colab untuk percobaan, tetapi URL lokal Colab tidak sama dengan deployment publik.

**Jika CSV belum ada di `data/raw/`:** salin file yang kamu unggah ke folder tersebut terlebih dahulu. Skrip tidak mencari file di seluruh Drive secara otomatis karena struktur folder pengguna berbeda-beda.
