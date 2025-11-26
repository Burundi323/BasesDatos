# Backend API para Universidad
# FastAPI + MongoDB Atlas

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import queries
from database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Universidad API",
    description="API para consultas de la base de datos Universidad - 10 consultas predeterminadas",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos incluyendo OPTIONS
    allow_headers=["*"],
)

# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Incluir router de consultas
app.include_router(queries.router, prefix="/api", tags=["Consultas Universidad"])


# Endpoint de prueba para verificar conexión
@app.get("/api/test")
async def test_connection():
    from database import get_students
    students = get_students()
    count = await students.count_documents({})
    return {"status": "ok", "students_count": count}

# Ruta raíz
@app.get("/")
async def root():
    return {
        "message": "Bienvenido a Universidad API",
        "docs": "/docs",
        "consultas": {
            "1": "/api/consulta1/prereqs/{course_id} - Prerrequisitos de un curso",
            "2": "/api/consulta2/transcript/{student_id} - Historial académico",
            "3": "/api/consulta3/section/{course_id}/{sec_id}/{semester}/{year} - Detalles de sección",
            "4": "/api/consulta4/sections-by-building/{building} - Secciones por edificio",
            "5": "/api/consulta5/student-advisor/{student_id} - Estudiante y asesor",
            "6": "/api/consulta6/students-with-a/{course_id} - Estudiantes con A en curso",
            "7": "/api/consulta7/students-by-advisor/{instructor_name} - Estudiantes por asesor",
            "8": "/api/consulta8/courses-by-instructor/{instructor_name} - Cursos por profesor",
            "9": "/api/consulta9/avg-salary-by-department - Salario promedio por depto",
            "10": "/api/consulta10/students-high-credits/{dept_name} - Estudiantes con >90 créditos"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
