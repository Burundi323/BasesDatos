# Router para las 10 consultas de la Universidad
# Compatible con el frontend existente
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import (
    get_students, get_courses, get_instructors, get_sections,
    get_takes, get_teaches, get_advisors, get_prereqs, 
    get_departments, get_classrooms, get_time_slots
)

router = APIRouter()

# Modelo para recibir parámetros del frontend
class ConsultaParams(BaseModel):
    courseId: Optional[str] = None
    studentId: Optional[str] = None
    sectionId: Optional[str] = None
    building: Optional[str] = None
    studentName: Optional[str] = None
    courseName: Optional[str] = None
    professorName: Optional[str] = None
    departmentName: Optional[str] = None


def format_response(columns: list, rows: list) -> dict:
    """Formatear respuesta como espera el frontend"""
    return {
        "columns": columns,
        "rows": rows
    }


# ============================================
# CONSULTA 1: Prerrequisitos de un curso
# ============================================
@router.post("/consulta/1")
async def consulta_1(params: ConsultaParams):
    """Encontrar los prerrequisitos de un curso."""
    course_id = params.courseId
    if not course_id:
        raise HTTPException(status_code=400, detail="Falta el ID del curso")
    
    courses = get_courses()
    prereqs = get_prereqs()
    
    # Verificar si el curso existe
    course = await courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail=f"El curso '{course_id}' no existe")
    
    # Buscar prerrequisitos
    prereq_list = await prereqs.find({"course_id": course_id}).to_list(100)
    
    if not prereq_list:
        return format_response(
            columns=["Mensaje"],
            rows=[["Este curso no tiene prerrequisitos"]]
        )
    
    # Obtener detalles de cada prerrequisito
    rows = []
    for p in prereq_list:
        prereq_course = await courses.find_one({"course_id": p["prereq_id"]})
        if prereq_course:
            rows.append([
                prereq_course["course_id"],
                prereq_course["title"],
                prereq_course["dept_name"],
                str(prereq_course["credits"])
            ])
    
    return format_response(
        columns=["ID Prerrequisito", "Título", "Departamento", "Créditos"],
        rows=rows
    )


# ============================================
# CONSULTA 2: Historial académico de estudiante
# ============================================
@router.post("/consulta/2")
async def consulta_2(params: ConsultaParams):
    """Obtener el historial académico completo de un estudiante."""
    student_id = params.studentId
    if not student_id:
        raise HTTPException(status_code=400, detail="Falta el ID del estudiante")
    
    students = get_students()
    takes_col = get_takes()
    courses = get_courses()
    
    # Verificar si el estudiante existe
    student = await students.find_one({"ID": student_id})
    if not student:
        raise HTTPException(status_code=404, detail=f"El estudiante con ID '{student_id}' no existe")
    
    # Obtener todas las materias cursadas
    takes_list = await takes_col.find({"ID": student_id}).to_list(1000)
    
    if not takes_list:
        return format_response(
            columns=["Mensaje"],
            rows=[[f"El estudiante {student['name']} no tiene cursos registrados"]]
        )
    
    rows = []
    for t in takes_list:
        course = await courses.find_one({"course_id": t["course_id"]})
        rows.append([
            t["course_id"],
            course["title"] if course else "N/A",
            str(course["credits"]) if course else "0",
            t["semester"],
            str(t["year"]),
            t["grade"] if t["grade"] else "N/A"
        ])
    
    # Ordenar por año y semestre
    rows.sort(key=lambda x: (x[4], x[3]))
    
    return format_response(
        columns=["ID Curso", "Título", "Créditos", "Semestre", "Año", "Calificación"],
        rows=rows
    )


# ============================================
# CONSULTA 3: Detalles de una sección
# ============================================
@router.post("/consulta/3")
async def consulta_3(params: ConsultaParams):
    """Encontrar los detalles (horario y aula) de una sección específica."""
    sec_id = params.sectionId
    if not sec_id:
        raise HTTPException(status_code=400, detail="Falta el ID de la sección")
    
    sections = get_sections()
    time_slots = get_time_slots()
    courses = get_courses()
    
    # Buscar secciones con ese sec_id
    section_list = await sections.find({"sec_id": sec_id}).to_list(100)
    
    if not section_list:
        raise HTTPException(status_code=404, detail=f"No se encontró la sección '{sec_id}'")
    
    rows = []
    for section in section_list:
        course = await courses.find_one({"course_id": section["course_id"]})
        time_slot_list = await time_slots.find({"time_slot_id": section["time_slot_id"]}).to_list(10)
        
        # Formatear horario
        horario = ", ".join([
            f"{ts['day']} {ts['start_hr']}:{ts['start_min']:02d}-{ts['end_hr']}:{ts['end_min']:02d}"
            for ts in time_slot_list
        ]) if time_slot_list else "N/A"
        
        rows.append([
            section["course_id"],
            course["title"] if course else "N/A",
            section["sec_id"],
            section["semester"],
            str(section["year"]),
            section["building"],
            str(section["room_number"]),
            horario
        ])
    
    return format_response(
        columns=["ID Curso", "Título", "Sección", "Semestre", "Año", "Edificio", "Sala", "Horario"],
        rows=rows
    )


# ============================================
# CONSULTA 4: Secciones en un edificio
# ============================================
@router.post("/consulta/4")
async def consulta_4(params: ConsultaParams):
    """Encontrar todas las secciones que se imparten en el edificio X."""
    building = params.building
    if not building:
        raise HTTPException(status_code=400, detail="Falta el nombre del edificio")
    
    sections = get_sections()
    courses = get_courses()
    
    # Buscar secciones en el edificio (case-insensitive)
    section_list = await sections.find({
        "building": {"$regex": f"^{building}$", "$options": "i"}
    }).to_list(500)
    
    if not section_list:
        raise HTTPException(status_code=404, detail=f"No se encontraron secciones en el edificio '{building}'")
    
    rows = []
    for s in section_list:
        course = await courses.find_one({"course_id": s["course_id"]})
        rows.append([
            s["course_id"],
            course["title"] if course else "N/A",
            s["sec_id"],
            s["semester"],
            str(s["year"]),
            str(s["room_number"]),
            s["time_slot_id"]
        ])
    
    return format_response(
        columns=["ID Curso", "Título", "Sección", "Semestre", "Año", "Sala", "Horario ID"],
        rows=rows
    )


# ============================================
# CONSULTA 5: Estudiante y su asesor
# ============================================
@router.post("/consulta/5")
async def consulta_5(params: ConsultaParams):
    """Encontrar el nombre de un estudiante y el nombre de su asesor."""
    student_name = params.studentName
    if not student_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del estudiante")
    
    students = get_students()
    advisors = get_advisors()
    instructors = get_instructors()
    
    # Buscar estudiante por nombre (case-insensitive)
    student_list = await students.find({
        "name": {"$regex": f"^{student_name}$", "$options": "i"}
    }).to_list(100)
    
    if not student_list:
        raise HTTPException(status_code=404, detail=f"No se encontró estudiante con nombre '{student_name}'")
    
    rows = []
    for student in student_list:
        advisor = await advisors.find_one({"s_ID": student["ID"]})
        
        advisor_name = "Sin asesor asignado"
        advisor_dept = "N/A"
        if advisor:
            instructor = await instructors.find_one({"ID": advisor["i_ID"]})
            if instructor:
                advisor_name = instructor["name"]
                advisor_dept = instructor["dept_name"]
        
        rows.append([
            student["ID"],
            student["name"],
            student["dept_name"],
            str(student["tot_cred"]),
            advisor_name,
            advisor_dept
        ])
    
    return format_response(
        columns=["ID Estudiante", "Nombre Estudiante", "Depto. Estudiante", "Créditos", "Nombre Asesor", "Depto. Asesor"],
        rows=rows
    )


# ============================================
# CONSULTA 6: Estudiantes con 'A' en un curso
# ============================================
@router.post("/consulta/6")
async def consulta_6(params: ConsultaParams):
    """Encontrar a todos los estudiantes que obtuvieron una 'A' en el curso X."""
    course_name = params.courseName
    if not course_name:
        raise HTTPException(status_code=400, detail="Falta el nombre o ID del curso")
    
    courses = get_courses()
    takes_col = get_takes()
    students = get_students()
    
    # Buscar curso por ID o título
    course = await courses.find_one({
        "$or": [
            {"course_id": course_name},
            {"title": {"$regex": f"^{course_name}$", "$options": "i"}}
        ]
    })
    
    if not course:
        raise HTTPException(status_code=404, detail=f"El curso '{course_name}' no existe")
    
    # Buscar estudiantes con A (incluye A, A-, A+)
    takes_list = await takes_col.find({
        "course_id": course["course_id"],
        "grade": {"$regex": "^A", "$options": "i"}
    }).to_list(1000)
    
    if not takes_list:
        return format_response(
            columns=["Mensaje"],
            rows=[[f"Ningún estudiante obtuvo 'A' en el curso {course['title']}"]]
        )
    
    rows = []
    for t in takes_list:
        student = await students.find_one({"ID": t["ID"]})
        if student:
            rows.append([
                student["ID"],
                student["name"],
                student["dept_name"],
                t["grade"],
                t["semester"],
                str(t["year"])
            ])
    
    return format_response(
        columns=["ID Estudiante", "Nombre", "Departamento", "Calificación", "Semestre", "Año"],
        rows=rows
    )


# ============================================
# CONSULTA 7: Estudiantes asesorados por profesor X
# ============================================
@router.post("/consulta/7")
async def consulta_7(params: ConsultaParams):
    """Encontrar los nombres de todos los estudiantes asesorados por el profesor de nombre X."""
    professor_name = params.professorName
    if not professor_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del profesor")
    
    instructors = get_instructors()
    advisors = get_advisors()
    students = get_students()
    
    # Buscar instructor por nombre (case-insensitive)
    instructor = await instructors.find_one({
        "name": {"$regex": f"^{professor_name}$", "$options": "i"}
    })
    
    if not instructor:
        raise HTTPException(status_code=404, detail=f"No se encontró un profesor con nombre '{professor_name}'")
    
    # Buscar estudiantes asesorados
    advisor_list = await advisors.find({"i_ID": instructor["ID"]}).to_list(500)
    
    if not advisor_list:
        return format_response(
            columns=["Mensaje"],
            rows=[[f"El profesor {instructor['name']} no tiene estudiantes asignados"]]
        )
    
    rows = []
    for a in advisor_list:
        student = await students.find_one({"ID": a["s_ID"]})
        if student:
            rows.append([
                student["ID"],
                student["name"],
                student["dept_name"],
                str(student["tot_cred"])
            ])
    
    return format_response(
        columns=["ID Estudiante", "Nombre", "Departamento", "Créditos"],
        rows=rows
    )


# ============================================
# CONSULTA 8: Cursos que imparte un profesor
# ============================================
@router.post("/consulta/8")
async def consulta_8(params: ConsultaParams):
    """Encontrar todos los cursos (título, horario y aula) que imparte el profesor de nombre X."""
    professor_name = params.professorName
    if not professor_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del profesor")
    
    instructors = get_instructors()
    teaches_col = get_teaches()
    sections = get_sections()
    courses = get_courses()
    time_slots = get_time_slots()
    
    # Buscar instructor
    instructor = await instructors.find_one({
        "name": {"$regex": f"^{professor_name}$", "$options": "i"}
    })
    
    if not instructor:
        raise HTTPException(status_code=404, detail=f"No se encontró un profesor con nombre '{professor_name}'")
    
    # Buscar cursos que enseña
    teaches_list = await teaches_col.find({"ID": instructor["ID"]}).to_list(100)
    
    if not teaches_list:
        return format_response(
            columns=["Mensaje"],
            rows=[[f"El profesor {instructor['name']} no imparte ningún curso"]]
        )
    
    rows = []
    for t in teaches_list:
        course = await courses.find_one({"course_id": t["course_id"]})
        section = await sections.find_one({
            "course_id": t["course_id"],
            "sec_id": t["sec_id"],
            "semester": t["semester"],
            "year": t["year"]
        })
        
        horario = "N/A"
        aula = "N/A"
        if section:
            aula = f"{section['building']} {section['room_number']}"
            time_slot_list = await time_slots.find({"time_slot_id": section["time_slot_id"]}).to_list(10)
            if time_slot_list:
                horario = ", ".join([
                    f"{ts['day']} {ts['start_hr']}:{ts['start_min']:02d}-{ts['end_hr']}:{ts['end_min']:02d}"
                    for ts in time_slot_list
                ])
        
        rows.append([
            t["course_id"],
            course["title"] if course else "N/A",
            t["sec_id"],
            t["semester"],
            str(t["year"]),
            aula,
            horario
        ])
    
    return format_response(
        columns=["ID Curso", "Título", "Sección", "Semestre", "Año", "Aula", "Horario"],
        rows=rows
    )


# ============================================
# CONSULTA 9: Salario promedio por departamento
# ============================================
@router.post("/consulta/9")
async def consulta_9(params: ConsultaParams):
    """Calcular el salario promedio por departamento."""
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
    
    rows = []
    for r in result:
        rows.append([
            r["_id"],
            f"${r['salario_promedio']:,.2f}",
            str(r["total_profesores"]),
            f"${r['salario_minimo']:,.2f}",
            f"${r['salario_maximo']:,.2f}"
        ])
    
    return format_response(
        columns=["Departamento", "Salario Promedio", "Total Profesores", "Salario Mínimo", "Salario Máximo"],
        rows=rows
    )


# ============================================
# CONSULTA 10: Estudiantes de depto X con >90 créditos
# ============================================
@router.post("/consulta/10")
async def consulta_10(params: ConsultaParams):
    """Encontrar todos los estudiantes del departamento X con más de 90 créditos."""
    dept_name = params.departmentName
    if not dept_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del departamento")
    
    students = get_students()
    
    # Buscar estudiantes
    student_list = await students.find({
        "dept_name": {"$regex": f"^{dept_name}$", "$options": "i"},
        "tot_cred": {"$gt": 90}
    }).to_list(1000)
    
    if not student_list:
        raise HTTPException(
            status_code=404, 
            detail=f"No se encontraron estudiantes en '{dept_name}' con más de 90 créditos"
        )
    
    rows = []
    for s in student_list:
        rows.append([
            s["ID"],
            s["name"],
            s["dept_name"],
            str(s["tot_cred"])
        ])
    
    # Ordenar por créditos descendente
    rows.sort(key=lambda x: int(x[3]), reverse=True)
    
    return format_response(
        columns=["ID Estudiante", "Nombre", "Departamento", "Créditos"],
        rows=rows
    )
