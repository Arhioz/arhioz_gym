from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
import auth, models, schemas
from limiter import limiter

auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticación y Seguridad"]
)

@auth_router.post("/login", response_model=schemas.TokenResponse)
@limiter.limit("5/minute")
async def login(
    credenciales: schemas.LoginRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint principal de inicio de sesión para Personal y Clientes.
    Busca coincidencias por correo electrónico o nombre de usuario/empleado.
    """
    # 1. Buscar primero en la tabla Personal (cargando su rol)
    query = (
        select(models.Personal)
        .options(selectinload(models.Personal.rol))
        .where(
            (models.Personal.email == credenciales.username_or_email) | 
            (models.Personal.nombre == credenciales.username_or_email)
        )
    )
    resultado = await db.execute(query)
    usuario_personal = resultado.scalars().first()

    if usuario_personal:
        if not usuario_personal.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario se encuentra inactivo."
            )
            
        if not auth.verify_password(credenciales.password, usuario_personal.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas."
            )

        nombre_rol = usuario_personal.rol.nombre.lower() if usuario_personal.rol else "staff"

        # Generar Token JWT
        token_data = {
            "sub": str(usuario_personal.id),
            "tipo_usuario": "personal",
            "rol": nombre_rol
        }
        access_token = auth.create_access_token(data=token_data)

        return schemas.TokenResponse(
            access_token=access_token,
            tipo_usuario="personal",
            nombre=usuario_personal.nombre,
            rol=nombre_rol
        )

    # 2. Si no es Personal, buscar en la tabla Cliente
    query = (
        select(models.Cliente)
        .where(
            (models.Cliente.email == credenciales.username_or_email) | 
            (models.Cliente.nombre == credenciales.username_or_email)
        )
    )
    resultado = await db.execute(query)
    usuario_cliente = resultado.scalars().first()

    if usuario_cliente:
        if not usuario_cliente.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cliente se encuentra inactivo."
            )

        if not auth.verify_password(credenciales.password, usuario_cliente.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas."
            )

        # Generar Token JWT para Cliente
        token_data = {
            "sub": str(usuario_cliente.id),
            "tipo_usuario": "cliente",
            "rol": "cliente"
        }
        access_token = auth.create_access_token(data=token_data)

        return schemas.TokenResponse(
            access_token=access_token,
            tipo_usuario="cliente",
            nombre=usuario_cliente.nombre,
            rol="cliente"
        )

    # 3. Usuario no encontrado en ninguna tabla
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas."
    )


@auth_router.post("/token", include_in_schema=False)
@limiter.limit("5/minute")
async def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint interno compatible con OAuth2PasswordRequestForm 
    utilizado por el botón 'Authorize' de Swagger UI.
    """
    req = schemas.LoginRequest(
        username_or_email=form_data.username,
        password=form_data.password
    )
    res = await login(credenciales=req, db=db)
    return {
        "access_token": res.access_token,
        "token_type": "bearer"
    }


@auth_router.get("/me")
@limiter.limit("20/minute")
async def obtener_perfil_actual(
    usuario_actual = Depends(auth.obtener_usuario_actual)
):
    """
    Retorna la información del usuario autenticado actualmente en base a su Token JWT.
    """
    return usuario_actual