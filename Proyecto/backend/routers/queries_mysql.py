# Router para consultas MySQL
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import execute_query, execute_query_one

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

# CONSULTA 1: Prerrequisitos de un curso
@router.post("/consulta/1")
async def consulta_1(params: ConsultaParams):
    course_id = params.courseId
    if not course_id:
        raise HTTPException(status_code=400, detail="Falta el ID del curso")
    
    course = await execute_query_one("SELECT * FROM course WHERE course_id = %s", (course_id,))
    if not course:
        raise HTTPException(status_code=404, detail=f"El curso '{course_id}' no existe")
    
    prereqs = await execute_query("""
        SELECT c.course_id, c.title, c.dept_name, c.credits
        FROM prereq p JOIN course c ON p.prereq_id = c.course_id
        WHERE p.course_id = %s
    """, (course_id,))
    
    if not prereqs:
        return format_response(["Mensaje"], [["Este curso no tiene prerrequisitos"]])
    
    rows = [[p["course_id"], p["title"], p["dept_name"], str(p["credits"])] for p in prereqs]
    return format_response(["ID Prerrequisito", "Título", "Departamento", "Créditos"], rows)

# CONSULTA 2: Historial académico
@router.post("/consulta/2")
async def consulta_2(params: ConsultaParams):
    student_id = params.studentId
    if not student_id:
        raise HTTPException(status_code=400, detail="Falta el ID del estudiante")
    
    student = await execute_query_one("SELECT * FROM student WHERE ID = %s", (student_id,))
    if not student:
        raise HTTPException(status_code=404, detail=f"El estudiante con ID '{student_id}' no existe")
    
    takes = await execute_query("""
        SELECT t.course_id, c.title, c.credits, t.semester, t.year, t.grade
        FROM takes t JOIN course c ON t.course_id = c.course_id
        WHERE t.ID = %s ORDER BY t.year, t.semester
    """, (student_id,))
    
    if not takes:
        return format_response(["Mensaje"], [[f"El estudiante {student['name']} no tiene cursos"]])
    
    rows = [[t["course_id"], t["title"], str(t["credits"]), t["semester"], 
             str(t["year"]), t["grade"] or "N/A"] for t in takes]
    return format_response(["ID Curso", "Título", "Créditos", "Semestre", "Año", "Calificación"], rows)

# CONSULTA 3: Detalles de sección
@router.post("/consulta/3")
async def consulta_3(params: ConsultaParams):
    sec_id = params.sectionId
    if not sec_id:
        raise HTTPException(status_code=400, detail="Falta el ID de la sección")
    
    sections = await execute_query("""
        SELECT s.course_id, c.title, s.sec_id, s.semester, s.year, 
               s.building, s.room_number, s.time_slot_id
        FROM section s JOIN course c ON s.course_id = c.course_id
        WHERE s.sec_id = %s
    """, (sec_id,))
    
    if not sections:
        raise HTTPException(status_code=404, detail=f"No se encontró la sección '{sec_id}'")
    
    rows = []
    for s in sections:
        time_slots = await execute_query(
            "SELECT day, start_hr, start_min, end_hr, end_min FROM time_slot WHERE time_slot_id = %s",
            (s["time_slot_id"],))
        horario = ", ".join([f"{ts['day']} {ts['start_hr']}:{ts['start_min']:02d}-{ts['end_hr']}:{ts['end_min']:02d}"
                            for ts in time_slots]) if time_slots else "N/A"
        rows.append([s["course_id"], s["title"], s["sec_id"], s["semester"],
                    str(s["year"]), s["building"], str(s["room_number"]), horario])
    
    return format_response(["ID Curso", "Título", "Sección", "Semestre", "Año", "Edificio", "Sala", "Horario"], rows)

# CONSULTA 4: Secciones por edificio
@router.post("/consulta/4")
async def consulta_4(params: ConsultaParams):
    building = params.building
    if not building:
        raise HTTPException(status_code=400, detail="Falta el nombre del edificio")
    
    sections = await execute_query("""
        SELECT s.course_id, c.title, s.sec_id, s.semester, s.year, s.room_number, s.time_slot_id
        FROM section s JOIN course c ON s.course_id = c.course_id
        WHERE LOWER(s.building) = LOWER(%s)
    """, (building,))
    
    if not sections:
        raise HTTPException(status_code=404, detail=f"No hay secciones en '{building}'")
    
    rows = [[s["course_id"], s["title"], s["sec_id"], s["semester"], 
             str(s["year"]), str(s["room_number"]), s["time_slot_id"]] for s in sections]
    return format_response(["ID Curso", "Título", "Sección", "Semestre", "Año", "Sala", "Horario ID"], rows)

# CONSULTA 5: Estudiante y asesor
@router.post("/consulta/5")
async def consulta_5(params: ConsultaParams):
    student_name = params.studentName
    if not student_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del estudiante")
    
    results = await execute_query("""
        SELECT s.ID, s.name as student_name, s.dept_name as student_dept, s.tot_cred,
               i.name as advisor_name, i.dept_name as advisor_dept
        FROM student s
        LEFT JOIN advisor a ON s.ID = a.s_ID
        LEFT JOIN instructor i ON a.i_ID = i.ID
        WHERE LOWER(s.name) = LOWER(%s)
    """, (student_name,))
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No se encontró estudiante '{student_name}'")
    
    rows = [[r["ID"], r["student_name"], r["student_dept"], str(r["tot_cred"]),
             r["advisor_name"] or "Sin asesor", r["advisor_dept"] or "N/A"] for r in results]
    return format_response(["ID", "Nombre", "Depto.", "Créditos", "Asesor", "Depto. Asesor"], rows)

# CONSULTA 6: Estudiantes con A
@router.post("/consulta/6")
async def consulta_6(params: ConsultaParams):
    course_name = params.courseName
    if not course_name:
        raise HTTPException(status_code=400, detail="Falta el nombre o ID del curso")
    
    course = await execute_query_one(
        "SELECT * FROM course WHERE course_id = %s OR LOWER(title) = LOWER(%s)",
        (course_name, course_name))
    if not course:
        raise HTTPException(status_code=404, detail=f"El curso '{course_name}' no existe")
    
    students = await execute_query("""
        SELECT s.ID, s.name, s.dept_name, t.grade, t.semester, t.year
        FROM takes t JOIN student s ON t.ID = s.ID
        WHERE t.course_id = %s AND t.grade LIKE 'A%%'
    """, (course["course_id"],))
    
    if not students:
        return format_response(["Mensaje"], [[f"Nadie obtuvo 'A' en {course['title']}"]])
    
    rows = [[s["ID"], s["name"], s["dept_name"], s["grade"], s["semester"], str(s["year"])] for s in students]
    return format_response(["ID", "Nombre", "Departamento", "Calificación", "Semestre", "Año"], rows)

# CONSULTA 7: Estudiantes por asesor
@router.post("/consulta/7")
async def consulta_7(params: ConsultaParams):
    professor_name = params.professorName
    if not professor_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del profesor")
    
    instructor = await execute_query_one(
        "SELECT * FROM instructor WHERE LOWER(name) = LOWER(%s)", (professor_name,))
    if not instructor:
        raise HTTPException(status_code=404, detail=f"No se encontró profesor '{professor_name}'")
    
    students = await execute_query("""
        SELECT s.ID, s.name, s.dept_name, s.tot_cred
        FROM advisor a JOIN student s ON a.s_ID = s.ID
        WHERE a.i_ID = %s
    """, (instructor["ID"],))
    
    if not students:
        return format_response(["Mensaje"], [[f"El profesor {instructor['name']} no tiene estudiantes"]])
    
    rows = [[s["ID"], s["name"], s["dept_name"], str(s["tot_cred"])] for s in students]
    return format_response(["ID", "Nombre", "Departamento", "Créditos"], rows)

# CONSULTA 8: Cursos por profesor
@router.post("/consulta/8")
async def consulta_8(params: ConsultaParams):
    professor_name = params.professorName
    if not professor_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del profesor")
    
    instructor = await execute_query_one(
        "SELECT * FROM instructor WHERE LOWER(name) = LOWER(%s)", (professor_name,))
    if not instructor:
        raise HTTPException(status_code=404, detail=f"No se encontró profesor '{professor_name}'")
    
    teaches = await execute_query("""
        SELECT t.course_id, c.title, t.sec_id, t.semester, t.year,
               s.building, s.room_number, s.time_slot_id
        FROM teaches t
        JOIN course c ON t.course_id = c.course_id
        LEFT JOIN section s ON t.course_id = s.course_id AND t.sec_id = s.sec_id 
                            AND t.semester = s.semester AND t.year = s.year
        WHERE t.ID = %s
    """, (instructor["ID"],))
    
    if not teaches:
        return format_response(["Mensaje"], [[f"El profesor {instructor['name']} no imparte cursos"]])
    
    rows = []
    for t in teaches:
        aula = f"{t['building']} {t['room_number']}" if t["building"] else "N/A"
        horario = "N/A"
        if t["time_slot_id"]:
            ts = await execute_query(
                "SELECT day, start_hr, start_min, end_hr, end_min FROM time_slot WHERE time_slot_id = %s",
                (t["time_slot_id"],))
            if ts:
                horario = ", ".join([f"{x['day']} {x['start_hr']}:{x['start_min']:02d}-{x['end_hr']}:{x['end_min']:02d}" for x in ts])
        rows.append([t["course_id"], t["title"], t["sec_id"], t["semester"], str(t["year"]), aula, horario])
    
    return format_response(["ID Curso", "Título", "Sección", "Semestre", "Año", "Aula", "Horario"], rows)

# CONSULTA 9: Salario promedio
@router.post("/consulta/9")
async def consulta_9(params: ConsultaParams):
    results = await execute_query("""
        SELECT dept_name, AVG(salary) as avg_salary, COUNT(*) as total,
               MIN(salary) as min_salary, MAX(salary) as max_salary
        FROM instructor GROUP BY dept_name ORDER BY avg_salary DESC
    """)
    
    rows = [[r["dept_name"], f"${r['avg_salary']:,.2f}", str(r["total"]),
             f"${r['min_salary']:,.2f}", f"${r['max_salary']:,.2f}"] for r in results]
    return format_response(["Departamento", "Salario Promedio", "Profesores", "Mínimo", "Máximo"], rows)

# CONSULTA 10: Estudiantes >90 créditos
@router.post("/consulta/10")
async def consulta_10(params: ConsultaParams):
    dept_name = params.departmentName
    if not dept_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del departamento")
    
    students = await execute_query("""
        SELECT ID, name, dept_name, tot_cred FROM student
        WHERE LOWER(dept_name) = LOWER(%s) AND tot_cred > 90
        ORDER BY tot_cred DESC
    """, (dept_name,))
    
    if not students:
        raise HTTPException(status_code=404, detail=f"No hay estudiantes en '{dept_name}' con >90 créditos")
    
    rows = [[s["ID"], s["name"], s["dept_name"], str(s["tot_cred"])] for s in students]
    return format_response(["ID", "Nombre", "Departamento", "Créditos"], rows)
