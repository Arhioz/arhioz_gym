from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, extract
from sqlalchemy.orm import selectinload

from models import Pago, Cliente, Suscripcion, PlanMembresia
from schemas import EstadoSuscripcion

async def obtener_resumen_general(db: AsyncSession):
    hoy = date.today()
    primer_dia_mes = datetime(hoy.year, hoy.month, 1)

    # 1. Finanzas: Totales e Ingresos del mes
    stmt_total_ingresos = select(func.coalesce(func.sum(Pago.monto), 0.0), func.count(Pago.id))
    res_total = await db.execute(stmt_total_ingresos)
    ingresos_totales, total_transacciones = res_total.first()

    stmt_mes_ingresos = select(func.coalesce(func.sum(Pago.monto), 0.0)).where(Pago.fecha_pago >= primer_dia_mes)
    res_mes = await db.execute(stmt_mes_ingresos)
    ingresos_mes = res_mes.scalar()

    # 2. Clientes por Estatus
    stmt_total_cli = select(func.count(Cliente.id))
    res_total_cli = await db.execute(stmt_total_cli)
    total_clientes = res_total_cli.scalar()

    stmt_activos = select(func.count(Suscripcion.id)).where(Suscripcion.estado == EstadoSuscripcion.ACTIVA)
    res_activos = await db.execute(stmt_activos)
    activos = res_activos.scalar()

    stmt_vencidos = select(func.count(Suscripcion.id)).where(Suscripcion.estado == EstadoSuscripcion.VENCIDA)
    res_vencidos = await db.execute(stmt_vencidos)
    vencidos = res_vencidos.scalar()

    stmt_cancelados = select(func.count(Suscripcion.id)).where(Suscripcion.estado == EstadoSuscripcion.CANCELADA)
    res_cancelados = await db.execute(stmt_cancelados)
    cancelados = res_cancelados.scalar()

    stmt_congelados = select(func.count(Suscripcion.id)).where(Suscripcion.estado == EstadoSuscripcion.CONGELADA)
    res_congelados = await db.execute(stmt_congelados)
    congelados = res_congelados.scalar()

    # 3. Planes más populares
    stmt_populares = (
        select(PlanMembresia.id, PlanMembresia.tipo_membresia, PlanMembresia.precio, func.count(Suscripcion.id).label("total"))
        .join(Suscripcion, Suscripcion.plan_membresia_id == PlanMembresia.id)
        .group_by(PlanMembresia.id, PlanMembresia.tipo_membresia, PlanMembresia.precio)
        .order_by(func.count(Suscripcion.id).desc())
        .limit(5)
    )
    res_populares = await db.execute(stmt_populares)
    populares = [
        {"plan_id": row[0], "tipo_membresia": row[1], "precio": row[2], "total_suscripciones": row[3]}
        for row in res_populares.all()
    ]

    return {
        "finanzas": {
            "ingresos_totales": ingresos_totales,
            "ingresos_mes_actual": ingresos_mes,
            "total_transacciones": total_transacciones
        },
        "clientes": {
            "total_clientes": total_clientes,
            "clientes_activos": activos,
            "clientes_vencidos": vencidos,
            "clientes_cancelados": cancelados,
            "clientes_congelados": congelados
        },
        "planes_populares": populares
    }

async def obtener_proximos_vencimientos(db: AsyncSession, dias: int = 7):
    hoy = date.today()
    fecha_limite = hoy + timedelta(days=dias)

    stmt = (
        select(Suscripcion)
        .options(selectinload(Suscripcion.cliente), selectinload(Suscripcion.plan_membresia))
        .where(
            Suscripcion.estado == EstadoSuscripcion.ACTIVA,
            Suscripcion.fecha_fin >= hoy,
            Suscripcion.fecha_fin <= fecha_limite
        )
        .order_by(Suscripcion.fecha_fin.asc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()