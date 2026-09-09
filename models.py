from sqlalchemy import CheckConstraint, Column, Enum, Integer, Float, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from enums import TipoTurno, TipoMembresia, TipoEvento, TipoUsuario, EstadoSuscripcion, MetodoPago

# 1. Tabla de roles: Define los puestos permitidos para el personal del gimnasio
class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False) # 1 administrador, 2 cliente, 3 recepcion, 4 entrenador, 5 staff, 6 mantenimiento
    descripcion = Column(Text, nullable=True) # Descripcion de las responsabilidades del rol.

    rol_de_personal = relationship("Personal", back_populates="rol")

# 2. Tabla de personal: Almacena la información de los empleados
class Personal(Base):
    __tablename__ = "personal"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), index=True, nullable=False) # Nombre completo
    email = Column(String(50), unique=True, index=True, nullable=True)
    telefono = Column(String(20), unique=True, index=True, nullable=True)
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), index=True, nullable=False)
    password = Column(String, index=True, nullable=True)
    turno = Column(Enum(TipoTurno, name="tipoturno_enum"), nullable=False)
    horas_asignadas = Column(Integer, nullable=False)
    huella_hash = Column(String, unique=True, index=True, nullable=False) # Hash simulado de la huella dactilar para el checador
    fecha_de_alta = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True)

    rol = relationship("Rol", back_populates="rol_de_personal")
    asistencias = relationship("Asistencia", back_populates="personal", cascade="all, delete-orphan") # cascade="all, delete-orphan" se usa en relacion "Padre" hacie el "Hijo", ej. si eliminas a un personal se eliminaran sus asistencias.
    pagos = relationship("Pago", back_populates="personal")

# 3. Tabla de clientes: Almacena la información de los clientes
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), index=True, nullable=False) # Nombre completo
    edad = Column(Integer, nullable=True)
    telefono = Column(String(20), unique=True, index=True, nullable=True)
    email = Column(String(50), unique=True, index=True, nullable=True)
    enfermedades = Column(String, nullable=True)
    contacto_emergencia = Column(String(80), index=True, nullable=True)
    telefono_emergencia = Column(String(20), index=True, nullable=True)
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    huella_hash = Column(String, unique=True, index=True, nullable=False) # Hash simulado de la huella dactilar para acceso al gym
    fecha_de_alta = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True)

    suscripciones = relationship("Suscripcion", back_populates="cliente", cascade="all, delete-orphan") # cascade="all, delete-orphan", si eliminas un cliente, tambien se eliminan sus suscripciones y asistencias
    asistencias = relationship("Asistencia", back_populates="cliente", cascade="all, delete-orphan")
    pagos = relationship("Pago", back_populates="cliente")

# 4. Tabla de las diferentes membresias: Define los tipos de planes que el gimnasio ofrece (ej. Mensual, Trimestral, Anual)
class PlanMembresia(Base):
    __tablename__ = "planes_membresia"

    id = Column(Integer, primary_key=True, index=True)
    tipo_membresia = Column(Enum(TipoMembresia, name="tipomembresia_enum"), nullable=False)
    duracion_dias = Column(Integer, nullable=False)
    precio = Column(Float, nullable=False)

    suscripciones = relationship("Suscripcion", back_populates="plan_membresia")

# 5. Tabla de suscripciones: Relaciona al cliente con los planes que ha comprado, permitiendo llevar un historial transaccional exacto y control de deudas
class Suscripcion(Base):
    __tablename__ = "suscripciones"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), index=True, nullable=False)
    plan_membresia_id = Column(Integer, ForeignKey("planes_membresia.id", ondelete="CASCADE"), index=True, nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    monto_pagado = Column(Float, nullable=False)
    estado = Column(Enum(EstadoSuscripcion, name="estadosuscripcion_enum"), nullable=False)

    cliente = relationship("Cliente", back_populates="suscripciones")
    plan_membresia = relationship("PlanMembresia", back_populates="suscripciones")
    pagos = relationship("Pago", back_populates="suscripcion")

# 6. Tabla de asistencias del personal: Registro unificado tanto para el checador del personal como para los accesos de los clientes mediante la huella simulada
class Asistencia(Base):
    __tablename__ = "asistencias"

    id = Column(Integer, primary_key=True, index=True)
    tipo_usuario = Column(Enum(TipoUsuario, name="tipousuario_enum"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), index=True, nullable=True)
    personal_id = Column(Integer, ForeignKey("personal.id", ondelete="CASCADE"), index=True, nullable=True)
    tipo_evento = Column(Enum(TipoEvento, name="tipoevento_enum", nullable=False))
    fecha_evento = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cliente = relationship("Cliente", back_populates="asistencias")
    personal = relationship("Personal", back_populates="asistencias")

    # Para asegurarnos que un registro de asistencia pertenezca exclusivamente a un cliente o a un personal (Y no a ambos o a ninguno)
    __table_args__ = (
        CheckConstraint(
            "(cliente_id IS NOT NULL AND personal_id IS NULL) OR (cliente_id IS NULL AND personal_id IS NOT NULL)",
            name="check_asistencia_usuario_exclusivo"
        ),
    )

# 7. Tabla de pagos: Registro de ingresos, metodos de pago, folios, etc.
class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String, unique=True, index=True, nullable=False)
    monto = Column(Float, nullable=False)
    metodo_pago = Column(Enum(MetodoPago), nullable=False, default=MetodoPago.EFECTIVO)
    concepto = Column(String, nullable=True) # Ej: "Renovación Membresía Mensual"
    fecha_pago = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    suscripcion_id = Column(Integer, ForeignKey("suscripciones.id"), nullable=True)
    personal_id = Column(Integer, ForeignKey("personal.id"), nullable=True)

    cliente = relationship("Cliente", back_populates="pagos")
    suscripcion = relationship("Suscripcion", back_populates="pagos")
    personal = relationship("Personal", back_populates="pagos")