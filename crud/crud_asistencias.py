from datetime import datetime, date, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from models import Personal, Cliente, Suscripcion, Asistencia
from schemas import AsistenciaCreate
from enums import TipoEvento, TipoUsuario

async def registrar_marcaje_biometrico(db: AsyncSession, datos: AsistenciaCreate):
    fecha_hora_actual = datetime.now()
    hoy = date.today()
    # Definimos el rango del día actual (00:00:00 hasta 23:59:59)
    inicio_dia = datetime.combine(hoy, time.min)
    fin_dia = datetime.combine(hoy, time.max)
    # 1. Buscar si la huella corresponde a un miembro del Personal
    stmt_personal = select(Personal).where(Personal.huella_hash == datos.huella_hash, Personal.is_active == True)
    res_personal = await db.execute(stmt_personal)
    personal = res_personal.scalars().first()
    
    if personal:
        # Lógica para Personal: Buscar únicamente el último marcaje DEL DÍA DE HOY
        stmt_ultima = (
            select(Asistencia)
            .where(
                Asistencia.personal_id == personal.id,
                Asistencia.fecha_evento >= inicio_dia,
                Asistencia.fecha_evento <= fin_dia
            )
            .order_by(Asistencia.fecha_evento.desc())
        )
        res_ultima = await db.execute(stmt_ultima)
        ultima_asistencia_hoy = res_ultima.scalars().first()
        
        # Determinar el tipo de evento:
        # - Si NO tiene registros hoy -> ENTRADA
        # - Si su último registro de hoy fue ENTRADA -> SALIDA
        # - Si su último registro de hoy fue SALIDA -> ENTRADA
        if not ultima_asistencia_hoy:
            nuevo_evento = TipoEvento.ENTRADA
        elif ultima_asistencia_hoy.tipo_evento == TipoEvento.ENTRADA:
            nuevo_evento = TipoEvento.SALIDA
        else:
            nuevo_evento = TipoEvento.ENTRADA
            
        nueva_asistencia = Asistencia(
            tipo_usuario=TipoUsuario.PERSONAL,
            personal_id=personal.id,
            tipo_evento=nuevo_evento,
            fecha_evento=fecha_hora_actual
        )
        db.add(nueva_asistencia)
        await db.commit()
        await db.refresh(nueva_asistencia)
        
        return {
            "mensaje": f"Marcaje exitoso ({nuevo_evento.value}) para el empleado {personal.nombre}",
            "usuario": personal.nombre,
            "tipo_usuario": "PERSONAL",
            "evento": nuevo_evento,
            "fecha_evento": fecha_hora_actual
        }

    # 2. Buscar si la huella corresponde a un Cliente
    stmt_cliente = select(Cliente).where(Cliente.huella_hash == datos.huella_hash, Cliente.is_active == True)
    res_cliente = await db.execute(stmt_cliente)
    cliente = res_cliente.scalars().first()
    
    if cliente:
        # Lógica para Clientes: Verificar vigencia de suscripción
        stmt_sub = select(Suscripcion).where(
            Suscripcion.cliente_id == cliente.id,
            Suscripcion.estado == "ACTIVA",
            Suscripcion.fecha_fin >= hoy
        )
        res_sub = await db.execute(stmt_sub)
        suscripcion_activa = res_sub.scalars().first()
        
        if not suscripcion_activa:
            # Denegamos el acceso directamente lanzando la excepción HTTP 403
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado a {cliente.nombre}: No cuenta con una membresía activa o vigente."
            )

        # Si cuenta con suscripción activa, registramos el evento como ENTRADA
        asistencia_permitida = Asistencia(
            tipo_usuario=TipoUsuario.CLIENTE,
            cliente_id=cliente.id,
            tipo_evento=TipoEvento.ENTRADA,
            fecha_evento=fecha_hora_actual
        )
        db.add(asistencia_permitida)
        await db.commit()
        await db.refresh(asistencia_permitida)
        
        return {
            "mensaje": f"Acceso permitido. Bienvenido(a) {cliente.nombre}",
            "usuario": cliente.nombre,
            "tipo_usuario": "CLIENTE",
            "evento": TipoEvento.ENTRADA,
            "fecha_evento": fecha_hora_actual
        }

    # 3. Huella no encontrada
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Huella dactilar no reconocida en el sistema."
    )

async def obtener_historial_personal(db: AsyncSession, limit: int = 50):
    """Obtiene únicamente las asistencias/checadas asociadas al personal del gimnasio."""
    stmt = (
        select(Asistencia)
        .options(
            selectinload(Asistencia.personal)
            .selectinload(Personal.rol)
        )
        .where(Asistencia.tipo_usuario == TipoUsuario.PERSONAL)
        .order_by(Asistencia.fecha_evento.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

async def obtener_historial_personal_por_id(db: AsyncSession, personal_id: int, limit: int = 50):
    """Obtiene únicamente las asistencias/checadas asociadas a un personal buscado por id."""
    stmt = (
        select(Asistencia)
        .options(
            selectinload(Asistencia.personal)
            .selectinload(Personal.rol)
        )
        .where(
            Asistencia.tipo_usuario == TipoUsuario.PERSONAL,
            Asistencia.personal_id == personal_id
        )
        .order_by(Asistencia.fecha_evento.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

async def buscar_historial_personal_por_nombre(db: AsyncSession, nombre: str, limit: int = 50):
    """Busca el historial de asistencias de personal filtrando por coincidencia en el nombre."""
    stmt = (
        select(Asistencia)
        .join(Asistencia.personal)
        .options(
            selectinload(Asistencia.personal)
            .selectinload(Personal.rol)
        )
        .where(
            Asistencia.tipo_usuario == TipoUsuario.PERSONAL,
            Personal.nombre.ilike(f"%{nombre}%")
        )
        .order_by(Asistencia.fecha_evento.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

async def obtener_historial_clientes(db: AsyncSession, limit: int = 50):
    """Obtiene únicamente las asistencias/entradas registradas por clientes."""
    stmt = (
        select(Asistencia)
        .options(
            selectinload(Asistencia.cliente)
            .selectinload(Cliente.suscripciones)
            .selectinload(Suscripcion.plan_membresia)
        )
        .where(Asistencia.tipo_usuario == TipoUsuario.CLIENTE)
        .order_by(Asistencia.fecha_evento.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

async def obtener_historial_cliente_por_id(db: AsyncSession, cliente_id: int, limit: int = 50):
    """Obtiene el historial de asistencias/accesos de un cliente específico por su ID."""
    stmt = (
        select(Asistencia)
        .options(
            selectinload(Asistencia.cliente)
            .selectinload(Cliente.suscripciones)
            .selectinload(Suscripcion.plan_membresia)
        )
        .where(
            Asistencia.tipo_usuario == TipoUsuario.CLIENTE,
            Asistencia.cliente_id == cliente_id
        )
        .order_by(Asistencia.fecha_evento.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

async def buscar_historial_clientes_por_nombre(db: AsyncSession, nombre: str, limit: int = 50):
    """Busca el historial de accesos de clientes filtrando por coincidencia en el nombre."""
    stmt = (
        select(Asistencia)
        .join(Asistencia.cliente)
        .options(
            selectinload(Asistencia.cliente)
            .selectinload(Cliente.suscripciones)
            .selectinload(Suscripcion.plan_membresia)
        )
        .where(
            Asistencia.tipo_usuario == TipoUsuario.CLIENTE,
            Cliente.nombre.ilike(f"%{nombre}%")
        )
        .order_by(Asistencia.fecha_evento.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()