from fastapi import APIRouter
from api.schemas.request_models import PickingRequest, LatestOrderConfig
from api.schemas.response_models import PickingResponse
from services.picking_service import PickingService
from config.settings import Config, Settings

router = APIRouter(prefix='/picking')
picking_service = PickingService(is_testing=Settings.is_testing)

@router.post('/optimize', response_model=PickingResponse)
async def optimize_picking(request: PickingRequest) -> PickingResponse:
    picking_solution = picking_service.optimize(
        request.product_list,
        **request.config
    )

    return PickingResponse(
        paths=picking_solution.paths,
        summaries=picking_solution.summaries   
    )

@router.post('/latest-order', response_model=PickingResponse)
async def compute_latest_route(request: LatestOrderConfig = LatestOrderConfig()) -> PickingResponse:
    cursor = Config.postgres_conn.cursor()
    query = '''
    SELECT DISTINCT sop.sku
    FROM wms.scheduled_outbounds_products sop;
    '''
    cursor.execute(query)
    distinct_products = cursor.fetchall()

    map_products = {product[0]: f'Product_{i}' for i, product in enumerate(distinct_products, 1)}
    
    query = '''
    SELECT sop.sku, sop.cantidad
    FROM wms.scheduled_outbounds so
    JOIN wms.scheduled_outbounds_products sop ON so.uuid_outbound = sop.uuid_outbound;
    '''
    cursor.execute(query)
    picking_order = cursor.fetchall()
    cursor.close()
    
    product_list = {map_products[product]: quantity for product, quantity in picking_order}
    picking_solution = picking_service.optimize(
        product_list,
        **request.config
    )

    return PickingResponse(
        paths=picking_solution.paths,
        summaries=picking_solution.summaries   
    )