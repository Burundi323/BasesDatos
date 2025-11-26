# Router para la colección Books
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from database import get_books_collection
from bson import ObjectId

router = APIRouter()

def serialize_doc(doc) -> dict:
    """Convertir documento MongoDB a dict serializable"""
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.get("/")
async def get_all_books(
    skip: int = Query(0, ge=0, description="Número de documentos a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Límite de documentos a retornar")
):
    """Obtener todos los libros con paginación"""
    collection = get_books_collection()
    cursor = collection.find().skip(skip).limit(limit)
    books = await cursor.to_list(length=limit)
    return [serialize_doc(book) for book in books]

@router.get("/count")
async def count_books():
    """Obtener el número total de libros"""
    collection = get_books_collection()
    count = await collection.count_documents({})
    return {"total": count}

@router.get("/search")
async def search_books(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    field: str = Query("title", description="Campo en el que buscar"),
    skip: int = 0,
    limit: int = 10
):
    """Buscar libros por un campo específico"""
    collection = get_books_collection()
    query = {field: {"$regex": q, "$options": "i"}}
    cursor = collection.find(query).skip(skip).limit(limit)
    books = await cursor.to_list(length=limit)
    return [serialize_doc(book) for book in books]

@router.get("/{book_id}")
async def get_book_by_id(book_id: str):
    """Obtener un libro por su ID"""
    collection = get_books_collection()
    
    try:
        book = await collection.find_one({"_id": ObjectId(book_id)})
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    return serialize_doc(book)
