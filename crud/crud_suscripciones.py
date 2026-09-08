from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import models, schemas

async def obtener_suscripcion_por_id(db: AsyncSession, suscripcion_id: int):
    query = select(models.Suscripcion).options(selectinload(models.Suscripcion.plan_membresia)).where(models.Suscripcion.id == suscripcion_id)
    resultado = await db.execute(query)
    return resultado.scalars().first()

async def obtener_suscripciones_por_cliente(db: AsyncSession, cliente_id: int):
    query = select(models.Suscripcion).options(selectinload(models.Suscripcion.plan_membresia)).where(models.Suscripcion.cliente_id == cliente_id)
    resultado = await db.execute(query)
    return resultado.scalars().all()

async def crear_suscripcion(db: AsyncSession, datos: schemas.SuscripcionCreate):
    # 1. Validar que el cliente existe
    query = select(models.Cliente).where(models.Cliente.id == datos.cliente_id)
    resultado = await db.execute(query)
    cliente = resultado.scalars().first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Cliente con ID {datos.cliente_id} no encontrado."
        )

    # 2. Validar que el plan de membresía existe
    query = select(models.PlanMembresia).where(models.PlanMembresia.id == datos.plan_membresia_id)
    resultado = await db.execute(query)
    plan = resultado.scalars().first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Plan de membresía con ID {datos.plan_id} no encontrado."
        )

    # 3. Desactivar cualquier suscripción activa anterior que tuviera el cliente
    query = select(models.Suscripcion).where(
        models.Suscripcion.cliente_id == datos.cliente_id,
        models.Suscripcion.estado == schemas.EstadoSuscripcion.ACTIVA
    )
    resultado = await db.execute(query)
    suscripciones_anteriores = resultado.scalars().all()
    
    for sub_ant in suscripciones_anteriores:
        sub_ant.estado = schemas.EstadoSuscripcion.CANCELADA

    # 4. Calcular fecha fin automática basada en la duración del plan
    fecha_inicio = datos.fecha_inicio or date.today()
    fecha_fin = fecha_inicio + timedelta(days=plan.duracion_dias)

    nueva_suscripcion = models.Suscripcion(
        cliente_id=datos.cliente_id,
        plan_membresia_id=datos.plan_membresia_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        monto_pagado=datos.monto_pagado if datos.monto_pagado is not None else plan.precio,
        estado=schemas.EstadoSuscripcion.ACTIVA
    )

    db.add(nueva_suscripcion)
    await db.commit()
    await db.refresh(nueva_suscripcion)

    # Re-consultar con relaciones para respuesta completa
    query = (
        select(models.Suscripcion)
        .options(selectinload(models.Suscripcion.cliente), selectinload(models.Suscripcion.plan_membresia))
        .where(models.Suscripcion.id == nueva_suscripcion.id)
    )
    resultado = await db.execute(query)
    return resultado.scalars().first()

async def cambiar_estado_suscripcion(db: AsyncSession, suscripcion_id: int, nuevo_estado: models.EstadoSuscripcion):
    query = select(models.Suscripcion).options(selectinload(models.Suscripcion.plan_membresia)).where(models.Suscripcion.id == suscripcion_id)
    resultado = await db.execute(query)
    suscripcion_db = resultado.scalars().first()
    
    if not suscripcion_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada.")

    suscripcion_db.estado = nuevo_estado
    await db.commit()
    await db.refresh(suscripcion_db)
    return suscripcion_db

async def congelar_suscripcion(db: AsyncSession, suscripcion_id: int):
    query = select(models.Suscripcion).options(selectinload(models.Suscripcion.plan_membresia)).where(models.Suscripcion.id == suscripcion_id)
    resultado = await db.execute(query)
    suscripcion = resultado.scalars().first()

    if not suscripcion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada.")

    if suscripcion.estado != schemas.EstadoSuscripcion.ACTIVA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Solo se pueden congelar suscripciones activas. Estado actual: {suscripcion.estado.value}"
        )

    suscripcion.estado = schemas.EstadoSuscripcion.CONGELADA
    await db.commit()
    await db.refresh(suscripcion)
    return suscripcion

async def reactivar_suscripcion(db: AsyncSession, suscripcion_id: int):
    query = select(models.Suscripcion).options(selectinload(models.Suscripcion.plan_membresia)).where(models.Suscripcion.id == suscripcion_id)
    resultado = await db.execute(query)
    suscripcion = resultado.scalars().first()

    if not suscripcion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada.")

    if suscripcion.estado != schemas.EstadoSuscripcion.CONGELADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Solo se pueden reactivar suscripciones en estado CONGELADA."
        )

    # Recalcular vigencia: conservar días restantes
    hoy = date.today()
    dias_restantes = (suscripcion.fecha_fin - suscripcion.fecha_inicio).days
    suscripcion.fecha_inicio = hoy
    suscripcion.fecha_fin = hoy + timedelta(days=dias_restantes)
    suscripcion.estado = schemas.EstadoSuscripcion.ACTIVA

    await db.commit()
    await db.refresh(suscripcion)
    return suscripcion

async def eliminar_suscripcion(db: AsyncSession, suscripcion_db: models.Suscripcion):
    await db.delete(suscripcion_db)
    await db.commit()
    return suscripcion_db