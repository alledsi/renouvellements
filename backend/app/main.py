from fastapi import FastAPI
from app.api import proposals
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Renouvellement Crédit API")
app.include_router(proposals.router, prefix="/proposals", tags=["proposals"])



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],  # ou "*" pour test local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"ok": True}
