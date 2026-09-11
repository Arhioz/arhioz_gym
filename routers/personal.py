from fastapi import APIRouter, Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import auth, schemas, crud.crud_personal as crud_personal

personal_router = APIRouter(prefix="/personal", tags=["Catálogo de personal"], dependencies=[Depends(auth.RequiereRol(["administrador"]))])

# Endpoint para mostrar el listado de todo el personal
@personal_router.get("/lista_completa", response_model=list[schemas.PersonalResponse])
async def obtener_personal(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    return await crud_personal.obtener_personal(db=db, skip=skip, limit=limit)

# Endpoint para buscar un personal por ID
@personal_router.get("/{personal_id}", response_model=schemas.PersonalResponse)
async def obtener_personal_por_id(personal_id: int = Path(..., description="ID del empleado"), db: AsyncSession = Depends(get_db)):
    personal = await crud_personal.obtener_personal_por_id(db=db, personal_id=personal_id)
    if not personal:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return personal

# Endpoint para buscar un cliente por nombre
@personal_router.get("/buscar/{personal_nombre}", response_model=schemas.PersonalResponse)
async def obtener_personal_por_nombre(personal_nombre: str = Path(..., description="Nombre del personal"), db: AsyncSession = Depends(get_db)):
    resultado = await crud_personal.obtener_personal_por_nombre(db=db, personal_nombre=personal_nombre)
    if not resultado:
        raise HTTPException(status_code=404, detail="Personal no encontrado")
    return resultado

# Endpoint para crear un nuevo personal
@personal_router.post("/", response_model=schemas.PersonalResponse, status_code=status.HTTP_201_CREATED)
async def crear_personal(personal: schemas.PersonalCreate, db: AsyncSession = Depends(get_db)):
    # 1. Verificamos si existe
    db_personal = await crud_personal.obtener_personal_por_nombre(db, personal_nombre=personal.nombre)
    if db_personal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El usuario {personal.nombre} ya exite")
    # 2. Creamos el usuario en la DB
    nuevo_personal = await crud_personal.crear_personal(db=db, personal=personal)
    return nuevo_personal

# Endpoint para crear un nuevo personal pro
@personal_router.post("/pro", response_model=schemas.PersonalResponse, status_code=status.HTTP_201_CREATED)
async def crear_personal_pro(personal: schemas.PersonalProCreate, db: AsyncSession = Depends(get_db)):
    # 1. Verificamos si existe
    db_personal = await crud_personal.obtener_personal_por_nombre(db, personal_nombre=personal.nombre)
    if db_personal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El usuario {personal.nombre} ya exite")
    # 2. Creamos el usuario en la DB
    nuevo_personal_pro = await crud_personal.crear_personal_pro(db=db, personal=personal)
    return nuevo_personal_pro

# Endpoint para actualizar los datos de un personal
@personal_router.put("/{personal_id}", response_model=schemas.PersonalResponse)
async def actualizar_personal(personal_id: int, datos_nuevos: schemas.PersonalUpdate, db: AsyncSession = Depends(get_db)):
    personal_db = await crud_personal.obtener_personal_por_id(db=db, personal_id=personal_id)
    if not personal_db:
        raise HTTPException(status_code=404, detail="Empleado no encontrado para actualizar")
    return await crud_personal.actualizar_datos_personal(db=db, personal_db=personal_db, datos_nuevos=datos_nuevos)

# Endpoint para eliminar un personal de la base de datos
@personal_router.delete("/{personal_id}", status_code=status.HTTP_200_OK)
async def eliminar_personal(personal_id: int, db: AsyncSession = Depends(get_db)):
    personal_db = await crud_personal.obtener_personal_por_id(db=db, personal_id=personal_id)
    if not personal_db:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    await crud_personal.eliminar_personal(db=db, personal_db=personal_db)
    return {"mensaje": f"Empleado con ID {personal_id} eliminado exitosamente"}