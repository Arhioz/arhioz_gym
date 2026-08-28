from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import models, schemas

# Obtener plan de membresia por ID
async def obtener_plan_por_id(db: AsyncSession, plan_id: int):
    query = select(models.PlanMembresia).where(models.PlanMembresia.id == plan_id)
    resultado = await db.execute(query)
    return resultado.scalars().first()

# Ver todos los planes de membresias
async def obtener_planes(db: AsyncSession, skip: int = 0, limit: int = 20):
    query = select(models.PlanMembresia).offset(skip).limit(limit)
    resultado = await db.execute(query)
    return resultado.scalars().all()

# Crear nuevo plan de membresia
async def crear_plan(db: AsyncSession, plan: schemas.PlanMembresiaCreate):
    nuevo_plan = models.PlanMembresia(**plan.model_dump())
    db.add(nuevo_plan)
    await db.commit()
    await db.refresh(nuevo_plan)
    return nuevo_plan

# Actualizar datos de plan de membresia
async def actualizar_plan(db: AsyncSession, plan_db: models.PlanMembresia, datos_nuevos: schemas.PlanMembresiaUpdate):
    update_data = datos_nuevos.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan_db, field, value)
    await db.commit()
    await db.refresh(plan_db)
    return plan_db

# Eliminar un plan de membresia de la base de datos
async def eliminar_plan(db: AsyncSession, plan_db: models.PlanMembresia):
    await db.delete(plan_db)
    await db.commit()
    return plan_db