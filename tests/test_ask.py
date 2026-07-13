from __future__ import annotations


def test_ask_without_relevant_context_says_dont_know(client):
    resp = client.post("/ask", json={"question": "Qual é a capital da França?", "profile": "internal"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["confidence"] == "none"
    assert body["sources"] == []


def test_internal_profile_can_see_internal_document(client):
    resp = client.post(
        "/ask",
        json={"question": "Quais formatos o Serviço Vega aceita?", "profile": "internal"},
    )
    assert resp.status_code == 200
    body = resp.json()
    titles = {s["title"] for s in body["sources"]}
    assert "Serviço Vega" in titles
    assert body["confidence"] != "none"
    assert body["answer"].strip()


def test_public_profile_cannot_see_internal_document(client):
    resp = client.post(
        "/ask",
        json={"question": "Quais formatos o Serviço Vega aceita?", "profile": "public"},
    )
    assert resp.status_code == 200
    body = resp.json()
    titles = {s["title"] for s in body["sources"]}
    assert "Serviço Vega" not in titles
    assert body["confidence"] == "none"