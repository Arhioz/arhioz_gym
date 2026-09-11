import os
from dotenv import load_dotenv
from fastapi import FastAPI
from routers import asistencias, auth, clientes, dashboard, pagos, personal, planes, roles, suscripciones

load_dotenv()

app = FastAPI(
    title="Arhioz Gym API",
    description="Backend para sistema de gestion y administracion de gimnasio",
    version="1.0.0"
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
