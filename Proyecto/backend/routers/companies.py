# Router para la colección Companies
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from database import get_companies_collection
from bson import ObjectId

router = APIRouter()

def serialize_doc(doc) -> dict:
    """Convertir documento MongoDB a dict serializable"""
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.get("/")
async def get_all_companies(
    skip: int = Query(0, ge=0, description="Número de documentos a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Límite de documentos a retornar")
):
    """Obtener todas las compañías con paginación"""
    collection = get_companies_collection()
    cursor = collection.find().skip(skip).limit(limit)
    companies = await cursor.to_list(length=limit)
    return [serialize_doc(company) for company in companies]

@router.get("/count")
async def count_companies():
    """Obtener el número total de compañías"""
    collection = get_companies_collection()
    count = await collection.count_documents({})
    return {"total": count}

@router.get("/search")
async def search_companies(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    field: str = Query("name", description="Campo en el que buscar"),
    skip: int = 0,
    limit: int = 10
):
    """Buscar compañías por un campo específico"""
    collection = get_companies_collection()
    query = {field: {"$regex": q, "$options": "i"}}
    cursor = collection.find(query).skip(skip).limit(limit)
    companies = await cursor.to_list(length=limit)
    return [serialize_doc(company) for company in companies]

@router.get("/{company_id}")
async def get_company_by_id(company_id: str):
    """Obtener una compañía por su ID"""
    collection = get_companies_collection()
    
    try:
        company = await collection.find_one({"_id": ObjectId(company_id)})
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    if not company:
        raise HTTPException(status_code=404, detail="Compañía no encontrada")
    
    return serialize_doc(company)
