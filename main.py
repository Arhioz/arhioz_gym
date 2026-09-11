import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from routers import asistencias, auth, clientes, dashboard, pagos, personal, planes, roles, suscripciones
from limiter import limiter

load_dotenv()

app = FastAPI(
    title="Arhioz Gym API",
    description="Backend para sistema de gestion y administracion de gimnasio",
    version="1.0.0"
)

# --- CONFIGURACION RATE LIMITING ---
# 1. Asignamos el limitador al estado de la aplicación
app.state.limiter = limiter

# 2. Configuramos qué responder cuando alguien excede el límite (Error 429)
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Demasiadas peticiones",
            "mensaje": "Has superado el límite de peticiones permitido. Por favor, intenta más tarde."
        }
    )

# --- CONFIGURACIÓN CORS ---
origins_raw = os.getenv("ALLOWED_ORIGINS") 
origins = origins_raw.split(",") 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,           
    allow_methods=["*"],              
    allow_headers=["*"],              
)

# --- INCLUSIÓN DE ROUTERS ---
app.include_router(clientes.cliente_router)
app.include_router(roles.rol_router)
app.include_router(personal.personal_router)
app.include_router(planes.plan_router)
app.include_router(suscripciones.suscripcion_router)
app.include_router(asistencias.asistencia_router)
app.include_router(pagos.pago_router)
app.include_router(dashboard.dashboard_router)
app.include_router(auth.auth_router)

@app.get("/")
def read_root():
    return {"status": "Arhioz Gym API funcionando en Docker!"}
