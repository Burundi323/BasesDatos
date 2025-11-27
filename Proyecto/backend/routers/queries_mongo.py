# Router para consultas MongoDB
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_mongo_collection

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
    
    courses = get_mongo_collection("Course")
    prereqs = get_mongo_collection("Prereq")
    
    course = await courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail=f"El curso '{course_id}' no existe")
    
    prereq_list = await prereqs.find({"course_id": course_id}).to_list(100)
    
    if not prereq_list:
        return format_response(["Mensaje"], [["Este curso no tiene prerrequisitos"]])
    
    rows = []
    for p in prereq_list:
        prereq_course = await courses.find_one({"course_id": p["prereq_id"]})
        if prereq_course:
            rows.append([prereq_course["course_id"], prereq_course["title"], 
                        prereq_course["dept_name"], str(prereq_course["credits"])])
    
    return format_response(["ID Prerrequisito", "Título", "Departamento", "Créditos"], rows)

# CONSULTA 2: Historial académico
@router.post("/consulta/2")
async def consulta_2(params: ConsultaParams):
    student_id = params.studentId
    if not student_id:
        raise HTTPException(status_code=400, detail="Falta el ID del estudiante")
    
    students = get_mongo_collection("Student")
    takes = get_mongo_collection("Takes")
    courses = get_mongo_collection("Course")
    
    student = await students.find_one({"ID": student_id})
    if not student:
        raise HTTPException(status_code=404, detail=f"El estudiante con ID '{student_id}' no existe")
    
    takes_list = await takes.find({"ID": student_id}).to_list(1000)
    
    if not takes_list:
        return format_response(["Mensaje"], [[f"El estudiante {student['name']} no tiene cursos registrados"]])
    
    rows = []
    for t in takes_list:
        course = await courses.find_one({"course_id": t["course_id"]})
        rows.append([t["course_id"], course["title"] if course else "N/A",
                    str(course["credits"]) if course else "0", t["semester"],
                    str(t["year"]), t["grade"] if t["grade"] else "N/A"])
    
    rows.sort(key=lambda x: (x[4], x[3]))
    return format_response(["ID Curso", "Título", "Créditos", "Semestre", "Año", "Calificación"], rows)

# CONSULTA 3: Detalles de sección
@router.post("/consulta/3")
async def consulta_3(params: ConsultaParams):
    sec_id = params.sectionId
    if not sec_id:
        raise HTTPException(status_code=400, detail="Falta el ID de la sección")
    
    sections = get_mongo_collection("Section")
    time_slots = get_mongo_collection("Time_slot")
    courses = get_mongo_collection("Course")
    
    section_list = await sections.find({"sec_id": sec_id}).to_list(100)
    
    if not section_list:
        raise HTTPException(status_code=404, detail=f"No se encontró la sección '{sec_id}'")
    
    rows = []
    for section in section_list:
        course = await courses.find_one({"course_id": section["course_id"]})
        time_slot_list = await time_slots.find({"time_slot_id": section["time_slot_id"]}).to_list(10)
        
        horario = ", ".join([f"{ts['day']} {ts['start_hr']}:{ts['start_min']:02d}-{ts['end_hr']}:{ts['end_min']:02d}"
                            for ts in time_slot_list]) if time_slot_list else "N/A"
        
        rows.append([section["course_id"], course["title"] if course else "N/A", section["sec_id"],
                    section["semester"], str(section["year"]), section["building"],
                    str(section["room_number"]), horario])
    
    return format_response(["ID Curso", "Título", "Sección", "Semestre", "Año", "Edificio", "Sala", "Horario"], rows)

# CONSULTA 4: Secciones por edificio
@router.post("/consulta/4")
async def consulta_4(params: ConsultaParams):
    building = params.building
    if not building:
        raise HTTPException(status_code=400, detail="Falta el nombre del edificio")
    
    sections = get_mongo_collection("Section")
    courses = get_mongo_collection("Course")
    
    section_list = await sections.find({"building": {"$regex": f"^{building}$", "$options": "i"}}).to_list(500)
    
    if not section_list:
        raise HTTPException(status_code=404, detail=f"No se encontraron secciones en el edificio '{building}'")
    
    rows = []
    for s in section_list:
        course = await courses.find_one({"course_id": s["course_id"]})
        rows.append([s["course_id"], course["title"] if course else "N/A", s["sec_id"],
                    s["semester"], str(s["year"]), str(s["room_number"]), s["time_slot_id"]])
    
    return format_response(["ID Curso", "Título", "Sección", "Semestre", "Año", "Sala", "Horario ID"], rows)

# CONSULTA 5: Estudiante y asesor
@router.post("/consulta/5")
async def consulta_5(params: ConsultaParams):
    student_name = params.studentName
    if not student_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del estudiante")
    
    students = get_mongo_collection("Student")
    advisors = get_mongo_collection("Advisor")
    instructors = get_mongo_collection("Instructor")
    
    student_list = await students.find({"name": {"$regex": f"^{student_name}$", "$options": "i"}}).to_list(100)
    
    if not student_list:
        raise HTTPException(status_code=404, detail=f"No se encontró estudiante con nombre '{student_name}'")
    
    rows = []
    for student in student_list:
        advisor = await advisors.find_one({"s_ID": student["ID"]})
        advisor_name, advisor_dept = "Sin asesor", "N/A"
        if advisor:
            instructor = await instructors.find_one({"ID": advisor["i_ID"]})
            if instructor:
                advisor_name, advisor_dept = instructor["name"], instructor["dept_name"]
        
        rows.append([student["ID"], student["name"], student["dept_name"],
                    str(student["tot_cred"]), advisor_name, advisor_dept])
    
    return format_response(["ID Estudiante", "Nombre", "Depto.", "Créditos", "Asesor", "Depto. Asesor"], rows)

# CONSULTA 6: Estudiantes con A
@router.post("/consulta/6")
async def consulta_6(params: ConsultaParams):
    course_name = params.courseName
    if not course_name:
        raise HTTPException(status_code=400, detail="Falta el nombre o ID del curso")
    
    courses = get_mongo_collection("Course")
    takes = get_mongo_collection("Takes")
    students = get_mongo_collection("Student")
    
    course = await courses.find_one({"$or": [{"course_id": course_name}, 
                                             {"title": {"$regex": f"^{course_name}$", "$options": "i"}}]})
    if not course:
        raise HTTPException(status_code=404, detail=f"El curso '{course_name}' no existe")
    
    takes_list = await takes.find({"course_id": course["course_id"], 
                                   "grade": {"$regex": "^A", "$options": "i"}}).to_list(1000)
    
    if not takes_list:
        return format_response(["Mensaje"], [[f"Ningún estudiante obtuvo 'A' en {course['title']}"]])
    
    rows = []
    for t in takes_list:
        student = await students.find_one({"ID": t["ID"]})
        if student:
            rows.append([student["ID"], student["name"], student["dept_name"],
                        t["grade"], t["semester"], str(t["year"])])
    
    return format_response(["ID", "Nombre", "Departamento", "Calificación", "Semestre", "Año"], rows)

# CONSULTA 7: Estudiantes por asesor
@router.post("/consulta/7")
async def consulta_7(params: ConsultaParams):
    professor_name = params.professorName
    if not professor_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del profesor")
    
    instructors = get_mongo_collection("Instructor")
    advisors = get_mongo_collection("Advisor")
    students = get_mongo_collection("Student")
    
    instructor = await instructors.find_one({"name": {"$regex": f"^{professor_name}$", "$options": "i"}})
    if not instructor:
        raise HTTPException(status_code=404, detail=f"No se encontró profesor '{professor_name}'")
    
    advisor_list = await advisors.find({"i_ID": instructor["ID"]}).to_list(500)
    
    if not advisor_list:
        return format_response(["Mensaje"], [[f"El profesor {instructor['name']} no tiene estudiantes"]])
    
    rows = []
    for a in advisor_list:
        student = await students.find_one({"ID": a["s_ID"]})
        if student:
            rows.append([student["ID"], student["name"], student["dept_name"], str(student["tot_cred"])])
    
    return format_response(["ID", "Nombre", "Departamento", "Créditos"], rows)

# CONSULTA 8: Cursos por profesor
@router.post("/consulta/8")
async def consulta_8(params: ConsultaParams):
    professor_name = params.professorName
    if not professor_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del profesor")
    
    instructors = get_mongo_collection("Instructor")
    teaches = get_mongo_collection("Teaches")
    sections = get_mongo_collection("Section")
    courses = get_mongo_collection("Course")
    time_slots = get_mongo_collection("Time_slot")
    
    instructor = await instructors.find_one({"name": {"$regex": f"^{professor_name}$", "$options": "i"}})
    if not instructor:
        raise HTTPException(status_code=404, detail=f"No se encontró profesor '{professor_name}'")
    
    teaches_list = await teaches.find({"ID": instructor["ID"]}).to_list(100)
    
    if not teaches_list:
        return format_response(["Mensaje"], [[f"El profesor {instructor['name']} no imparte cursos"]])
    
    rows = []
    for t in teaches_list:
        course = await courses.find_one({"course_id": t["course_id"]})
        section = await sections.find_one({"course_id": t["course_id"], "sec_id": t["sec_id"],
                                          "semester": t["semester"], "year": t["year"]})
        
        aula, horario = "N/A", "N/A"
        if section:
            aula = f"{section['building']} {section['room_number']}"
            ts_list = await time_slots.find({"time_slot_id": section["time_slot_id"]}).to_list(10)
            if ts_list:
                horario = ", ".join([f"{ts['day']} {ts['start_hr']}:{ts['start_min']:02d}-{ts['end_hr']}:{ts['end_min']:02d}" for ts in ts_list])
        
        rows.append([t["course_id"], course["title"] if course else "N/A", t["sec_id"],
                    t["semester"], str(t["year"]), aula, horario])
    
    return format_response(["ID Curso", "Título", "Sección", "Semestre", "Año", "Aula", "Horario"], rows)

# CONSULTA 9: Salario promedio
@router.post("/consulta/9")
async def consulta_9(params: ConsultaParams):
    instructors = get_mongo_collection("Instructor")
    
    pipeline = [
        {"$group": {"_id": "$dept_name", "avg": {"$avg": "$salary"}, "count": {"$sum": 1},
                   "min": {"$min": "$salary"}, "max": {"$max": "$salary"}}},
        {"$sort": {"avg": -1}}
    ]
    
    result = await instructors.aggregate(pipeline).to_list(100)
    rows = [[r["_id"], f"${r['avg']:,.2f}", str(r["count"]), 
             f"${r['min']:,.2f}", f"${r['max']:,.2f}"] for r in result]
    
    return format_response(["Departamento", "Salario Promedio", "Profesores", "Mínimo", "Máximo"], rows)

# CONSULTA 10: Estudiantes >90 créditos
@router.post("/consulta/10")
async def consulta_10(params: ConsultaParams):
    dept_name = params.departmentName
    if not dept_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del departamento")
    
    students = get_mongo_collection("Student")
    
    student_list = await students.find({"dept_name": {"$regex": f"^{dept_name}$", "$options": "i"},
                                        "tot_cred": {"$gt": 90}}).to_list(1000)
    
    if not student_list:
        raise HTTPException(status_code=404, detail=f"No hay estudiantes en '{dept_name}' con >90 créditos")
    
    rows = [[s["ID"], s["name"], s["dept_name"], str(s["tot_cred"])] for s in student_list]
    rows.sort(key=lambda x: int(x[3]), reverse=True)
    
    return format_response(["ID", "Nombre", "Departamento", "Créditos"], rows)
