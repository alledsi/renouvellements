from fastapi import FastAPI
from app.api import proposals
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Renouvellement Crédit API")
app.include_router(proposals.router, prefix="/proposals", tags=["proposals"])



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.0.122:4884"],  # ou "*" pour test local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"ok": True}
