# Backend API para Librebria
# FastAPI + MongoDB Atlas

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import books, companies
from database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Librebria API",
    description="API para consultas de la base de datos Librebria",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # URLs del frontend
    allow_credentials=True,
    allow_methods=["GET"],  # Solo lectura
    allow_headers=["*"],
)

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Incluir routers
app.include_router(books.router, prefix="/api/books", tags=["Books"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])

# Ruta raíz
@app.get("/")
async def root():
    return {
        "message": "Bienvenido a Librebria API",
        "docs": "/docs",
        "endpoints": {
            "books": "/api/books",
            "companies": "/api/companies"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
