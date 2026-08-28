from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import models, schemas

async def obtener_suscripcion_por_id(db: AsyncSession, suscripcion_id: int):
    query = select(models.Suscripcion).options(selectinload(models.Suscripcion.plan_membresia)).where(models.Suscripcion.id == suscripcion_id)
    resultado = await db.execute(query)
    return resultado.scalars().first()

async def obtener_suscripciones_por_cliente(db: AsyncSession, cliente_id: int):
    query = select(models.Suscripcion).options(selectinload(models.Suscripcion.plan_membresia)).where(models.Suscripcion.cliente_id == cliente_id)
    resultado = await db.execute(query)
    return resultado.scalars().all()

async def crear_suscripcion(db: AsyncSession, suscripcion: schemas.SuscripcionCreate, duracion_dias: int):
    fecha_inicio = datetime.utcnow()
    fecha_fin = fecha_inicio + timedelta(days=duracion_dias)

    nueva_suscripcion = models.Suscripcion(
        cliente_id=suscripcion.cliente_id,
        plan_membresia_id=suscripcion.plan_membresia_id,
        monto_pagado=suscripcion.monto_pagado,
        estado=suscripcion.estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    db.add(nueva_suscripcion)
    await db.commit()
    await db.refresh(nueva_suscripcion)
    return await obtener_suscripcion_por_id(db, nueva_suscripcion.id)

async def cambiar_estado_suscripcion(db: AsyncSession, suscripcion_db: models.Suscripcion, nuevo_estado: models.EstadoSuscripcion):
    suscripcion_db.estado = nuevo_estado
    await db.commit()
    await db.refresh(suscripcion_db)
    return suscripcion_db

async def eliminar_suscripcion(db: AsyncSession, suscripcion_db: models.Suscripcion):
    await db.delete(suscripcion_db)
    await db.commit()
    return suscripcion_db