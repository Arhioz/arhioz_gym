from fastapi import APIRouter, Path, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import auth, schemas, crud.crud_roles as crud_roles

rol_router = APIRouter(
    prefix="/roles",
    tags=["Catalogo de roles"],
    dependencies=[Depends(auth.RequiereRol(["administrador"]))]
)

# Endpoint para ver todos los roles
@rol_router.get("/", response_model=list[schemas.RolResponse])
async def obtener_roles(db: AsyncSession = Depends(get_db)):
    return await crud_roles.obtener_roles(db=db)

# Endpoint para crear un nuevo rol
@rol_router.post("/", response_model=schemas.RolResponse, status_code=status.HTTP_201_CREATED)
async def crear_rol(rol: schemas.RolCreate, db: AsyncSession = Depends(get_db)):
    return await crud_roles.crear_rol(db=db, rol=rol)

# Endpoint para eliminar un rol de la base de datos
@rol_router.delete("/{rol_id}", status_code=status.HTTP_200_OK)
async def eliminar_rol(rol_id: int, db: AsyncSession = Depends(get_db)):
    rol_db = await crud_roles.obtener_rol_por_id(db=db, rol_id=rol_id)
    if not rol_db:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    await crud_roles.eliminar_rol(db=db, rol_db=rol_db)
    return {"mensaje": f"Rol con ID {rol_id} eliminado exitosamente"}