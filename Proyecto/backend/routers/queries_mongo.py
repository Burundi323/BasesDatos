# Router para consultas MongoDB (sintaxis pymongo síncrona)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import (
    get_students, get_courses, get_instructors, get_sections,
    get_takes, get_teaches, get_advisors, get_prereqs,
    get_departments, get_time_slots
)

router = APIRouter()

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
    return {"columns": columns, "rows": rows}


# ============================================
# CONSULTA 1: Prerrequisitos de un curso
# ============================================
@router.post("/consulta/1")
def consulta_1(params: ConsultaParams):
    """Encontrar los prerrequisitos de un curso."""
    course_id = params.courseId
    if not course_id:
        raise HTTPException(status_code=400, detail="Falta el ID del curso")
    
    # Acceso a colecciones
    courses = get_courses()      # university["Course"]
    prereqs = get_prereqs()      # university["Prereq"]
    
    # Buscar si el curso existe
    # Similar a: SELECT * FROM course WHERE course_id = '376'
    course = courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail=f"El curso '{course_id}' no existe")
    
    # Buscar prerrequisitos
    # Similar a: SELECT * FROM prereq WHERE course_id = '376'
    cursor = prereqs.find({"course_id": course_id})
    prereq_list = list(cursor)  # Convertir cursor a lista
    
    if len(prereq_list) == 0:
        return format_response(["Mensaje"], [["Este curso no tiene prerrequisitos"]])
    
    # Obtener detalles de cada prerrequisito
    rows = []
    for p in prereq_list:
        # Buscar el curso prerrequisito
        prereq_course = courses.find_one({"course_id": p["prereq_id"]})
        if prereq_course:
            rows.append([
                prereq_course["course_id"],
                prereq_course["title"],
                prereq_course["dept_name"],
                str(prereq_course["credits"])
            ])
    
    return format_response(["ID Prerrequisito", "Título", "Departamento", "Créditos"], rows)


# ============================================
# CONSULTA 2: Historial académico de estudiante
# ============================================
@router.post("/consulta/2")
def consulta_2(params: ConsultaParams):
    """Obtener el historial académico completo de un estudiante."""
    student_id = params.studentId
    if not student_id:
        raise HTTPException(status_code=400, detail="Falta el ID del estudiante")
    
    students = get_students()    # university["Student"]
    takes = get_takes()          # university["Takes"]
    courses = get_courses()      # university["Course"]
    
    # Buscar estudiante
    # Similar a: SELECT * FROM student WHERE ID = '24746'
    student = students.find_one({"ID": student_id})
    if not student:
        raise HTTPException(status_code=404, detail=f"El estudiante con ID '{student_id}' no existe")
    
    # Buscar materias cursadas
    # Similar a: SELECT * FROM takes WHERE ID = '24746'
    cursor = takes.find({"ID": student_id})
    takes_list = list(cursor)
    
    if len(takes_list) == 0:
        return format_response(["Mensaje"], [[f"El estudiante {student['name']} no tiene cursos registrados"]])
    
    # Construir historial
    rows = []
    for t in takes_list:
        # Buscar información del curso
        course = courses.find_one({"course_id": t["course_id"]})
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
    
    return format_response(["ID Curso", "Título", "Créditos", "Semestre", "Año", "Calificación"], rows)


# ============================================
# CONSULTA 3: Detalles de una sección
# ============================================
@router.post("/consulta/3")
def consulta_3(params: ConsultaParams):
    """Encontrar los detalles (horario y aula) de una sección específica."""
    sec_id = params.sectionId
    if not sec_id:
        raise HTTPException(status_code=400, detail="Falta el ID de la sección")
    
    sections = get_sections()      # university["Section"]
    time_slots = get_time_slots()  # university["Time_slot"]
    courses = get_courses()        # university["Course"]
    
    # Buscar secciones con ese sec_id
    # Similar a: SELECT * FROM section WHERE sec_id = '1'
    cursor = sections.find({"sec_id": sec_id})
    section_list = list(cursor)
    
    if len(section_list) == 0:
        raise HTTPException(status_code=404, detail=f"No se encontró la sección '{sec_id}'")
    
    rows = []
    for section in section_list:
        # Buscar curso
        course = courses.find_one({"course_id": section["course_id"]})
        
        # Buscar horarios
        ts_cursor = time_slots.find({"time_slot_id": section["time_slot_id"]})
        ts_list = list(ts_cursor)
        
        # Formatear horario
        horario = ", ".join([
            f"{ts['day']} {ts['start_hr']}:{ts['start_min']:02d}-{ts['end_hr']}:{ts['end_min']:02d}"
            for ts in ts_list
        ]) if ts_list else "N/A"
        
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
    
    return format_response(["ID Curso", "Título", "Sección", "Semestre", "Año", "Edificio", "Sala", "Horario"], rows)


# ============================================
# CONSULTA 4: Secciones en un edificio
# ============================================
@router.post("/consulta/4")
def consulta_4(params: ConsultaParams):
    """Encontrar todas las secciones que se imparten en el edificio X."""
    building = params.building
    if not building:
        raise HTTPException(status_code=400, detail="Falta el nombre del edificio")
    
    sections = get_sections()  # university["Section"]
    courses = get_courses()    # university["Course"]
    
    # Buscar secciones en el edificio (case-insensitive)
    # Similar a: SELECT * FROM section WHERE LOWER(building) = LOWER('Gates')
    cursor = sections.find({"building": {"$regex": f"^{building}$", "$options": "i"}})
    section_list = list(cursor)
    
    if len(section_list) == 0:
        raise HTTPException(status_code=404, detail=f"No se encontraron secciones en el edificio '{building}'")
    
    rows = []
    for s in section_list:
        course = courses.find_one({"course_id": s["course_id"]})
        rows.append([
            s["course_id"],
            course["title"] if course else "N/A",
            s["sec_id"],
            s["semester"],
            str(s["year"]),
            str(s["room_number"]),
            s["time_slot_id"]
        ])
    
    return format_response(["ID Curso", "Título", "Sección", "Semestre", "Año", "Sala", "Horario ID"], rows)


# ============================================
# CONSULTA 5: Estudiante y su asesor
# ============================================
@router.post("/consulta/5")
def consulta_5(params: ConsultaParams):
    """Encontrar el nombre de un estudiante y el nombre de su asesor."""
    student_name = params.studentName
    if not student_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del estudiante")
    
    students = get_students()        # university["Student"]
    advisors = get_advisors()        # university["Advisor"]
    instructors = get_instructors()  # university["Instructor"]
    
    # Buscar estudiante por nombre
    # Similar a: SELECT * FROM student WHERE LOWER(name) = LOWER('Schrefl')
    cursor = students.find({"name": {"$regex": f"^{student_name}$", "$options": "i"}})
    student_list = list(cursor)
    
    if len(student_list) == 0:
        raise HTTPException(status_code=404, detail=f"No se encontró estudiante con nombre '{student_name}'")
    
    rows = []
    for student in student_list:
        # Buscar asesor del estudiante
        advisor = advisors.find_one({"s_ID": student["ID"]})
        
        advisor_name = "Sin asesor"
        advisor_dept = "N/A"
        if advisor:
            # Buscar información del instructor/asesor
            instructor = instructors.find_one({"ID": advisor["i_ID"]})
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
    
    return format_response(["ID Estudiante", "Nombre", "Depto.", "Créditos", "Asesor", "Depto. Asesor"], rows)


# ============================================
# CONSULTA 6: Estudiantes con 'A' en un curso
# ============================================
@router.post("/consulta/6")
def consulta_6(params: ConsultaParams):
    """Encontrar a todos los estudiantes que obtuvieron una 'A' en el curso X."""
    course_name = params.courseName
    if not course_name:
        raise HTTPException(status_code=400, detail="Falta el nombre o ID del curso")
    
    courses = get_courses()    # university["Course"]
    takes = get_takes()        # university["Takes"]
    students = get_students()  # university["Student"]
    
    # Buscar curso por ID o título
    course = courses.find_one({
        "$or": [
            {"course_id": course_name},
            {"title": {"$regex": f"^{course_name}$", "$options": "i"}}
        ]
    })
    
    if not course:
        raise HTTPException(status_code=404, detail=f"El curso '{course_name}' no existe")
    
    # Buscar estudiantes con A (incluye A, A-, A+)
    # Similar a: SELECT * FROM takes WHERE course_id = '401' AND grade LIKE 'A%'
    cursor = takes.find({
        "course_id": course["course_id"],
        "grade": {"$regex": "^A", "$options": "i"}
    })
    takes_list = list(cursor)
    
    if len(takes_list) == 0:
        return format_response(["Mensaje"], [[f"Ningún estudiante obtuvo 'A' en {course['title']}"]])
    
    rows = []
    for t in takes_list:
        student = students.find_one({"ID": t["ID"]})
        if student:
            rows.append([
                student["ID"],
                student["name"],
                student["dept_name"],
                t["grade"],
                t["semester"],
                str(t["year"])
            ])
    
    return format_response(["ID", "Nombre", "Departamento", "Calificación", "Semestre", "Año"], rows)


# ============================================
# CONSULTA 7: Estudiantes asesorados por profesor X
# ============================================
@router.post("/consulta/7")
def consulta_7(params: ConsultaParams):
    """Encontrar los nombres de todos los estudiantes asesorados por el profesor de nombre X."""
    professor_name = params.professorName
    if not professor_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del profesor")
    
    instructors = get_instructors()  # university["Instructor"]
    advisors = get_advisors()        # university["Advisor"]
    students = get_students()        # university["Student"]
    
    # Buscar instructor por nombre
    instructor = instructors.find_one({"name": {"$regex": f"^{professor_name}$", "$options": "i"}})
    
    if not instructor:
        raise HTTPException(status_code=404, detail=f"No se encontró profesor '{professor_name}'")
    
    # Buscar estudiantes asesorados por este instructor
    # Similar a: SELECT * FROM advisor WHERE i_ID = '63395'
    cursor = advisors.find({"i_ID": instructor["ID"]})
    advisor_list = list(cursor)
    
    if len(advisor_list) == 0:
        return format_response(["Mensaje"], [[f"El profesor {instructor['name']} no tiene estudiantes"]])
    
    rows = []
    for a in advisor_list:
        student = students.find_one({"ID": a["s_ID"]})
        if student:
            rows.append([
                student["ID"],
                student["name"],
                student["dept_name"],
                str(student["tot_cred"])
            ])
    
    return format_response(["ID", "Nombre", "Departamento", "Créditos"], rows)


# ============================================
# CONSULTA 8: Cursos que imparte un profesor
# ============================================
@router.post("/consulta/8")
def consulta_8(params: ConsultaParams):
    """Encontrar todos los cursos (título, horario y aula) que imparte el profesor de nombre X."""
    professor_name = params.professorName
    if not professor_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del profesor")
    
    instructors = get_instructors()  # university["Instructor"]
    teaches = get_teaches()          # university["Teaches"]
    sections = get_sections()        # university["Section"]
    courses = get_courses()          # university["Course"]
    time_slots = get_time_slots()    # university["Time_slot"]
    
    # Buscar instructor
    instructor = instructors.find_one({"name": {"$regex": f"^{professor_name}$", "$options": "i"}})
    
    if not instructor:
        raise HTTPException(status_code=404, detail=f"No se encontró profesor '{professor_name}'")
    
    # Buscar cursos que enseña
    # Similar a: SELECT * FROM teaches WHERE ID = '63395'
    cursor = teaches.find({"ID": instructor["ID"]})
    teaches_list = list(cursor)
    
    if len(teaches_list) == 0:
        return format_response(["Mensaje"], [[f"El profesor {instructor['name']} no imparte cursos"]])
    
    rows = []
    for t in teaches_list:
        course = courses.find_one({"course_id": t["course_id"]})
        section = sections.find_one({
            "course_id": t["course_id"],
            "sec_id": t["sec_id"],
            "semester": t["semester"],
            "year": t["year"]
        })
        
        aula = "N/A"
        horario = "N/A"
        if section:
            aula = f"{section['building']} {section['room_number']}"
            ts_cursor = time_slots.find({"time_slot_id": section["time_slot_id"]})
            ts_list = list(ts_cursor)
            if ts_list:
                horario = ", ".join([
                    f"{ts['day']} {ts['start_hr']}:{ts['start_min']:02d}-{ts['end_hr']}:{ts['end_min']:02d}"
                    for ts in ts_list
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
    
    return format_response(["ID Curso", "Título", "Sección", "Semestre", "Año", "Aula", "Horario"], rows)


# ============================================
# CONSULTA 9: Salario promedio por departamento
# ============================================
@router.post("/consulta/9")
def consulta_9(params: ConsultaParams):
    """Calcular el salario promedio por departamento."""
    instructors = get_instructors()  # university["Instructor"]
    
    # Usar agregación de MongoDB
    # Similar a: SELECT dept_name, AVG(salary) FROM instructor GROUP BY dept_name
    pipeline = [
        {
            "$group": {
                "_id": "$dept_name",
                "avg": {"$avg": "$salary"},
                "count": {"$sum": 1},
                "min": {"$min": "$salary"},
                "max": {"$max": "$salary"}
            }
        },
        {"$sort": {"avg": -1}}
    ]
    
    cursor = instructors.aggregate(pipeline)
    result = list(cursor)
    
    rows = []
    for r in result:
        rows.append([
            r["_id"],
            f"${r['avg']:,.2f}",
            str(r["count"]),
            f"${r['min']:,.2f}",
            f"${r['max']:,.2f}"
        ])
    
    return format_response(["Departamento", "Salario Promedio", "Profesores", "Mínimo", "Máximo"], rows)


# ============================================
# CONSULTA 10: Estudiantes de depto X con >90 créditos
# ============================================
@router.post("/consulta/10")
def consulta_10(params: ConsultaParams):
    """Encontrar todos los estudiantes del departamento X con más de 90 créditos."""
    dept_name = params.departmentName
    if not dept_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del departamento")
    
    students = get_students()  # university["Student"]
    
    # Buscar estudiantes
    # Similar a: SELECT * FROM student WHERE dept_name = 'History' AND tot_cred > 90
    cursor = students.find({
        "dept_name": {"$regex": f"^{dept_name}$", "$options": "i"},
        "tot_cred": {"$gt": 90}
    })
    student_list = list(cursor)
    
    if len(student_list) == 0:
        raise HTTPException(status_code=404, detail=f"No hay estudiantes en '{dept_name}' con >90 créditos")
    
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
    
    return format_response(["ID", "Nombre", "Departamento", "Créditos"], rows)
