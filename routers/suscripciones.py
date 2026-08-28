from fastapi import APIRouter, Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import schemas, crud.crud_suscripciones as crud_suscripciones, crud.crud_clientes as crud_clientes, crud.crud_planes as crud_planes

suscripcion_router = APIRouter(prefix="/suscripciones", tags=["Gestión de suscripciones"])

@suscripcion_router.post("/", response_model=schemas.SuscripcionResponse, status_code=status.HTTP_201_CREATED)
async def crear_suscripcion(suscripcion: schemas.SuscripcionCreate, db: AsyncSession = Depends(get_db)):
    # 1. Validar que el cliente exista
    cliente = await crud_clientes.obtener_cliente_por_id(db=db, cliente_id=suscripcion.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="El cliente especificado no existe")
    # 2. Validar que el plan de membresía exista
    plan = await crud_planes.obtener_plan_por_id(db=db, plan_id=suscripcion.plan_membresia_id)
    if not plan:
        raise HTTPException(status_code=404, detail="El plan de membresía especificado no existe")
    # 3. Crear suscripción calculando vigencia
    return await crud_suscripciones.crear_suscripcion(db=db, suscripcion=suscripcion, duracion_dias=plan.duracion_dias)

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