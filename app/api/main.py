#!/usr/bin/env python3
"""
Student Services Platform - Simplified Main API Application
Basic FastAPI application with simple admin authentication
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, HTTPException, Depends, Form, File, UploadFile, Cookie, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

# Import application modules
from app.models.database import get_db, init_database
from app.models.models import Order, User, Payment, Feedback
from app.services.auth import auth_service, get_current_admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("student-services")

# Initialize FastAPI app
app = FastAPI(
    title="Student Services Platform",
    description="Academic writing services platform with admin panel",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Basic security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """
    Basic security middleware
    """
    response = await call_next(request)
    
    # Basic security headers
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    return response

# Session cleanup middleware
@app.middleware("http")
async def cleanup_middleware(request: Request, call_next):
    """
    Cleanup expired sessions periodically
    """
    auth_service.cleanup_expired_sessions()
    response = await call_next(request)
    return response

# -------------------------------------------------
# Authentication Routes
# -------------------------------------------------

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: Optional[str] = None):
    """
    Admin login page
    """
    # Check if already logged in
    session_id = request.cookies.get("admin_session")
    if session_id:
        session_data = auth_service.verify_session(session_id)
        if session_data:
            return RedirectResponse(url="/admin", status_code=302)
    
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "error": error
    })

@app.post("/admin/login")
async def admin_login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Simple admin login endpoint
    """
    try:
        # Authenticate user
        if not auth_service.authenticate_admin(username, password):
            logger.warning(f"Failed login attempt for username: {username}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid username or password."}
            )
        
        # Create session
        ip_address = auth_service.get_client_ip(request)
        session_id = auth_service.create_session(username, ip_address)
        
        # Set cookie
        response.set_cookie(
            key="admin_session",
            value=session_id,
            max_age=8 * 60 * 60,  # 8 hours
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        logger.info(f"Admin login successful: {username}")
        
        return JSONResponse(
            status_code=200,
            content={"detail": "Login successful", "redirect": "/admin"}
        )
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An error occurred during login. Please try again."}
        )

@app.post("/admin/logout")
async def admin_logout(request: Request, response: Response):
    """
    Admin logout endpoint
    """
    session_id = request.cookies.get("admin_session")
    if session_id:
        auth_service.invalidate_session(session_id)
        response.delete_cookie("admin_session")
    
    return RedirectResponse(url="/admin/login", status_code=302)

# -------------------------------------------------
# Protected Admin Routes
# -------------------------------------------------

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin_session: dict = Depends(get_current_admin)):
    """
    Admin dashboard - main overview page
    """
    try:
        db = next(get_db())
        
        # Get dashboard statistics
        total_orders = db.query(Order).count()
        pending_orders = db.query(Order).filter(Order.status == 'pending').count()
        completed_orders = db.query(Order).filter(Order.status == 'completed').count()
        total_users = db.query(User).count()
        
        # Recent orders
        recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
        
        # Revenue calculation
        total_revenue = db.query(Order).filter(Order.payment_status == 'paid').with_entities(
            db.func.sum(Order.total_amount)
        ).scalar() or 0
        
        db.close()
        
        return templates.TemplateResponse("admin_dashboard.html", {
            "request": request,
            "admin_user": admin_session['username'],
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "total_users": total_users,
            "total_revenue": total_revenue,
            "recent_orders": recent_orders
        })
        
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error loading dashboard")

@app.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders(request: Request, admin_session: dict = Depends(get_current_admin)):
    """
    Admin orders management page
    """
    try:
        db = next(get_db())
        
        # Get all orders with user information
        orders = db.query(Order).join(User).order_by(Order.created_at.desc()).all()
        
        db.close()
        
        return templates.TemplateResponse("admin_orders.html", {
            "request": request,
            "admin_user": admin_session['username'],
            "orders": orders
        })
        
    except Exception as e:
        logger.error(f"Error loading admin orders: {e}")
        raise HTTPException(status_code=500, detail="Error loading orders")

@app.get("/admin/customers", response_class=HTMLResponse)
async def admin_customers(request: Request, admin_session: dict = Depends(get_current_admin)):
    """
    Admin customers management page
    """
    try:
        db = next(get_db())
        
        # Get all users with order statistics
        users = db.query(User).all()
        
        # Add order statistics for each user
        for user in users:
            user.order_count = db.query(Order).filter(Order.user_id == user.id).count()
            user.total_spent = db.query(Order).filter(
                Order.user_id == user.id,
                Order.payment_status == 'paid'
            ).with_entities(db.func.sum(Order.total_amount)).scalar() or 0
        
        db.close()
        
        return templates.TemplateResponse("admin_customers.html", {
            "request": request,
            "admin_user": admin_session['username'],
            "customers": users
        })
        
    except Exception as e:
        logger.error(f"Error loading admin customers: {e}")
        raise HTTPException(status_code=500, detail="Error loading customers")

@app.get("/admin/payments", response_class=HTMLResponse)
async def admin_payments(request: Request, admin_session: dict = Depends(get_current_admin)):
    """
    Admin payments management page
    """
    try:
        db = next(get_db())
        
        # Get all payments
        payments = db.query(Payment).join(Order).join(User).order_by(Payment.created_at.desc()).all()
        
        db.close()
        
        return templates.TemplateResponse("admin_payments.html", {
            "request": request,
            "admin_user": admin_session['username'],
            "payments": payments
        })
        
    except Exception as e:
        logger.error(f"Error loading admin payments: {e}")
        raise HTTPException(status_code=500, detail="Error loading payments")

@app.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request, admin_session: dict = Depends(get_current_admin)):
    """
    Admin analytics and reports page
    """
    try:
        db = next(get_db())
        
        # Get analytics data
        analytics_data = {
            'total_orders': db.query(Order).count(),
            'total_revenue': db.query(Order).filter(Order.payment_status == 'paid').with_entities(
                db.func.sum(Order.total_amount)
            ).scalar() or 0,
            'avg_order_value': db.query(Order).filter(Order.payment_status == 'paid').with_entities(
                db.func.avg(Order.total_amount)
            ).scalar() or 0,
            'conversion_rate': 0  # Calculate based on your metrics
        }
        
        # Monthly revenue data (last 12 months)
        monthly_revenue = []
        for i in range(12):
            month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            
            revenue = db.query(Order).filter(
                Order.payment_status == 'paid',
                Order.created_at >= month_start,
                Order.created_at < month_end
            ).with_entities(db.func.sum(Order.total_amount)).scalar() or 0
            
            monthly_revenue.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': float(revenue)
            })
        
        monthly_revenue.reverse()
        
        db.close()
        
        return templates.TemplateResponse("admin_analytics.html", {
            "request": request,
            "admin_user": admin_session['username'],
            "analytics": analytics_data,
            "monthly_revenue": monthly_revenue
        })
        
    except Exception as e:
        logger.error(f"Error loading admin analytics: {e}")
        raise HTTPException(status_code=500, detail="Error loading analytics")

@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, admin_session: dict = Depends(get_current_admin)):
    """
    Admin settings page
    """
    try:
        return templates.TemplateResponse("admin_settings.html", {
            "request": request,
            "admin_user": admin_session['username']
        })
        
    except Exception as e:
        logger.error(f"Error loading admin settings: {e}")
        raise HTTPException(status_code=500, detail="Error loading settings")

# -------------------------------------------------
# API Routes (Protected)
# -------------------------------------------------

@app.get("/api/orders")
async def get_orders(admin_session: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """
    Get all orders (API endpoint)
    """
    try:
        orders = db.query(Order).join(User).order_by(Order.created_at.desc()).all()
        
        orders_data = []
        for order in orders:
            orders_data.append({
                "id": order.id,
                "user_id": order.user_id,
                "user_name": f"{order.user.first_name} {order.user.last_name}",
                "service_type": order.service_type,
                "title": order.title,
                "status": order.status,
                "payment_status": order.payment_status,
                "total_amount": float(order.total_amount),
                "currency": order.currency,
                "created_at": order.created_at.isoformat(),
                "deadline": order.deadline.isoformat() if order.deadline else None
            })
        
        return JSONResponse(content={"orders": orders_data})
        
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail="Error fetching orders")

@app.put("/api/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str = Form(...),
    admin_session: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update order status
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = status
        order.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Order {order_id} status updated to {status} by {admin_session['username']}")
        
        return JSONResponse(content={"detail": "Order status updated successfully"})
        
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error updating order status")

@app.get("/api/users")
async def get_users(admin_session: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """
    Get all users (API endpoint)
    """
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        
        users_data = []
        for user in users:
            # Get user statistics
            order_count = db.query(Order).filter(Order.user_id == user.id).count()
            total_spent = db.query(Order).filter(
                Order.user_id == user.id,
                Order.payment_status == 'paid'
            ).with_entities(db.func.sum(Order.total_amount)).scalar() or 0
            
            users_data.append({
                "id": user.id,
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "country": user.country,
                "created_at": user.created_at.isoformat(),
                "order_count": order_count,
                "total_spent": float(total_spent)
            })
        
        return JSONResponse(content={"users": users_data})
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Error fetching users")

# -------------------------------------------------
# Health Check and Root Routes
# -------------------------------------------------

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "Student Services Platform API", "version": "2.0.0"}

# -------------------------------------------------
# Application Startup
# -------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """
    Application startup event
    """
    logger.info("Starting Student Services Platform...")
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    logger.info("Student Services Platform started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event
    """
    logger.info("Shutting down Student Services Platform...")

if __name__ == "__main__":
    uvicorn.run(
        "main_simplified:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
