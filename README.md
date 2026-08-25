# PharmShelf

PharmShelf keeps a pharmacy's stock list — what's on the shelf and how much of it — and answers the question a paper list can't: which drugs are about to expire, while there's still time to do something about it.

**Live API:** https://pharmshelf-api.onrender.com/docs

> Hosted on free tiers, so the first request after a period of inactivity can take up to a minute while the web service and the database wake. Subsequent requests are fast.

---

## What It Does

It's the API behind a stock screen: a front-end or a script can add a product, adjust a count when stock moves, search the shelf by name, and ask for everything expiring inside a given window.

**Key features:**

- Add, list, update, and remove products, each with a name, a quantity, a price, and an expiry date
- Ask for everything expiring within a given number of days, returned soonest-first
- Filter the list by expiry status or search it by name, with both filters combining
- Treats "expired" as a comparison against today rather than a stored flag, so a row can never claim to be valid after its date has passed
- Stores prices as exact decimals rather than floating-point numbers, so totals across the shelf add up
- Enforces a floor of zero on stock in both the API and the database, so an impossible quantity is refused even by a hand-written SQL statement
- Versions schema changes through migrations rather than recreating tables, so the schema can change without dropping data

---

## Why I Built This

I wanted a project where the data goes stale on its own. Every drug has an expiry date, so a row that was correct when written becomes wrong simply because days passed — which forces "expired" to be a query rather than a column, and makes a real SQL date comparison the centre of the project rather than an afterthought.

It's also the first database project in a sequence I'm working toward: the same store-and-query muscle that a document Q&A system uses for its chunks table, with a different sort order.

---

## API

| Method | Path | Does | Success | Errors |
|---|---|---|---|---|
| `GET` | `/health` | Liveness check; touches no database | `200` | — |
| `POST` | `/products` | Add a product | `201` | `422` |
| `GET` | `/products` | List the shelf; `?search=` and `?expired=` | `200` | `422` |
| `GET` | `/products/expiring-soon` | Products expiring within `?days=` (default 30), soonest first | `200` | `422` |
| `GET` | `/products/{id}` | One product | `200` | `404`, `422` |
| `PATCH` | `/products/{id}` | Change the fields sent; returns the full product | `200` | `404`, `422` |
| `DELETE` | `/products/{id}` | Remove a product | `204` | `404`, `422` |

**Query parameters**

| Parameter | Endpoint | Type | Default | Effect |
|---|---|---|---|---|
| `search` | `GET /products` | string | none | Name contains, case-insensitive, matches anywhere |
| `expired` | `GET /products` | boolean | none — **all** | `true` = expired only; `false` = not expired only; omitted = no filter |
| `days` | `expiring-soon` | integer, 1–365 | `30` | How far ahead to look |

**Errors** return `{"detail": ...}`. For `404` and other single-cause errors `detail` is a string; for `422` validation errors it is FastAPI's standard list of per-field objects, because a validation failure can name several fields at once and a string cannot.

**All endpoints are public.** No authentication — see Known Limitations.

---

## Data Model

One entity, seven fields:

```
products
─────────────────────────────────────────────────────────────
  id            INTEGER        PK, auto-increment
  name          VARCHAR(200)   NOT NULL
  quantity      INTEGER        NOT NULL, default 0, CHECK >= 0
  price         NUMERIC(10,2)  NOT NULL, CHECK >= 0
  expiry_date   DATE           NOT NULL, INDEXED
  created_at    TIMESTAMPTZ    NOT NULL, server default now()
  updated_at    TIMESTAMPTZ    NOT NULL, server default now(),
                               updated on write
```

No relationships, no foreign keys, and one index — on `expiry_date`, which is both filtered and sorted by the expiring-soon endpoint, so a single index serves both.

*(The database also contains `alembic_version`, a single-row table Alembic maintains to record which migration has been applied. It is part of the database, not part of the data model.)*

**Entities identified in the domain and deliberately not built:** batch, supplier, category, stock movement. Reasons are in Known Limitations.

---

## Architecture

```
Request
   │
   ▼
routers/products.py     HTTP in, HTTP out. Translates results
   │                    and errors into status codes.
   ▼
crud/product.py         Every query and write. Knows SQLAlchemy,
   │                    never HTTP. Returns objects or None.
   ▼
models/product.py       The table's shape.
   │
   ▼
database.py             The engine, the session factory, and
                        get_db — the only place a session is made.

schemas/product.py      Request and response shapes. Read by
                        routers only.
config.py               Values everything reads. Never acts.
```

Grouped by layer rather than by feature, because there is one entity — with folders rather than flat modules, so a second entity has somewhere to go without a refactor.

Two rules hold the shape: **no SQLAlchemy queries in routers**, and **no `HTTPException` in `crud/`**. The second is what lets the query layer be called from a script or a test with no web server involved.

---

## Tech Stack

**Backend:** FastAPI, Uvicorn, Pydantic v2
**Database:** PostgreSQL on Neon, SQLAlchemy 2.0, psycopg 3, Alembic
**Configuration:** pydantic-settings reading `DATABASE_URL` from the environment
**Testing:** pytest, httpx, against a separate Neon branch
**Deployment:** Render free tier, with migrations run before the app serves

**One external service: the database.** Every other dependency is a library installed with pip, and exactly two files know the service exists — `config.py` reads the connection string, `database.py` opens the connection. Nothing else in the codebase knows which database it is talking to or where it is.

PostgreSQL was chosen over SQLite despite SQLite requiring no service at all, because SQLite does not enforce `NUMERIC` the way PostgreSQL does and has no true `DATE` type — and exact decimals and date arithmetic are the two things this project is actually about.

---

## Running It Locally

**Requirements:** Python 3.11+, and a Neon account with a project created.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

copy .env.example .env          # then paste your Neon URL into it
alembic upgrade head
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs

**A `.env` file is required.** Copy `.env.example` to `.env` and put your own Neon connection string in `DATABASE_URL`. `.env` is git-ignored and must stay that way — a connection string contains a password, and a password that reaches commit history can only be fixed by resetting it at the database.

Paste the string exactly as Neon gives it. The settings layer rewrites the `postgresql://` prefix to `postgresql+psycopg://` itself, so the same raw string works locally and on the host.

**Run migrations before starting the app.** The repository contains the models and the migration chain; it does not contain the tables.

---

## Testing

**36 tests, run against a separate Neon branch rather than the development database.**

```bash
pytest -v
```

The suite is split in two. `tests/test_products_crud.py` calls the query layer directly with a session and no HTTP at all, which is possible because the CRUD layer never raises `HTTPException` — it returns objects or `None`, and the router does the translating. `tests/test_products_api.py` goes through the endpoints with a test client.

**What the tests are mostly for.** A handful assert the happy path, which is the part you can check by eye in `/docs`. The rest assert failure and edge behaviour, which you cannot: that a negative quantity is rejected, that a product expiring exactly at the window edge appears and one day past it does not, that already-expired stock is excluded from "expiring soon" rather than sitting permanently at the top of it, that the list comes back sorted soonest-first, and that a partial update leaves the fields you did not send untouched.

**Isolation.** Each test truncates the products table afterwards and resets the id sequence, and every request inside a test gets a fresh session. That last part is deliberate and costs a little speed: the faster approach — wrapping each test in a transaction and rolling it back — shares one session across a test's requests, and a shared session returns its own staged rows on a subsequent read. That would make a missing `commit()` invisible, which is the single most common bug in this kind of project and the one the suite most needs to catch.

**Nothing is mocked.** The database is not, because how the code talks to PostgreSQL — commits, constraints, types — is exactly what is under test, and a fake would answer every one of those questions correctly while hiding every one of the bugs. The clock is not either: the query layer takes today's date as an argument rather than reading it, so tests pass the date they want to reason about, and the API tests build their fixture data relative to today instead of hard-coding a date that would expire.

---

## Engineering Decisions

**Product and batch are one table, and that makes the expiry report wrong for multi-batch stock.**
A real pharmacy holds the same drug from several deliveries with different expiry dates, so quantity and expiry belong to a batch rather than to a product. Modelling that means a second table, a join, and an aggregate for every quantity read — roughly four to six hours, and it converts a single-table project into a relationship project, which is not what this one set out to teach. The cost is specific and it is not a performance cost: for a product with two deliveries, the expiring-soon endpoint reports the whole quantity against the earliest date, so it says forty boxes are at risk when thirty are. That threshold is not a row count — it is the second delivery of anything, which in a working pharmacy is week one. The current workaround, entering the drug twice under the same name, is also what forbids a unique constraint on the name column, and untangling those duplicate rows later is manual. Any real user is the condition that changes this; there is no version of a production pharmacy system that tracks one expiry date per product.

**Stock is set to an absolute value rather than adjusted by an amount, which silently loses concurrent updates.**
`PATCH /products/{id}` takes the new quantity, so the caller computes it from a value it read earlier. If two people dispense from the same drug in the same short window, both compute from the same starting number and the second write overwrites the first — seven boxes leave the shelf, the row records five, and both requests return 200. The discrepancy is invisible until a physical count, by which point nobody can say which update was lost. The threshold is not volume but concurrency: the bug needs exactly two simultaneous users and no particular number of rows. It is defensible here because the demonstrated use is one developer and a reviewer, and because the fix is purely additive — a `POST /products/{id}/dispense` performing `quantity = quantity - n` in a single statement, so the arithmetic happens at the database and nobody holds a stale number. That change is the first item on the roadmap. There is also a modelling cost worth naming: a request carrying "38" has discarded the reason, so a stock-movement ledger could not record it even if one existed.

**Search matches a substring anywhere in the name, which is forgiving and cannot use an index.**
A technician typing three letters at a counter does not know whether the drug name starts with them and is not thinking about capitals, so `ILIKE '%para%'` is the behaviour the moment calls for. A B-tree index answers "starts with" but not "contains" — with a wildcard at the front there is no starting point in an alphabetical order — so every search reads every row, and the name column is deliberately not indexed, because an index that cannot be used is pure write cost. The prefix alternative would be indexed and would silently miss any drug whose brand name comes first, returning a confident empty list that looks identical to "we don't stock it". Full-text search is more powerful and less suitable: it matches whole words, and "para" is not a word. The scan costs well under ten milliseconds at a few hundred products, which is invisible next to the network round trip, and it starts to matter somewhere around fifty thousand rows — a threshold a single pharmacy's catalogue of one to three thousand products will not reach. The upgrade path is a trigram index, which makes the same query indexable with no application change at all, and a type-ahead search firing on every keystroke would trigger it sooner than growth would.

**One entity is described by four separate classes, which duplicates every field declaration.**
The table model, the create schema, the update schema, and the read schema each declare the name and the price, so a fifth field means four edits and a constraint tightened in one place and not another diverges silently. Merging them — with SQLModel, where one class is both the table and the API contract — would remove that entirely. It is not chosen because the shapes genuinely differ rather than coincidentally: the create schema has no `id`, because a caller who could set one could overwrite an arbitrary row; the update schema has every field optional, which is what lets `PATCH` mean "leave this alone"; and the read schema carries two fields the table does not have, whether the product is expired and how many days remain. Merging is also the one option here that is expensive to undo, where extracting a shared base class later is a mechanical half-hour. At four fields the duplication is sixteen lines and worth paying; a second entity, or a fifth field, is the point at which a shared base earns its indirection.

**Request schemas reject fields they do not declare.**
Pydantic's default is to ignore unknown keys, which is safe for a caller trying to set `id` — the field is simply discarded and the database assigns the real one. It is not safe for a typo: a body containing `quantitiy` rather than `quantity` has the misspelling silently dropped, and because quantity defaults to zero for a catalogued-but-unstocked product, the API returns `201 Created` for a product recorded as having none. Two decisions that were each correct alone combine into a silent wrong value. `extra="forbid"` turns that into a `422` naming the offending key. The cost is a stricter API than most public ones — a client sending a harmless extra field is rejected — which is acceptable here because the only intended client is the front-end built alongside it.

---

## Known Limitations

- **One expiry date per product.** Stock received in different deliveries cannot be distinguished, so "expiring soon" reports the whole quantity against the earliest date. A real system models batches as separate rows under a product, each with its own quantity and expiry, and queries batches rather than products. This is the largest simplification in the model and the first structural change I would make.

- **Stock is set, not adjusted.** `PATCH` takes an absolute quantity, so two concurrent updates silently lose one — both callers compute a new value from the same starting number and the second write overwrites the first. The fix is a delta operation performed in a single statement, so the arithmetic happens at the database rather than in the caller's head.

- **No authentication and no per-pharmacy scoping.** Any caller can read or permanently delete any product, and because deletion is a hard delete with no movement history, nothing records that the product existed. PharmShelf is scoped as a single-pharmacy service behind a front-end that checks identity once, at the edge. This would be the first change before exposing it more widely.

- **No pagination.** `GET /products` returns every row in one response. That is fine at a few hundred products and would need cursor or offset pagination beyond that. It is absent from all three list endpoints uniformly, so no caller has to remember which ones page.

- **No stock-movement history.** The row holds only the current number, with no record of what changed it or when. A movement ledger would make quantity derivable rather than stored, and would supply the "what" and "when" of an audit trail.

- **A product can be deleted while stock is on hand.** Deleting the row does not delete the boxes. Whether deletion should be refused when quantity is above zero is a workflow policy I would want a real pharmacy to set rather than guess at.

- **Nothing is pushed.** The API answers "what expires soon" correctly and instantly, but only when asked. Warning someone unprompted needs a scheduler and a delivery channel, which are running services rather than code. The project moves the problem from unanswerable to unasked.

- **Every product must have an expiry date.** The column is `NOT NULL`, so the model covers drugs and not non-expiring pharmacy items such as devices or dressings. Making it nullable would require every expiry comparison to handle `NULL` explicitly, since `NULL` is excluded by a comparison and by its negation alike — a nullable expiry would silently drop rows from both `?expired=true` and `?expired=false`.

- **Concurrent updates are not tested.** Reproducing a lost update needs two genuinely overlapping requests, and the test client is synchronous, so a test would pass whether or not the bug were present. The behaviour is documented above and the fix is the first item on the roadmap.

- **Migrations are not verified against the models.** The test suite builds its schema directly from the models while deployment applies the Alembic chain, so a migration that drifted from a model would leave the suite passing and the deployment broken. Running `alembic downgrade base && alembic upgrade head` against the test branch before a release catches it; doing that automatically on every push is what CI would be for.

**Next additions, in order:** a delta-based stock adjustment, then batch tracking, then a stock-movement history, then authentication, then per-pharmacy scoping.