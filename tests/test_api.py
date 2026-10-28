import sys
from pathlib import Path

from fastapi.testclient import TestClient
import spacy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import app as app_module


def setup_client(monkeypatch):
    nlp = spacy.blank("en")
    ruler = nlp.add_pipe("entity_ruler")
    ruler.add_patterns([
        {"label": "ORG", "pattern": "Maybank"},
        {"label": "GPE", "pattern": "Malaysia"},
        {"label": "PERSON", "pattern": "Aisha Tan"},
    ])
    monkeypatch.setattr(app_module, "nlp", nlp)
    monkeypatch.setattr(app_module, "MODEL_NAME", "test-entity-ruler")
    monkeypatch.setattr(app_module, "IS_TRAINED", True)
    return TestClient(app_module.app)


def test_valid_request_returns_entities_and_offsets(monkeypatch):
    client = setup_client(monkeypatch)
    response = client.post("/extract-entities", json={"title": "Maybank update", "body": "Aisha Tan visited Malaysia."})
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["entity_count"] == 3
    combined = "Maybank update\nAisha Tan visited Malaysia."
    for ent in data["entities"]:
        assert combined[ent["start"]:ent["end"]] == ent["text"]


def test_empty_title_rejected(monkeypatch):
    response = setup_client(monkeypatch).post("/extract-entities", json={"title": "  ", "body": "Some article body"})
    assert response.status_code == 400


def test_empty_body_rejected(monkeypatch):
    response = setup_client(monkeypatch).post("/extract-entities", json={"title": "A title", "body": ""})
    assert response.status_code == 400


def test_non_string_field_rejected(monkeypatch):
    response = setup_client(monkeypatch).post("/extract-entities", json={"title": ["wrong"], "body": "Some body"})
    assert response.status_code == 400


def test_malformed_json_rejected(monkeypatch):
    response = setup_client(monkeypatch).post("/extract-entities", content="{bad json", headers={"Content-Type": "application/json"})
    assert response.status_code == 400


def test_long_text_rejected(monkeypatch):
    response = setup_client(monkeypatch).post("/extract-entities", json={"title": "Title", "body": "x" * 50000})
    assert response.status_code == 400


def test_unicode_and_repeated_entities_keep_exact_offsets(monkeypatch):
    response = setup_client(monkeypatch).post(
        "/extract-entities",
        json={"title": "Maybank — café update", "body": "Maybank met Aisha Tan in Malaysia; Maybank will return."},
    )
    assert response.status_code == 200
    data = response.json()
    combined = "Maybank — café update\nMaybank met Aisha Tan in Malaysia; Maybank will return."
    assert all(combined[e["start"]:e["end"]] == e["text"] for e in data["entities"])
    assert sum(e["text"] == "Maybank" for e in data["entities"]) == 3


def test_home_page_loads(monkeypatch):
    response = setup_client(monkeypatch).get("/")
    assert response.status_code == 200
    assert b"Maybank Article NER Service" in response.content
