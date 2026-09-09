from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from schemas import PagoCreate, PagoResponse
from crud import crud_pagos

pago_router = APIRouter(
    prefix="/pagos",
    tags=["Manejo de Transacciones y Cobros"]
)

@pago_router.post("/", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
async def procesar_cobro(datos: PagoCreate, db: AsyncSession = Depends(get_db)):
    """
    Registra un cobro/transacción, genera un folio autogenerado de recibo
    y lo almacena vinculado al cliente.
    """
    return await crud_pagos.registrar_pago(db, datos)

@pago_router.get("/", response_model=List[PagoResponse])
async def historial_transacciones(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """
    Lista las últimas transacciones y cobros registrados en la caja.
    """
    return await crud_pagos.obtener_pagos(db, limit)

@pago_router.get("/cliente/{cliente_id}", response_model=List[PagoResponse])
async def historial_pagos_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el historial completo de pagos realizados por un cliente en particular.
    """
    return await crud_pagos.obtener_pagos_por_cliente(db, cliente_id)