# Configuración de conexión a MongoDB y MySQL
from pymongo import MongoClient
import aiomysql
from config import settings

# ==================== MongoDB ====================
# Conexión síncrona con pymongo
client = None
university = None

def connect_to_mongo():
    """Conectar a MongoDB Atlas"""
    global client, university
    client = MongoClient(settings.MONGODB_URL)
    university = client[settings.MONGODB_DATABASE]
    print("✅ Conectado a MongoDB Atlas")
    print(f"   Colecciones: {university.list_collection_names()}")

def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    global client
    if client:
        client.close()
    print("❌ Conexión a MongoDB cerrada")

# Colecciones MongoDB
def get_mongo_collection(name: str):
    return university[name]

# Acceso directo a colecciones
def get_students():
    return university["Student"]

def get_courses():
    return university["Course"]

def get_instructors():
    return university["Instructor"]

def get_sections():
    return university["Section"]

def get_takes():
    return university["Takes"]

def get_teaches():
    return university["Teaches"]

def get_advisors():
    return university["Advisor"]

def get_prereqs():
    return university["Prereq"]

def get_departments():
    return university["Department"]

def get_time_slots():
    return university["Time_slot"]


# ==================== MySQL ====================
class MySQLDatabase:
    pool = None

mysql_db = MySQLDatabase()

async def connect_to_mysql():
    """Conectar a MySQL"""
    try:
        mysql_db.pool = await aiomysql.create_pool(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            db=settings.MYSQL_DATABASE,
            autocommit=True,
            minsize=1,
            maxsize=10
        )
        print("✅ Conectado a MySQL")
    except Exception as e:
        print(f"⚠️ No se pudo conectar a MySQL: {e}")

async def close_mysql_connection():
    """Cerrar conexión a MySQL"""
    if mysql_db.pool:
        mysql_db.pool.close()
        await mysql_db.pool.wait_closed()
    print("❌ Conexión a MySQL cerrada")

async def execute_query(query: str, params: tuple = None):
    """Ejecutar una consulta MySQL y retornar resultados"""
    async with mysql_db.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params)
            result = await cursor.fetchall()
            return result

async def execute_query_one(query: str, params: tuple = None):
    """Ejecutar una consulta MySQL y retornar un solo resultado"""
    async with mysql_db.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params)
            result = await cursor.fetchone()
            return result
