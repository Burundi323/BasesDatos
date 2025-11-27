# Configuración de conexión a MongoDB Atlas y MySQL
from motor.motor_asyncio import AsyncIOMotorClient
import aiomysql
from config import settings

# ==================== MongoDB ====================
class MongoDatabase:
    client: AsyncIOMotorClient = None

mongo_db = MongoDatabase()

async def connect_to_mongo():
    """Conectar a MongoDB Atlas"""
    mongo_db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    print("✅ Conectado a MongoDB Atlas")

async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    if mongo_db.client:
        mongo_db.client.close()
    print("❌ Conexión a MongoDB cerrada")

def get_mongo_database():
    return mongo_db.client[settings.MONGODB_DATABASE]

def get_mongo_collection(name: str):
    return get_mongo_database()[name]

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
