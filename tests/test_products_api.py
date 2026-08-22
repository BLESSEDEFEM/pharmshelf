from tests.conftest import make_product


def test_create_returns_201_with_generated_values(client):
    """POST returns 201, and the values PostgreSQL generated come back."""
    r = make_product(client, name="Paracetamol 500mg", quantity=40,
                     price="250.00", days_out=26)

    assert r.status_code == 201
    body = r.json()
    assert body["id"] is not None            # ⭐ proves db.refresh ran
    assert body["created_at"] is not None    # ⭐ same
    assert body["days_until_expiry"] == 26


def test_created_product_survives_into_a_separate_request(client):
    """⭐⭐ The missing-commit test. Two requests, two sessions."""
    make_product(client, name="Paracetamol 500mg")

    r = client.get("/products")              # ← a SEPARATE request

    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "Paracetamol 500mg"


def test_empty_list_is_200_with_an_empty_array(client):
    """An empty collection is an answer, not a failure."""
    r = client.get("/products")

    assert r.status_code == 200
    assert r.json() == []


def test_undeclared_field_is_rejected(client):
    """⭐ Batch 4's correction: a typo must not become a default."""
    r = client.post("/products", json={
        "name": "Ibuprofen 400mg",
        "quantitiy": 25,                     # ⚠️ misspelled
        "price": "400.00",
        "expiry_date": "2026-07-30",
    })

    assert r.status_code == 422
    
def test_ids_start_at_one_every_time(client):
    r = make_product(client)
    assert r.json()["id"] == 1