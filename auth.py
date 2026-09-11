from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import os
from typing import List, Union, Optional
import database, models
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
from dotenv import load_dotenv
from enums import NombreRolEnum

# Busca el archivo .env y carga sus valores en el sistema
load_dotenv()

# Asignar variables del entorno (.env)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Esquema OAuth2 que apunta a la ruta de inicio de sesión
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# --- GESTIÓN DE CONTRASEÑAS ---

# A. Convertir texto plano a Hash (para cuando el usuario se registra)
def get_password_hash(password: str) -> str:
    """Encripta una contraseña usando bcrypt."""
    # Convertimos el string a bytes
    password_bytes = password.encode('utf-8')
    # Generamos la salt (Conjunto de caracteres aleatorios únicos que se generan automáticamente antes de encriptar una contraseña) y el hash
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    # Lo devolvemos como string para guardarlo en la base de datos de forma sencilla
    return hashed_password.decode('utf-8')

# B. Verificar si una clave coincide con el hash (para el Login)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con el hash guardado."""
    # Convertimos ambos a bytes para que bcrypt pueda compararlos
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

# --- GESTIÓN DE TOKENS JWT ---

# C. Crear el Token JWT (el pasaporte digital)
def create_access_token(data: dict) -> str:
    """
    Genera un token JWT firmado.
    Se espera que `data` incluya:
      - 'sub': ID del usuario (str)
      - 'tipo_usuario': 'personal' | 'cliente'
      - 'rol': Nombre del rol
    """
    to_encode = data.copy()
    
    # Calculamos el tiempo de expiración
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Añadimos la expiración al paquete de datos
    to_encode.update({"exp": expire})
    
    # Firmamos el token con nuestra SECRET_KEY usando PyJWT
    token_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return token_jwt

# --- MIDDLEWARE DE AUTENTICACION ---
# Función para obtener al usuario actual a partir del Token
async def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(database.get_db)
) -> Union[models.Personal, models.Cliente]:
    """
    Obtiene al usuario actual (Personal o Cliente) evaluando el token JWT.
    """
    credenciales_invalidas_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales o sesión expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Intentamos decodificar el token con PyJWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        tipo_usuario: str = payload.get("tipo_usuario")
        if user_id is None or tipo_usuario is None:
            raise credenciales_invalidas_exception
        user_id_int = int(user_id)
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, ValueError):
        # Si el token está roto, corrupto o ya expiró
        raise credenciales_invalidas_exception
        
    # Búsqueda según la entidad del usuario
    if tipo_usuario == "personal":
        query = (
            select(models.Personal)
            .options(selectinload(models.Personal.rol))
            .where(models.Personal.id == user_id_int)
        )
        resultado = await db.execute(query)
        usuario = resultado.scalars().first()
        
    elif tipo_usuario == "cliente":
        query = select(models.Cliente).where(models.Cliente.id == user_id_int)
        resultado = await db.execute(query)
        usuario = resultado.scalars().first()
        
    else:
        raise credenciales_invalidas_exception

    if usuario is None or not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o no encontrado"
        )
        
    return usuario

# --- CONTROL DE ACCESO BASADO EN ROLES (RBAC) ---

class RequiereRol:
    """
    Clase inyectable para FastAPI que valida si el usuario autenticado
    posee uno de los roles autorizados.
    
    Uso en endpoints:
        @router.get("/admin-only", dependencies=[Depends(RequiereRol(["administrador"]))])
        @router.get("/recepcion-or-admin", dependencies=[Depends(RequiereRol(["administrador", "recepcion"]))])
    """
    def __init__(self, roles_permitidos: List[str]):
        self.roles_permitidos = [r.lower() for r in roles_permitidos]

    def __call__(self, usuario_actual: Union[models.Personal, models.Cliente] = Depends(obtener_usuario_actual)):
        # 1. Determinar el rol del usuario autenticado
        if isinstance(usuario_actual, models.Personal):
            rol_usuario = usuario_actual.rol.nombre.lower() if usuario_actual.rol else ""
        elif isinstance(usuario_actual, models.Cliente):
            rol_usuario = "cliente"
        else:
            rol_usuario = ""

        # 2. Permitir el paso si el rol está autorizado o si es Administrador
        if rol_usuario not in self.roles_permitidos and rol_usuario != "administrador":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No posees los permisos necesarios para realizar esta acción"
            )
            
        return usuario_actual