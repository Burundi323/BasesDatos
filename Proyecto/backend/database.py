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
    """Obtener la base de datos Universidad"""
    return db.client[settings.DATABASE_NAME]

# Colecciones
def get_collection(name: str):
    return get_database()[name]

def get_students():
    return get_database()["Student"]

def get_courses():
    return get_database()["Course"]

def get_instructors():
    return get_database()["Instructor"]

def get_sections():
    return get_database()["Section"]

def get_takes():
    return get_database()["Takes"]

def get_teaches():
    return get_database()["Teaches"]

def get_advisors():
    return get_database()["Advisor"]

def get_prereqs():
    return get_database()["Prereq"]

def get_departments():
    return get_database()["Department"]

def get_classrooms():
    return get_database()["Classroom"]

def get_time_slots():
    return get_database()["Time_slot"]
