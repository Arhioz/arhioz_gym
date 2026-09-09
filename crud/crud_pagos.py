import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models import Pago, Cliente, Suscripcion, Personal
import schemas

def generar_folio_unico() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    suffix = uuid.uuid4().hex[:4].upper()
    return f"REC-{timestamp}-{suffix}"

async def registrar_pago(db: AsyncSession, datos: schemas.PagoCreate):
    # 1. Validar que el cliente exista
    query = select(Cliente).where(Cliente.id == datos.cliente_id)
    resultado = await db.execute(query)
    if not resultado.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Cliente con ID {datos.cliente_id} no existe."
        )

    # 2. Validar suscripción si fue proporcionada
    if datos.suscripcion_id:
        query = select(Suscripcion).where(Suscripcion.id == datos.suscripcion_id)
        resultado = await db.execute(query)
        if not resultado.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Suscripción con ID {datos.suscripcion_id} no existe."
            )

    # 3. Validar recepcionista/personal si fue proporcionado
    if datos.personal_id:
        query = select(Personal).where(Personal.id == datos.personal_id)
        resultado = await db.execute(query)
        if not resultado.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empleado/Recepcionista con ID {datos.personal_id} no existe."
            )

    nuevo_pago = Pago(
        folio=generar_folio_unico(),
        monto=datos.monto,
        metodo_pago=datos.metodo_pago,
        concepto=datos.concepto,
        cliente_id=datos.cliente_id,
        suscripcion_id=datos.suscripcion_id,
        personal_id=datos.personal_id
    )

    db.add(nuevo_pago)
    await db.commit()
    await db.refresh(nuevo_pago)
    return nuevo_pago

async def obtener_pagos(db: AsyncSession, limit: int = 50):
    query = (
        select(Pago)
        .options(
            selectinload(Pago.cliente),
            selectinload(Pago.personal)
            .selectinload(Personal.rol)
        )
        .order_by(Pago.fecha_pago.desc())
        .limit(limit)
    )
    resultado = await db.execute(query)
    return resultado.scalars().all()

async def obtener_pagos_por_cliente(db: AsyncSession, cliente_id: int):
    query = (
        select(Pago)
        .options(
            selectinload(Pago.cliente),
            selectinload(Pago.personal)
            .selectinload(Personal.rol)
        )
        .where(Pago.cliente_id == cliente_id)
        .order_by(Pago.fecha_pago.desc())
    )
    resultado = await db.execute(query)
    return resultado.scalars().all()