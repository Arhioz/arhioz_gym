from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
import schemas, auth
from crud import crud_dashboard

dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard y Analíticas"],
    dependencies=[Depends(auth.RequiereRol(["administrador"]))]
)

@dashboard_router.get("/resumen", response_model=schemas.DashboardResumenResponse)
async def obtener_resumen_metricas(db: AsyncSession = Depends(get_db)):
    """
    Obtiene las métricas agregadas del gimnasio (Ingresos, Clientes por estado y Planes más vendidos).
    """
    return await crud_dashboard.obtener_resumen_general(db)

@dashboard_router.get("/proximos-vencimientos", response_model=List[schemas.SuscripcionConClienteResponse])
async def obtener_alertas_vencimiento(dias: int = 7, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el listado de clientes cuyas suscripciones vencen en los próximos N días.
    """
    return await crud_dashboard.obtener_proximos_vencimientos(db, dias)