from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from schemas import AsistenciaCreate, AsistenciaResponse
from crud import crud_asistencias
import auth
from limiter import limiter

asistencia_router = APIRouter(
    prefix="/asistencias",
    tags=["Asistencias y Checador"]
)

@asistencia_router.post("/scan", status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def escanear_huella(datos: AsistenciaCreate, db: AsyncSession = Depends(get_db)):
    """
    Simula la lectura de la huella dactilar.
    Valida internamente si corresponde a personal (Entrada/Salida) 
    o cliente (Verifica vigencia de membresía para permitir o denegar el paso).
    """
    return await crud_asistencias.registrar_marcaje_biometrico(db, datos)

@asistencia_router.get("/historial/personal", response_model=List[AsistenciaResponse], dependencies=[Depends(auth.RequiereRol(["administrador", "recepcion"]))])
async def ver_historial_personal(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el historial de marcajes (entradas y salidas) del personal.
    """
    return await crud_asistencias.obtener_historial_personal(db, limit)

@asistencia_router.get("/historial/personal/{personal_id}", response_model=List[AsistenciaResponse], dependencies=[Depends(auth.RequiereRol(["administrador", "recepcion"]))])
async def ver_historial_personal_por_id(personal_id: int, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el historial de marcajes de un empleado específico mediante su ID.
    """
    return await crud_asistencias.obtener_historial_personal_por_id(db, personal_id, limit)

@asistencia_router.get("/historial/buscar/personal", response_model=List[AsistenciaResponse], dependencies=[Depends(auth.RequiereRol(["administrador", "recepcion"]))])
async def buscar_historial_personal_por_nombre(
    nombre: str, 
    limit: int = 50, 
    db: AsyncSession = Depends(get_db)
):
    """
    Busca registros de checado de personal filtrando por nombre o apellido.
    """
    return await crud_asistencias.buscar_historial_personal_por_nombre(db, nombre, limit)

@asistencia_router.get("/historial/clientes", response_model=List[AsistenciaResponse], dependencies=[Depends(auth.RequiereRol(["administrador", "recepcion"]))])
async def ver_historial_clientes(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el historial de entradas registradas para clientes.
    """
    return await crud_asistencias.obtener_historial_clientes(db, limit)

@asistencia_router.get("/historial/clientes/{cliente_id}", response_model=List[AsistenciaResponse], dependencies=[Depends(auth.RequiereRol(["administrador", "recepcion"]))])
async def ver_historial_cliente_por_id(
    cliente_id: int, 
    limit: int = 50, 
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el historial de entradas/accesos de un cliente específico mediante su ID.
    """
    return await crud_asistencias.obtener_historial_cliente_por_id(db, cliente_id, limit)

@asistencia_router.get("/historial/buscar/clientes", response_model=List[AsistenciaResponse], dependencies=[Depends(auth.RequiereRol(["administrador", "recepcion"]))])
async def buscar_historial_clientes_por_nombre(
    nombre: str, 
    limit: int = 50, 
    db: AsyncSession = Depends(get_db)
):
    """
    Busca registros de accesos de clientes filtrando por nombre o apellido.
    """
    return await crud_asistencias.buscar_historial_clientes_por_nombre(db, nombre, limit)