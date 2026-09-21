from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

# 加载 .env 文件
load_dotenv(Path(__file__).parent.parent / ".env")
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import agent as agent_router
from app.routers import auth as auth_router
from app.routers import calc as calc_router
from app.routers import cases as cases_router
from app.routers import document as document_router
from app.routers import evidence as evidence_router
from app.routers import labor as labor_router
from app.routers import law_search as law_search_router
from app.routers import case_search as case_search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="多类劳动者劳动仲裁辅助系统", version="1.0.0", lifespan=lifespan)

# CORS 安全配置：不允许通配符 + credentials 的组合
cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api")
app.include_router(labor_router.router, prefix="/api")
app.include_router(cases_router.router, prefix="/api")
app.include_router(evidence_router.router, prefix="/api")
app.include_router(document_router.router, prefix="/api")
app.include_router(agent_router.router, prefix="/api")
app.include_router(calc_router.router, prefix="/api")
app.include_router(law_search_router.router, prefix="/api")
app.include_router(case_search_router.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "ui_meta": {"pulse": False}}
