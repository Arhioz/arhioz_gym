from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from models import TipoTurno, TipoMembresia, EstadoSuscripcion, TipoUsuario, TipoEvento
from enums import TipoTurno, NombreRolEnum, TipoMembresia, TipoEvento, TipoUsuario, EstadoSuscripcion

# Configuracion base para lectura ORM desde SQLAlchemy
class BaseSchema(BaseModel): # Es lo mismo que BaseConfigModel, lee JSON, Diccionarios Y Objetos de SQLAlchemy, no solo JSON y diccionarios como BaseModel
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 1. SCHEMAS DE ROLES
# ==========================================

class RolBase(BaseSchema):
    nombre: str = Field(..., min_length=2, max_length=50, examples=["administrador", "entrenador"])
    descripcion: Optional[str] = Field(None, examples=["Acceso total al sistema"])

class RolCreate(RolBase):
    pass

class RolUpdate(BaseSchema):
    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    descripcion: Optional[str] = None

class RolResponse(RolBase):
    id: int

# ==========================================
# 2. SCHEMAS DE PLANES DE MEMBRESÍA
# ==========================================

class PlanMembresiaBase(BaseSchema):
    tipo_membresia: TipoMembresia
    duracion_dias: int = Field(..., gt=0, examples=[30])
    precio: float = Field(..., gt=0, examples=[550.00])

class PlanMembresiaCreate(PlanMembresiaBase):
    pass

class PlanMembresiaUpdate(BaseSchema):
    tipo_membresia: Optional[TipoMembresia] = None
    duracion_dias: Optional[int] = Field(None, gt=0)
    precio: Optional[float] = Field(None, gt=0)

class PlanMembresiaResponse(PlanMembresiaBase):
    id: int

# ==========================================
# 3. SCHEMAS DE SUSCRIPCIONES
# ==========================================

class SuscripcionBase(BaseSchema):
    cliente_id: int
    plan_membresia_id: int
    monto_pagado: float = Field(..., ge=0, examples=[550.00])

class SuscripcionCreate(SuscripcionBase):
    fecha_inicio: Optional[datetime] = None  # Si no se envía, la BD usa func.now()
    fecha_fin: Optional[datetime] = None
    estado: EstadoSuscripcion = EstadoSuscripcion.ACTIVA

class SuscripcionUpdate(BaseSchema):
    plan_membresia_id: Optional[int] = None
    monto_pagado: Optional[float] = Field(None, ge=0)
    estado: Optional[EstadoSuscripcion] = None
    fecha_fin: Optional[datetime] = None

class SuscripcionResponse(SuscripcionBase):
    id: int
    plan_membresia: Optional[PlanMembresiaResponse] = None
    plan_membresia_id: int
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    estado: Optional[EstadoSuscripcion] = None

# ==========================================
# 4. SCHEMAS DE PERSONAL
# ==========================================

class PersonalBase(BaseSchema):
    nombre: str = Field(..., min_length=2, max_length=80, description="Nombre del usuario", examples=["Arhioz Arthorias"])
    email: Optional[EmailStr] = Field(None, description="Correo electrónico válido", examples=["arhioz@gym.com"])
    telefono: Optional[str] = Field(None, max_length=20, description="Numero de telefono", examples=["6621234567"])
    turno: TipoTurno = Field(..., description="Turno matutino, vespertino, nocturno")
    horas_asignadas: int = Field(..., ge=1, le=300, description="Horas asignadas al usuario", examples=[40])

class PersonalCreate(PersonalBase):
    rol_nombre: NombreRolEnum
    password: Optional[str] = Field(None, min_length=6, description="Opcional si no tiene acceso al sistema")
    huella_hash: str = Field(..., description="Hash único registrado por el lector biométrico")

class PersonalProCreate(BaseSchema):
    nombre: str
    email: Optional[EmailStr]
    telefono: Optional[str]
    turno: Optional[TipoTurno]
    horas_asignadas: Optional[int]
    rol_nombre: Optional[NombreRolEnum]
    password: Optional[str]
    huella_hash: Optional[str]

class PersonalUpdate(BaseSchema):
    nombre: Optional[str] = Field(None, min_length=2, max_length=80)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    rol_id: Optional[int] = None
    password: Optional[str] = Field(None, min_length=6)
    turno: Optional[TipoTurno] = None
    horas_asignadas: Optional[int] = Field(None, ge=1, le=300)
    huella_hash: Optional[str] = None
    is_active: Optional[bool] = None

class PersonalResponse(PersonalBase):
    id: int
    rol_id: int
    huella_hash: str
    fecha_de_alta: datetime
    is_active: bool
    rol: Optional[RolResponse] = None  # Carga la relación si se usa selectionload

# ==========================================
# 5. SCHEMAS DE CLIENTES
# ==========================================

class ClienteBase(BaseSchema):
    nombre: str = Field(..., min_length=2, max_length=80, examples=["Zahori Starr"])
    edad: Optional[int] = Field(None, ge=12, le=100, examples=[28])
    telefono: Optional[str] = Field(None, max_length=20, examples=["6629876543"])
    email: Optional[EmailStr] = Field(None, examples=["zahori@email.com"])
    enfermedades: Optional[str] = Field(default="N/A")
    contacto_emergencia: Optional[str] = Field(None, max_length=80, examples=["Adamas Starr (Padre)"])
    telefono_emergencia: Optional[str] = Field(None, max_length=20, examples=["6621112233"])

class ClienteCreate(ClienteBase):
    rol_id: int = 2  # Por defecto rol Cliente en BD
    huella_hash: str = Field(..., description="Hash del biométrico del cliente")

class ClienteProCreate(BaseSchema):
    nombre: str
    edad: Optional[int]
    telefono: Optional[str]
    email: Optional[EmailStr]
    enfermedades: Optional[str]
    contacto_emergencia: Optional[str]
    telefono_emergencia: Optional[str]
    rol_id: int = 2
    huella_hash: Optional[str]
    
class ClienteUpdate(BaseSchema):
    nombre: Optional[str] = Field(None, min_length=2, max_length=80)
    edad: Optional[int] = Field(None, ge=12, le=100)
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    enfermedades: Optional[str] = None
    contacto_emergencia: Optional[str] = None
    telefono_emergencia: Optional[str] = None
    huella_hash: Optional[str] = None
    is_active: Optional[bool] = None

class ClienteResponse(ClienteBase):
    id: int
    rol_id: int
    huella_hash: str
    fecha_de_alta: datetime
    is_active: bool
    suscripciones: list[SuscripcionResponse] = []

class ClienteSimpleResponse(BaseSchema):
    id: int
    nombre: str
    is_active: bool

# ==========================================
# 6. SCHEMAS DE ASISTENCIAS / CHECK-IN
# ==========================================

class AsistenciaBase(BaseSchema):
    tipo_usuario: TipoUsuario
    tipo_evento: TipoEvento

class AsistenciaCreate(AsistenciaBase):
    huella_hash: str = Field(..., description="Hash leído del lector biométrico en puerta")
    # Nota: cliente_id o personal_id se resolverán internamente en el endpoint buscando la huella

class AsistenciaResponse(AsistenciaBase):
    id: int
    cliente_id: Optional[int] = None
    personal_id: Optional[int] = None
    fecha_evento: datetime
    
    # Datos resumidos opcionales para la respuesta en pantalla del checador
    cliente: Optional[ClienteResponse] = None
    personal: Optional[PersonalResponse] = None