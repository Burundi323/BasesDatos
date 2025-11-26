# Router para las 10 consultas de la Universidad
from fastapi import APIRouter, HTTPException, Query
from database import (
    get_students, get_courses, get_instructors, get_sections,
    get_takes, get_teaches, get_advisors, get_prereqs, 
    get_departments, get_classrooms, get_time_slots
)

router = APIRouter()

def serialize_doc(doc) -> dict:
    """Convertir documento MongoDB a dict serializable"""
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ============================================
# CONSULTA 1: Prerrequisitos de un curso
# ============================================
@router.get("/consulta1/prereqs/{course_id}")
async def get_course_prerequisites(course_id: str):
    """
    Encontrar los prerrequisitos de un curso.
    Si el curso no existe, envía mensaje de error.
    """
    courses = get_courses()
    prereqs = get_prereqs()
    
    # Verificar si el curso existe
    course = await courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail=f"El curso '{course_id}' no existe")
    
    # Buscar prerrequisitos
    prereq_list = await prereqs.find({"course_id": course_id}).to_list(100)
    
    if not prereq_list:
        return {
            "curso": serialize_doc(course),
            "mensaje": "Este curso no tiene prerrequisitos",
            "prerrequisitos": []
        }
    
    # Obtener detalles de cada prerrequisito
    prereq_details = []
    for p in prereq_list:
        prereq_course = await courses.find_one({"course_id": p["prereq_id"]})
        if prereq_course:
            prereq_details.append(serialize_doc(prereq_course))
    
    return {
        "curso": serialize_doc(course),
        "prerrequisitos": prereq_details
    }


# ============================================
# CONSULTA 2: Historial académico de estudiante
# ============================================
@router.get("/consulta2/transcript/{student_id}")
async def get_student_transcript(student_id: str):
    """
    Obtener el historial académico completo (transcript) de un estudiante.
    """
    students = get_students()
    takes_col = get_takes()
    courses = get_courses()
    
    # Verificar si el estudiante existe
    student = await students.find_one({"ID": student_id})
    if not student:
        raise HTTPException(status_code=404, detail=f"El estudiante con ID '{student_id}' no existe")
    
    # Obtener todas las materias cursadas
    takes_list = await takes_col.find({"ID": student_id}).to_list(1000)
    
    # Obtener detalles de cada curso
    transcript = []
    for t in takes_list:
        course = await courses.find_one({"course_id": t["course_id"]})
        transcript.append({
            "course_id": t["course_id"],
            "title": course["title"] if course else "N/A",
            "credits": course["credits"] if course else 0,
            "semester": t["semester"],
            "year": t["year"],
            "grade": t["grade"],
            "sec_id": t["sec_id"]
        })
    
    # Ordenar por año y semestre
    transcript.sort(key=lambda x: (x["year"], x["semester"]))
    
    return {
        "estudiante": serialize_doc(student),
        "historial": transcript,
        "total_cursos": len(transcript)
    }


# ============================================
# CONSULTA 3: Detalles de una sección (horario y aula)
# ============================================
@router.get("/consulta3/section/{course_id}/{sec_id}/{semester}/{year}")
async def get_section_details(course_id: str, sec_id: str, semester: str, year: int):
    """
    Encontrar los detalles (horario y aula) de una sección específica.
    """
    sections = get_sections()
    time_slots = get_time_slots()
    classrooms = get_classrooms()
    courses = get_courses()
    
    # Buscar la sección
    section = await sections.find_one({
        "course_id": course_id,
        "sec_id": sec_id,
        "semester": semester,
        "year": year
    })
    
    if not section:
        raise HTTPException(status_code=404, detail="Sección no encontrada")
    
    # Obtener información del curso
    course = await courses.find_one({"course_id": course_id})
    
    # Obtener horario
    time_slot_list = await time_slots.find({"time_slot_id": section["time_slot_id"]}).to_list(10)
    
    # Obtener aula
    classroom = await classrooms.find_one({
        "building": section["building"],
        "room_number": section["room_number"]
    })
    
    return {
        "curso": course["title"] if course else "N/A",
        "seccion": {
            "course_id": course_id,
            "sec_id": sec_id,
            "semester": semester,
            "year": year
        },
        "aula": {
            "edificio": section["building"],
            "numero_sala": section["room_number"],
            "capacidad": classroom["capacity"] if classroom else "N/A"
        },
        "horario": [serialize_doc(ts) for ts in time_slot_list]
    }


# ============================================
# CONSULTA 4: Secciones en un edificio
# ============================================
@router.get("/consulta4/sections-by-building/{building}")
async def get_sections_by_building(building: str):
    """
    Encontrar todas las secciones que se imparten en el edificio X.
    """
    sections = get_sections()
    courses = get_courses()
    
    # Buscar secciones en el edificio (case-insensitive)
    section_list = await sections.find({
        "building": {"$regex": f"^{building}$", "$options": "i"}
    }).to_list(500)
    
    if not section_list:
        raise HTTPException(status_code=404, detail=f"No se encontraron secciones en el edificio '{building}'")
    
    # Agregar nombre del curso a cada sección
    result = []
    for s in section_list:
        course = await courses.find_one({"course_id": s["course_id"]})
        result.append({
            "course_id": s["course_id"],
            "course_title": course["title"] if course else "N/A",
            "sec_id": s["sec_id"],
            "semester": s["semester"],
            "year": s["year"],
            "room_number": s["room_number"],
            "time_slot_id": s["time_slot_id"]
        })
    
    return {
        "edificio": building,
        "total_secciones": len(result),
        "secciones": result
    }


# ============================================
# CONSULTA 5: Estudiante y su asesor
# ============================================
@router.get("/consulta5/student-advisor/{student_id}")
async def get_student_and_advisor(student_id: str):
    """
    Encontrar el nombre de un estudiante y el nombre de su asesor.
    """
    students = get_students()
    advisors = get_advisors()
    instructors = get_instructors()
    
    # Buscar estudiante
    student = await students.find_one({"ID": student_id})
    if not student:
        raise HTTPException(status_code=404, detail=f"El estudiante con ID '{student_id}' no existe")
    
    # Buscar asesor
    advisor = await advisors.find_one({"s_ID": student_id})
    
    advisor_info = None
    if advisor:
        instructor = await instructors.find_one({"ID": advisor["i_ID"]})
        if instructor:
            advisor_info = {
                "ID": instructor["ID"],
                "nombre": instructor["name"],
                "departamento": instructor["dept_name"]
            }
    
    return {
        "estudiante": {
            "ID": student["ID"],
            "nombre": student["name"],
            "departamento": student["dept_name"],
            "creditos_totales": student["tot_cred"]
        },
        "asesor": advisor_info if advisor_info else "No tiene asesor asignado"
    }


# ============================================
# CONSULTA 6: Estudiantes con 'A' en un curso
# ============================================
@router.get("/consulta6/students-with-a/{course_id}")
async def get_students_with_a_in_course(course_id: str):
    """
    Encontrar a todos los estudiantes que obtuvieron una 'A' en el curso X.
    """
    courses = get_courses()
    takes_col = get_takes()
    students = get_students()
    
    # Verificar si el curso existe
    course = await courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail=f"El curso '{course_id}' no existe")
    
    # Buscar estudiantes con A (incluye A, A-, A+)
    takes_list = await takes_col.find({
        "course_id": course_id,
        "grade": {"$regex": "^A", "$options": "i"}
    }).to_list(1000)
    
    # Obtener información de cada estudiante
    result = []
    for t in takes_list:
        student = await students.find_one({"ID": t["ID"]})
        if student:
            result.append({
                "ID": student["ID"],
                "nombre": student["name"],
                "departamento": student["dept_name"],
                "calificacion": t["grade"],
                "semester": t["semester"],
                "year": t["year"]
            })
    
    return {
        "curso": {
            "course_id": course["course_id"],
            "titulo": course["title"]
        },
        "total_estudiantes": len(result),
        "estudiantes": result
    }


# ============================================
# CONSULTA 7: Estudiantes asesorados por profesor X
# ============================================
@router.get("/consulta7/students-by-advisor/{instructor_name}")
async def get_students_by_advisor_name(instructor_name: str):
    """
    Encontrar los nombres de todos los estudiantes asesorados por el profesor de nombre X.
    """
    instructors = get_instructors()
    advisors = get_advisors()
    students = get_students()
    
    # Buscar instructor por nombre (case-insensitive)
    instructor = await instructors.find_one({
        "name": {"$regex": f"^{instructor_name}$", "$options": "i"}
    })
    
    if not instructor:
        raise HTTPException(status_code=404, detail=f"No se encontró un profesor con nombre '{instructor_name}'")
    
    # Buscar estudiantes asesorados
    advisor_list = await advisors.find({"i_ID": instructor["ID"]}).to_list(500)
    
    result = []
    for a in advisor_list:
        student = await students.find_one({"ID": a["s_ID"]})
        if student:
            result.append({
                "ID": student["ID"],
                "nombre": student["name"],
                "departamento": student["dept_name"],
                "creditos": student["tot_cred"]
            })
    
    return {
        "profesor": {
            "ID": instructor["ID"],
            "nombre": instructor["name"],
            "departamento": instructor["dept_name"]
        },
        "total_estudiantes": len(result),
        "estudiantes": result
    }


# ============================================
# CONSULTA 8: Cursos que imparte un profesor
# ============================================
@router.get("/consulta8/courses-by-instructor/{instructor_name}")
async def get_courses_by_instructor(instructor_name: str):
    """
    Encontrar todos los cursos (título, horario y aula) que imparte el profesor de nombre X.
    """
    instructors = get_instructors()
    teaches_col = get_teaches()
    sections = get_sections()
    courses = get_courses()
    time_slots = get_time_slots()
    
    # Buscar instructor
    instructor = await instructors.find_one({
        "name": {"$regex": f"^{instructor_name}$", "$options": "i"}
    })
    
    if not instructor:
        raise HTTPException(status_code=404, detail=f"No se encontró un profesor con nombre '{instructor_name}'")
    
    # Buscar cursos que enseña
    teaches_list = await teaches_col.find({"ID": instructor["ID"]}).to_list(100)
    
    result = []
    for t in teaches_list:
        course = await courses.find_one({"course_id": t["course_id"]})
        section = await sections.find_one({
            "course_id": t["course_id"],
            "sec_id": t["sec_id"],
            "semester": t["semester"],
            "year": t["year"]
        })
        
        horario = []
        if section:
            time_slot_list = await time_slots.find({"time_slot_id": section["time_slot_id"]}).to_list(10)
            horario = [{"dia": ts["day"], "hora_inicio": f"{ts['start_hr']}:{ts['start_min']:02d}", 
                       "hora_fin": f"{ts['end_hr']}:{ts['end_min']:02d}"} for ts in time_slot_list]
        
        result.append({
            "course_id": t["course_id"],
            "titulo": course["title"] if course else "N/A",
            "creditos": course["credits"] if course else 0,
            "sec_id": t["sec_id"],
            "semester": t["semester"],
            "year": t["year"],
            "aula": f"{section['building']} {section['room_number']}" if section else "N/A",
            "horario": horario
        })
    
    return {
        "profesor": {
            "ID": instructor["ID"],
            "nombre": instructor["name"],
            "departamento": instructor["dept_name"]
        },
        "total_cursos": len(result),
        "cursos": result
    }


# ============================================
# CONSULTA 9: Salario promedio por departamento
# ============================================
@router.get("/consulta9/avg-salary-by-department")
async def get_avg_salary_by_department():
    """
    Calcular el salario promedio por departamento.
    """
    instructors = get_instructors()
    
    # Usar agregación de MongoDB
    pipeline = [
        {
            "$group": {
                "_id": "$dept_name",
                "salario_promedio": {"$avg": "$salary"},
                "total_profesores": {"$sum": 1},
                "salario_minimo": {"$min": "$salary"},
                "salario_maximo": {"$max": "$salary"}
            }
        },
        {
            "$sort": {"salario_promedio": -1}
        }
    ]
    
    result = await instructors.aggregate(pipeline).to_list(100)
    
    # Formatear resultado
    formatted = []
    for r in result:
        formatted.append({
            "departamento": r["_id"],
            "salario_promedio": round(r["salario_promedio"], 2),
            "total_profesores": r["total_profesores"],
            "salario_minimo": round(r["salario_minimo"], 2),
            "salario_maximo": round(r["salario_maximo"], 2)
        })
    
    return {
        "total_departamentos": len(formatted),
        "departamentos": formatted
    }


# ============================================
# CONSULTA 10: Estudiantes de depto X con >90 créditos
# ============================================
@router.get("/consulta10/students-high-credits/{dept_name}")
async def get_students_with_high_credits(dept_name: str, min_credits: int = 90):
    """
    Encontrar todos los estudiantes del departamento X con más de 90 créditos.
    """
    students = get_students()
    
    # Buscar estudiantes
    student_list = await students.find({
        "dept_name": {"$regex": f"^{dept_name}$", "$options": "i"},
        "tot_cred": {"$gt": min_credits}
    }).to_list(1000)
    
    if not student_list:
        raise HTTPException(
            status_code=404, 
            detail=f"No se encontraron estudiantes en '{dept_name}' con más de {min_credits} créditos"
        )
    
    result = [{
        "ID": s["ID"],
        "nombre": s["name"],
        "creditos": s["tot_cred"]
    } for s in student_list]
    
    # Ordenar por créditos descendente
    result.sort(key=lambda x: x["creditos"], reverse=True)
    
    return {
        "departamento": dept_name,
        "creditos_minimos": min_credits,
        "total_estudiantes": len(result),
        "estudiantes": result
    }
