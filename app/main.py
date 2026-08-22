from fastapi import FastAPI
from app.routers import products


app = FastAPI(
    title="PharmShelf",
    description="A pharmacy stock API. Tracks products and flags what is expiring soon.",
    version="1.0.0",
)

app.include_router(products.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}