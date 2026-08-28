from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import models, schemas

#==================================
# --- OPERACIONES DE CLIENTE ---
#==================================
# 1 Buscar un cliente por su ID
async def obtener_cliente_por_id(db: AsyncSession, cliente_id: int):
    query = (
        select(models.Cliente)
        .options(
            selectinload(models.Cliente.suscripciones).selectinload(models.Suscripcion.plan_membresia)
        )
        .where(models.Cliente.id == cliente_id)
    )
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 1.1 Buscar cliente por su Nombre
async def obtener_cliente_por_nombre(db: AsyncSession, cliente_nombre: str):
    query = (
        select(models.Cliente)
        .options(
            selectinload(models.Cliente.suscripciones).selectinload(models.Suscripcion.plan_membresia)
        )
        .where(models.Cliente.nombre.ilike(cliente_nombre))
    )
    resultado = await db.execute(query)
    return resultado.scalars().first()

# 1.2 Buscar todos los clientes con el mismo nombre
async def buscar_todos_los_clientes_por_nombre(db: AsyncSession, cliente_nombre: str, skip: int = 0, limit: int = 20):
    # El uso de % antes y después busca el texto en cualquier parte del nombre (inicio, medio o fin)
    query = (
        select(models.Cliente)
        .options(
            selectinload(models.Cliente.suscripciones).selectinload(models.Suscripcion.plan_membresia)
        )
        .where(models.Cliente.nombre.ilike(f"%{cliente_nombre}%"))
        .offset(skip)
        .limit(limit)
    ) # ilike se encarga de ignorar mayúsculas y minúsculas ("juan" traerá "Juan", "JUAN", etc.)
    resultado = await db.execute(query)
    return resultado.scalars().all() # Usamos .all() para retornar una lista completa

# 1.3 Muestra todos los clientes
async def obtener_clientes(db: AsyncSession, skip: int = 0, limit: int = 20):
    query = (
        select(models.Cliente)
        .options(
            selectinload(models.Cliente.suscripciones).selectinload(models.Suscripcion.plan_membresia)
        )
        .offset(skip)
        .limit(limit)
    )
    resultado = await db.execute(query)
    return resultado.scalars().all()

# 2. Registrar un nuevo cliente en la base de datos
async def crear_cliente(db: AsyncSession, cliente: schemas.ClienteCreate):
    # model_dump(): Toma el objeto Pydantic cliente (recibido en el endpoint) y lo convierte en un diccionario de Python con formato clave: valor
    nuevo_cliente = models.Cliente(**cliente.model_dump()) # **: Toma las claves del diccionario y las desempaqueta como argumentos nombrados para el constructor del modelo de SQLAlchemy
    db.add(nuevo_cliente)
    await db.commit()
    await db.refresh(nuevo_cliente)
    return await obtener_cliente_por_id(db, nuevo_cliente.id)

# 2.1 Registra un nuevo cliente Pro sin restriccion de datos
async def crear_cliente_pro(db: AsyncSession, cliente_pro: schemas.ClienteProCreate):
    nuevo_cliente_pro = models.Cliente(**cliente_pro.model_dump())
    db.add(nuevo_cliente_pro)
    await db.commit()
    await db.refresh(nuevo_cliente_pro)
    return await obtener_cliente_por_id(db, nuevo_cliente_pro.id)

# 3. Actualizar los datos de un cliente
async def actualizar_datos_cliente(db: AsyncSession, cliente_db: models.Cliente, datos_nuevos: schemas.ClienteUpdate):
    # Convierte el esquema a diccionario extrayendo SOLO los datos enviados explícitamente
    update_data = datos_nuevos.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cliente_db, field, value)   
    await db.commit()
    await db.refresh(cliente_db)
    return await obtener_cliente_por_id(db, cliente_db.id)

# 4. Elimina un cliente de la DB
async def eliminar_cliente(db: AsyncSession, cliente_db: models.Cliente):
    await db.delete(cliente_db)
    await db.commit()
    return cliente_db