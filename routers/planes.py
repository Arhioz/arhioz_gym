from fastapi import APIRouter, Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import schemas, crud.crud_planes as crud_planes, auth
from limiter import limiter

plan_router = APIRouter(prefix="/planes", tags=["Catálogo de planes de membresía"])

@plan_router.get("/", response_model=list[schemas.PlanMembresiaResponse])
@limiter.limit("10/minute")
async def obtener_planes(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    return await crud_planes.obtener_planes(db=db, skip=skip, limit=limit)

@plan_router.get("/{plan_id}", response_model=schemas.PlanMembresiaResponse)
@limiter.limit("10/minute")
async def obtener_plan_por_id(plan_id: int = Path(..., description="ID del plan"), db: AsyncSession = Depends(get_db)):
    plan = await crud_planes.obtener_plan_por_id(db=db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de membresía no encontrado")
    return plan

@plan_router.post("/", response_model=schemas.PlanMembresiaResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(auth.RequiereRol(["administrador", "recepcion"]))])
async def crear_plan(plan: schemas.PlanMembresiaCreate, db: AsyncSession = Depends(get_db)):
    return await crud_planes.crear_plan(db=db, plan=plan)

@plan_router.put("/{plan_id}", response_model=schemas.PlanMembresiaResponse, dependencies=[Depends(auth.RequiereRol(["administrador", "recepcion"]))])
async def actualizar_plan(plan_id: int, datos_nuevos: schemas.PlanMembresiaUpdate, db: AsyncSession = Depends(get_db)):
    plan_db = await crud_planes.obtener_plan_por_id(db=db, plan_id=plan_id)
    if not plan_db:
        raise HTTPException(status_code=404, detail="Plan no encontrado para actualizar")
    return await crud_planes.actualizar_plan(db=db, plan_db=plan_db, datos_nuevos=datos_nuevos)

@plan_router.delete("/{plan_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(auth.RequiereRol(["administrador", "recepcion"]))])
async def eliminar_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    plan_db = await crud_planes.obtener_plan_por_id(db=db, plan_id=plan_id)
    if not plan_db:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    await crud_planes.eliminar_plan(db=db, plan_db=plan_db)
    return {"mensaje": f"Plan con ID {plan_id} eliminado exitosamente"}