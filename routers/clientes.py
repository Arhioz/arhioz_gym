from fastapi import APIRouter, Path, Depends, Query, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import schemas, crud.crud_clientes as crud_clientes

cliente_router = APIRouter(
    prefix="/clientes",
    tags=["Catalogo de clientes"]
)

# Endpoint para mostrar el listado de todos los clientes
@cliente_router.get("/lista_completa", response_model=list[schemas.ClienteResponse])
async def obtener_clientes(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    resultado = await crud_clientes.obtener_clientes(db=db, skip=skip, limit=limit)
    if not resultado:
        raise HTTPException(status_code=404, detail="Aun no hay clientes registrados")
    return resultado

# Endpoint para buscar un cliente por ID
@cliente_router.get("/{cliente_id}", response_model=schemas.ClienteResponse)
async def obtener_cliente_por_id(cliente_id: int = Path(..., description="ID del cliente"), db: AsyncSession = Depends(get_db)):
    resultado = await crud_clientes.obtener_cliente_por_id(db=db, cliente_id=cliente_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return resultado

# Endpoint para buscar un cliente por nombre
@cliente_router.get("/buscar/{cliente_nombre}", response_model=schemas.ClienteResponse)
async def obtener_cliente_por_nombre(cliente_nombre: str = Path(..., description="Nombre del cliente"), db: AsyncSession = Depends(get_db)):
    resultado = await crud_clientes.obtener_cliente_por_nombre(db=db, cliente_nombre=cliente_nombre)
    if not resultado:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return resultado

# Endpoint para buscar todos los clientes con un mismo nombre
@cliente_router.get("/buscar/", response_model=list[schemas.ClienteResponse])
async def buscar_todos_los_clientes_por_nombre(cliente_nombre: str = Query(..., min_length=1, description="Nombre o parte del nombre a buscar"), db: AsyncSession = Depends(get_db)):
    resultado = await crud_clientes.buscar_todos_los_clientes_por_nombre(db=db, cliente_nombre=cliente_nombre)
    return resultado

# Endpoint para crear un nuevo cliente
@cliente_router.post("/", response_model=schemas.ClienteResponse, status_code=status.HTTP_201_CREATED)
async def crear_cliente(cliente: schemas.ClienteCreate, db: AsyncSession = Depends(get_db)):
    return await crud_clientes.crear_cliente(db=db, cliente=cliente)

# Endpoint para actualizar los datos de un cliente
@cliente_router.put("/{cliente_id}", response_model=schemas.ClienteResponse)
async def actualizar_cliente(cliente_id: int, datos_nuevos: schemas.ClienteUpdate, db: AsyncSession = Depends(get_db)):
    cliente_db = await crud_clientes.obtener_cliente_por_id(db=db, cliente_id=cliente_id)
    if not cliente_db:
        raise HTTPException(status_code=404, detail="Cliente no encontrado para actualizar")
    return await crud_clientes.actualizar_datos_cliente(db=db, cliente_db=cliente_db, datos_nuevos=datos_nuevos)

# Endpoint para eliminar un cliente de la base de datos
@cliente_router.delete("/{cliente_id}", status_code=status.HTTP_200_OK)
async def eliminar_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    cliente_db = await crud_clientes.obtener_cliente_por_id(db=db, cliente_id=cliente_id)
    if not cliente_db:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    await crud_clientes.eliminar_cliente(db=db, cliente_db=cliente_db)
    return {"mensaje": f"Cliente con ID {cliente_id} eliminado exitosamente"}