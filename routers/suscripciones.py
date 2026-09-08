from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from database import get_db
from enums import EstadoSuscripcion
import schemas, crud.crud_suscripciones as crud_suscripciones, crud.crud_clientes as crud_clientes, crud.crud_planes as crud_planes

suscripcion_router = APIRouter(prefix="/suscripciones", tags=["Gestión de suscripciones"])

@suscripcion_router.post("/", response_model=schemas.SuscripcionResponse, status_code=status.HTTP_201_CREATED)
async def crear_suscripcion(datos: schemas.SuscripcionCreate, db: AsyncSession = Depends(get_db)):
    """
    Registra/Renueva la suscripción de un cliente, calculando la fecha límite
    según la duración del plan contratado.
    """
    return await crud_suscripciones.crear_suscripcion(db, datos)

@suscripcion_router.put("/{suscripcion_id}/cambiar_estado", response_model=schemas.SuscripcionResponse)
async def cambiar_estado_suscripcion(suscripcion_id: int, nuevo_estado: EstadoSuscripcion, db: AsyncSession = Depends(get_db)):
    """
    Cambia directamente el estado de una suscripción usando el Enum de estados.
    """
    return await crud_suscripciones.cambiar_estado_suscripcion(db, suscripcion_id, nuevo_estado)

@suscripcion_router.put("/{suscripcion_id}/congelar", response_model=schemas.SuscripcionResponse)
async def congelar_membresia(suscripcion_id: int, db: AsyncSession = Depends(get_db)):
    """
    Pausa temporalmente una suscripción activa.
    """
    return await crud_suscripciones.congelar_suscripcion(db, suscripcion_id)

@suscripcion_router.put("/{suscripcion_id}/reactivar", response_model=schemas.SuscripcionResponse)
async def reactivar_membresia(suscripcion_id: int, db: AsyncSession = Depends(get_db)):
    """
    Reanuda una suscripción previamente congelada y recalcula la fecha de vencimiento.
    """
    return await crud_suscripciones.reactivar_suscripcion(db, suscripcion_id)

@suscripcion_router.get("/cliente/{cliente_id}", response_model=list[schemas.SuscripcionResponse])
async def obtener_suscripciones_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    return await crud_suscripciones.obtener_suscripciones_por_cliente(db=db, cliente_id=cliente_id)

@suscripcion_router.delete("/{suscripcion_id}", status_code=status.HTTP_200_OK)
async def eliminar_suscripcion(suscripcion_id: int, db: AsyncSession = Depends(get_db)):
    suscripcion_db = await crud_suscripciones.obtener_suscripcion_por_id(db=db, suscripcion_id=suscripcion_id)
    if not suscripcion_db:
        raise HTTPException(status_code=404, detail="Suscripcion no encontrada")
    await crud_suscripciones.eliminar_suscripcion(db=db, suscripcion_db=suscripcion_db)
    return {"mensaje": f"Suscripcion con ID {suscripcion_id} eliminada exitosamente"}