from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.flights import router as flights_router
from backend.routes.ai import router as ai_router
from backend.routes.user_auth import router as user_auth_router
from backend.routes.admin_auth import router as admin_auth_router
from backend.routes.admin_users import router as admin_users_router
from backend.routes.booking import router as booking_router
from backend.routes.chat import router as chat_router
from backend.routes.payments import router as payments_router, bookings_payment_router as bookings_payment_router


app = FastAPI(
    title="Flight Booking API",
    description="Flight Booking API with MCP and AI Agent",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(flights_router)
app.include_router(ai_router)
app.include_router(user_auth_router)
app.include_router(admin_auth_router)
app.include_router(admin_users_router)
app.include_router(booking_router)
app.include_router(chat_router)
app.include_router(payments_router)
app.include_router(bookings_payment_router)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def home():
    return {
        "message": "Flight Booking API is running"
    }