from fastapi import APIRouter
from app.api.v1.endpoints import auth, diagnosis, breast_cancer, statistics, stroke

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(diagnosis.router, prefix="/diagnosis", tags=["diagnosis"])
api_router.include_router(breast_cancer.router, prefix="/breast-cancer", tags=["breast-cancer"])
api_router.include_router(stroke.router, prefix="/stroke", tags=["stroke"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["statistics"])