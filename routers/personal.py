from fastapi import APIRouter, Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import schemas, crud.crud_personal as crud_personal, crud.crud_roles as crud_roles

personal_router = APIRouter(prefix="/personal", tags=["Catálogo de personal"])

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
    # 1. Buscamos el rol para obtener su ID correspondiente
    roles = await crud_roles.obtener_roles(db=db)
    rol_encontrado = next((r for r in roles if r.nombre.lower() == personal.rol_nombre.value.lower()), None)
    
    if not rol_encontrado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"El rol '{personal.rol_nombre.value}' no existe en la base de datos. Por favor créalo primero en /roles."
        )
        
    return await crud_personal.crear_personal(db=db, personal=personal, rol_id=rol_encontrado.id)

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