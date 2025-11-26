# Backend Librebria API

API REST con FastAPI para consultas a MongoDB Atlas.

## 📋 Requisitos

- Python 3.9+
- MongoDB Atlas (ya configurado)

## 🚀 Instalación

1. Crear entorno virtual:
```bash
python -m venv venv
```

2. Activar entorno virtual:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
   - Editar el archivo `.env` con tu connection string de MongoDB Atlas

## ▶️ Ejecutar

```bash
uvicorn main:app --reload --port 8000
```

## 📚 Documentación API

Una vez ejecutando, acceder a:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔗 Endpoints Disponibles

### Books
- `GET /api/books` - Obtener todos los libros (paginado)
- `GET /api/books/count` - Contar total de libros
- `GET /api/books/search?q=texto&field=title` - Buscar libros
- `GET /api/books/{id}` - Obtener libro por ID

### Companies
- `GET /api/companies` - Obtener todas las compañías (paginado)
- `GET /api/companies/count` - Contar total de compañías
- `GET /api/companies/search?q=texto&field=name` - Buscar compañías
- `GET /api/companies/{id}` - Obtener compañía por ID

## 🔧 Parámetros de Paginación

- `skip`: Número de documentos a saltar (default: 0)
- `limit`: Máximo de documentos a retornar (default: 10, max: 100)
