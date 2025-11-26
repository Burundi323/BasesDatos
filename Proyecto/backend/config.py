# Configuración de la aplicación
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB Atlas
    MONGODB_URL: str = "mongodb+srv://galiciaadri_db_user:7FKCqiCYz3E4nxrS@introbases.spkcuvc.mongodb.net/?retryWrites=true&w=majority"
    DATABASE_NAME: str = "Universidad"
    
    # API Settings
    API_TITLE: str = "Librebria API"
    API_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
