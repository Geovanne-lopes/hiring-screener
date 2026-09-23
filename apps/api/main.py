from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from persistencia.db import init_db
from routers import avaliacao, importacao, projetos, triagem

app = FastAPI(title="Screener", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(projetos.router)
app.include_router(importacao.router)
app.include_router(triagem.router)
app.include_router(avaliacao.router)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/config/llm")
def config_llm():
    import config as cfg

    return {
        "configurada": cfg.llm_configurada(),
        "modelo": cfg.llm_model(),
        "baseUrlDefinida": bool(cfg.llm_base_url()),
    }


@app.get("/api/pedido-trajetoria")
def pedido_trajetoria():
    return {
        "acao": "avaliar_trajetoria",
        "habilitada": False,
        "mensagem": "Avaliar trajetória vem em sprint posterior.",
    }
