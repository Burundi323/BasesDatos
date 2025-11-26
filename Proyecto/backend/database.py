# Configuración de conexión a MongoDB Atlas
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

class Database:
    client: AsyncIOMotorClient = None
    
db = Database()

async def connect_to_mongo():
    """Conectar a MongoDB Atlas"""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    print("✅ Conectado a MongoDB Atlas")

async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    db.client.close()
    print("❌ Conexión a MongoDB cerrada")

def get_database():
    """Obtener la base de datos Librebria"""
    return db.client[settings.DATABASE_NAME]

def get_books_collection():
    """Obtener colección de libros"""
    return get_database()["Books"]

def get_companies_collection():
    """Obtener colección de compañías"""
    return get_database()["Companies"]
