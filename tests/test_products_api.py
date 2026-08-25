from tests.conftest import make_product


def test_create_returns_201_with_generated_values(client):
    """POST returns 201, and the values PostgreSQL generated come back."""
    r = make_product(client, name="Paracetamol 500mg", quantity=40,
                     price="250.00", days_out=26)

    assert r.status_code == 201
    body = r.json()
    assert body["id"] is not None            #proves db.refresh ran
    assert body["created_at"] is not None    #same
    assert body["days_until_expiry"] == 26


def test_created_product_survives_into_a_separate_request(client):
    """The missing-commit test. Two requests, two sessions."""
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
    """Batch 4's correction: a typo must not become a default."""
    r = client.post("/products", json={
        "name": "Ibuprofen 400mg",
        "quantitiy": 25,                     #misspelled
        "price": "400.00",
        "expiry_date": "2026-07-30",
    })

    assert r.status_code == 422
    
def test_ids_start_at_one_every_time(client):
    r = make_product(client)
    assert r.json()["id"] == 1
    
    
def test_expiring_soon_route_is_reachable(client):
    """The route-order guard. Cheapest insurance in the suite."""
    r = client.get("/products/expiring-soon?days=30")
    assert r.status_code == 200          # NOT 422


def test_expiring_soon_window_boundaries(client):
    """Four assertions. The fourth is the one nobody writes."""
    make_product(client, name="Day 29", days_out=29)
    make_product(client, name="Day 30", days_out=30)
    make_product(client, name="Day 31", days_out=31)
    make_product(client, name="Yesterday", days_out=-1)

    names = [p["name"] for p in client.get("/products/expiring-soon?days=30").json()]

    assert "Day 29" in names
    assert "Day 30" in names           # the inclusive upper edge
    assert "Day 31" not in names
    assert "Yesterday" not in names    # THE LOWER BOUND


def test_expiring_soon_is_ordered_soonest_first(client):
    """Created in the WRONG order on purpose, so a missing ORDER BY fails."""
    make_product(client, name="Paracetamol 500mg", days_out=26)
    make_product(client, name="Amoxicillin 250mg", days_out=5)

    names = [p["name"] for p in client.get("/products/expiring-soon?days=30").json()]

    assert names == ["Amoxicillin 250mg", "Paracetamol 500mg"]


def test_expiring_soon_empty_is_good_news_not_an_error(client):
    """Nothing close to expiry is the BEST answer this endpoint can give."""
    make_product(client, name="Vitamin C 100mg", days_out=300)

    r = client.get("/products/expiring-soon?days=30")

    assert r.status_code == 200
    assert r.json() == []


def test_days_parameter_is_bounded(client):
    r_zero = client.get("/products/expiring-soon?days=0")
    r_huge = client.get("/products/expiring-soon?days=400")

    assert r_zero.status_code == 422
    assert r_huge.status_code == 422
    
    
def test_get_one_returns_the_product(client):
    created = make_product(client, name="Paracetamol 500mg").json()

    r = client.get(f"/products/{created['id']}")

    assert r.status_code == 200
    assert r.json()["name"] == "Paracetamol 500mg"


def test_get_missing_product_returns_404_not_500(client):
    r = client.get("/products/999")

    assert r.status_code == 404
    assert r.json()["detail"] == "Product not found"


def test_non_integer_id_returns_422(client):
    r = client.get("/products/abc")

    assert r.status_code == 422


def test_expiring_soon_is_still_reachable(client):
    """The route-order regression guard. Now it has something to guard against."""
    r = client.get("/products/expiring-soon?days=30")

    assert r.status_code == 200      # NOT 422
    
    
def test_patch_leaves_unsent_fields_alone(client):
    """THE test. The last two assertions are the real ones."""
    created = make_product(
        client, name="Paracetamol 500mg", quantity=40, price="250.00", days_out=26
    ).json()

    r = client.patch(f"/products/{created['id']}", json={"quantity": 38})
    assert r.status_code == 200

    after = client.get(f"/products/{created['id']}").json()
    assert after["quantity"] == 38                      # passes WITH the bug
    assert after["name"] == "Paracetamol 500mg"         # THE TEST
    assert after["price"] == "250.00"                   # THE TEST


def test_patch_missing_product_returns_404(client):
    r = client.patch("/products/999", json={"quantity": 5})

    assert r.status_code == 404


def test_patch_rejects_a_negative_quantity(client):
    created = make_product(client).json()

    r = client.patch(f"/products/{created['id']}", json={"quantity": -5})

    assert r.status_code == 422


def test_patch_rejects_an_undeclared_field(client):
    """extra='forbid' is what makes setattr in crud safe."""
    created = make_product(client).json()

    r = client.patch(f"/products/{created['id']}", json={"quantitiy": 38})

    assert r.status_code == 422
