# Backend API para Universidad
# FastAPI + MongoDB (pymongo) + MySQL

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import queries_mongo, queries_mysql
from database import connect_to_mongo, close_mongo_connection, connect_to_mysql, close_mysql_connection

app = FastAPI(
    title="Universidad API",
    description="API para consultas de la base de datos Universidad - MongoDB y MySQL",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_db_client():
    # MongoDB (síncrono)
    connect_to_mongo()
    # MySQL (asíncrono)
    await connect_to_mysql()

@app.on_event("shutdown")
async def shutdown_db_client():
    close_mongo_connection()
    await close_mysql_connection()

# Incluir routers
app.include_router(queries_mongo.router, prefix="/api/mongo", tags=["Consultas MongoDB"])
app.include_router(queries_mysql.router, prefix="/api/mysql", tags=["Consultas MySQL"])

# Ruta raíz
@app.get("/")
async def root():
    return {
        "message": "Universidad API - MongoDB y MySQL",
        "docs": "/docs",
        "endpoints": {
            "mongodb": "/api/mongo/consulta/{1-10}",
            "mysql": "/api/mysql/consulta/{1-10}"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
