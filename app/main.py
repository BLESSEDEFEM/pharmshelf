from fastapi import FastAPI


app = FastAPI(
    title="PharmShelf",
    description="A pharmacy stock API. Tracks products and flags what is expiring soon.",
    version="1.0.0",
)

@app.get("/health")
def health_check():
    return {"status": "ok"}