# Configuración de la aplicación
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB Atlas
    MONGODB_URL: str = "mongodb+srv://galiciaadri_db_user:7FKCqiCYz3E4nxrS@introbases.spkcuvc.mongodb.net/?retryWrites=true&w=majority"
    MONGODB_DATABASE: str = "Universidad"
    
    # MySQL
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "1234"
    MYSQL_DATABASE: str = "university"
    
    # API Settings
    API_TITLE: str = "Universidad API"
    API_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
