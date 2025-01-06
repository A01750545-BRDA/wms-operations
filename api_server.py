from fastapi import FastAPI
from api.routes import picking

def create_app() -> FastAPI:
    app = FastAPI(
        title='Warehouse Management API',
        description='API for warehouse management and picking operations',
        version='1.0.0'
    )
    
    app.include_router(picking.router, tags=['Picking'])
    
    return app