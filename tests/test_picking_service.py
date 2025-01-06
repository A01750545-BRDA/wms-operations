import os
import json
from services.picking_service import PickingService
from utils.helpers import animate_computed_multiple_paths

def load_test_product_list(filename):
    with open(os.path.join('tests', 'product_lists', filename), 'r') as file:
        return json.load(file)
    
def test_optimize_picking(
        filename: str,
        start_id: str = 'start', 
        dest_id: str = 'dest1', 
        num_routes: int = 1,
        animate: bool = False
    ):
    product_list = load_test_product_list(filename)
    
    picking_service = PickingService(is_testing=True)
    picking_solution = picking_service.optimize(
        product_list, 
        start_id=start_id,
        dest_id=dest_id,
        num_routes=num_routes, 
        debug=False
    )

    print('-'*10)
    distances = list()
    for path in picking_solution.paths:
        distance = sum(x['distance'] for x in path)
        distances.append(distance)
        print(distance)
    
    html = None
    if animate:
        html = animate_computed_multiple_paths(picking_solution.paths)
    
    return distances, picking_solution, html