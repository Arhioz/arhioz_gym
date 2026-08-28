import enum

# 1. Enum para validar roles desde la API (Swagger UI dropdown)
class NombreRolEnum(str, enum.Enum):
    ADMINISTRADOR = "administrador"
    RECEPCION = "recepcion"
    ENTRENADOR = "entrenador"
    STAFF = "staff"
    MANTENIMIENTO = "mantenimiento"

# 2. Definimos el Enum nativo de Python (Podemos usar esta clase en otras tablas ej. Horarios, Asistencias)
class TipoTurno(str, enum.Enum):
    MATUTINO = "matutino"
    VESPERTINO = "vespertino"
    NOCTURNO = "nocturno"

# 3. Definimos el Enum para las diferentes membresias
class TipoMembresia(str, enum.Enum):
    DIA = "dia"
    SEMANA = "semana"
    MENSUAL = "mensual"
    TRIMESTRAL = "trimestral"
    SEMESTRAL = "semestral"
    ANUAL = "anual"
    OTRO = "otro"

# 4. Definimos el Enum para los diferentes estados de las suscripciones (ej. activa, vencida, cancelada)
class EstadoSuscripcion(str, enum.Enum):
    ACTIVA = "activa"
    VENCIDA = "vencida"
    CANCELADA = "cancelada"
    CONGELADA = "congelada"
    OTRO = "otro"

# 5. Definimos el Enum para diferenciar entre clientes o personal del gimnasio
class TipoUsuario(str, enum.Enum):
    CLIENTE = "cliente"
    PERSONAL = "personal"
    OTRO = "otro"

# 6. Definimos el Enum para diferenciar entre entrada o salida (Util para el personal). Para clientes, normalmente será solo acceso_permitido / acceso_denegado
class TipoEvento(str, enum.Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"