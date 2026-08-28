from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import models, schemas

#==================================
# --- OPERACIONES DE PERSONAL ---
#==================================

# 1 Buscar un personal por su ID
async def obtener_personal_por_id(db: AsyncSession, personal_id: int):
    query = select(models.Personal).where(models.Personal.id == personal_id).options(selectinload(models.Personal.rol))
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 1.1 Buscar personal por su Nombre
async def obtener_personal_por_nombre(db: AsyncSession, personal_nombre: str):
    query = select(models.Personal).where(models.Personal.nombre.ilike(personal_nombre)).options(selectinload(models.Personal.rol))
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 1.2 Muestra todo el personal
async def obtener_personal(db: AsyncSession, skip: int = 0, limit: int = 10):
    query = select(models.Personal).options(selectinload(models.Personal.rol)).offset(skip).limit(limit)
    resultado = await db.execute(query)
    return resultado.scalars().all()

# 2. Registrar un nuevo personal en la base de datos
async def crear_personal(db: AsyncSession, personal: schemas.PersonalCreate, rol_id: int):
    # 1. Convertimos el esquema a diccionario Python
    datos_personal = personal.model_dump()
    # 2. Eliminamos 'rol_nombre' (que no es columna de la BD) y asignamos 'rol_id'
    datos_personal.pop("rol_nombre", None)
    datos_personal["rol_id"] = rol_id
    # 3. Ahora desempaquetamos un diccionario limpio que coincide exactamente con las columnas de SQLAlchemy
    nuevo_personal = models.Personal(**datos_personal)
    db.add(nuevo_personal)
    await db.commit()
    await db.refresh(nuevo_personal)
    # Cargamos explícitamente la relación 'rol' de forma asíncrona antes de retornarlo
    query = select(models.Personal).options(selectinload(models.Personal.rol)).where(models.Personal.id == nuevo_personal.id)
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 2.1 Registra un nuevo personal Pro sin restriccion de datos
async def crear_personal_pro(db: AsyncSession, personal_pro: schemas.PersonalProCreate):
    nuevo_personal_pro = models.Personal(**personal_pro.model_dump())
    db.add(nuevo_personal_pro)
    await db.commit()
    await db.refresh(nuevo_personal_pro)
    return nuevo_personal_pro

# 3. Actualizar los datos de un personal
async def actualizar_datos_personal(db: AsyncSession, personal_db: models.Personal, datos_nuevos: schemas.PersonalUpdate):
    # Convierte el esquema a diccionario extrayendo SOLO los datos enviados explícitamente
    update_data = datos_nuevos.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(personal_db, field, value)   
    await db.commit()
    await db.refresh(personal_db)
    return personal_db

# 4. Elimina un personal de la DB
async def eliminar_personal(db: AsyncSession, personal_db: models.Personal):
    await db.delete(personal_db)
    await db.commit()
    return personal_db