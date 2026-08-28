from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import models, schemas

#==================================
# --- OPERACIONES DE ROL ---
#==================================

# 1. Crear un nuevo rol en la base de datos
async def crear_rol(db: AsyncSession, rol: schemas.RolCreate):
    nuevo_rol = models.Rol(**rol.model_dump())
    db.add(nuevo_rol)
    await db.commit()
    await db.refresh(nuevo_rol)
    return nuevo_rol

# 2. Ver todos los roles
async def obtener_roles(db: AsyncSession):
    query = select(models.Rol)
    resultado = await db.execute(query)
    return resultado.scalars().all()

# 3. Buscar roles por ID
async def obtener_rol_por_id(db: AsyncSession, rol_id: int):
    query = select(models.Rol).where(models.Rol.id == rol_id)
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 4. Eliminar un rol de la base de datos
async def eliminar_rol(db: AsyncSession, rol_db: models.Rol):
    await db.delete(rol_db)
    await db.commit()
    return rol_db