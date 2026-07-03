from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from src.engine import SearchEngine

app = FastAPI()

# let the react frontend (different port) talk to this api
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# build the engine ONCE when the server boots
engine = SearchEngine()


@app.get("/search")
def search(q: str = Query(..., min_length=1, max_length=200)):
    return {"query": q, "results": engine.search(q, limit=10)}