from pathlib import Path
import os

import spacy
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "templates" / "index.html"
MAX_TEXT_LENGTH = 50000

app = FastAPI(
    title="Maybank Article NER Service",
    description="API untuk mendeteksi named entities pada artikel berita menggunakan spaCy.",
    version="1.0.0",
)

def load_pipeline():
    """Load custom spaCy model; use English baseline if available."""
    model_env = os.getenv("NER_MODEL_PATH")
    model_path = Path(model_env) if model_env else ROOT / "models" / "trained"
    if (model_path / "meta.json").exists():
        try:
            return spacy.load(model_path), model_path.name, True
        except Exception as exc:
            print(f"Gagal memuat model terlatih {model_path}: {exc}")
    try:
        return spacy.load("en_core_web_sm"), "en_core_web_sm (baseline; belum model terlatih)", False
    except OSError:
        return None, "model tidak tersedia", False

nlp, MODEL_NAME, IS_TRAINED = load_pipeline()

@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(TEMPLATE_PATH)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "trained_model": IS_TRAINED,
        "max_text_length": MAX_TEXT_LENGTH,
    }

@app.post("/extract-entities")
async def extract_entities(request: Request):
    if "application/json" not in request.headers.get("content-type", "").lower():
        return JSONResponse(status_code=400, content={"error": "Content-Type harus application/json."})
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Body harus berupa JSON object yang valid."})
    if not isinstance(data, dict):
        return JSONResponse(status_code=400, content={"error": "Body harus berupa JSON object yang valid."})

    title, body = data.get("title"), data.get("body")
    if not isinstance(title, str) or not isinstance(body, str):
        return JSONResponse(status_code=400, content={"error": "Field title dan body wajib berupa string."})
    title, body = title.strip(), body.strip()
    if not title:
        return JSONResponse(status_code=400, content={"error": "Judul artikel tidak boleh kosong."})
    if not body:
        return JSONResponse(status_code=400, content={"error": "Isi artikel tidak boleh kosong."})

    text = title + "\n" + body
    if len(text) > MAX_TEXT_LENGTH:
        return JSONResponse(
            status_code=400,
            content={"error": f"Teks gabungan terlalu panjang. Batas {MAX_TEXT_LENGTH} karakter."},
        )
    if nlp is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Model NER belum tersedia. Instal en_core_web_sm dan/atau letakkan model terlatih di models/trained/."},
        )

    doc = nlp(text)
    entities = [
        {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
        for ent in doc.ents
    ]
    return {
        "entities": entities,
        "meta": {
            "entity_count": len(entities),
            "model": MODEL_NAME,
            "trained_model": IS_TRAINED,
            "offset_reference": "title + newline + body",
        },
    }
