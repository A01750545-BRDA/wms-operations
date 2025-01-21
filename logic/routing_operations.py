import numpy as np
import random
from neo4j import Record, Transaction
from graph_db.queries.manipulation_queries import NODE_DISTANCES, NODE_DISTANCE_EXHAUSTIVE, FIND_PATH
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

def get_distance_matrix(
        tx: Transaction, 
        storage_locations: list[Record], 
        start_id: str = 'start',
        dest_id: str = 'dest1', 
        exhaustive: bool = False
    ) -> tuple[list[list[float]], dict[str, int]]:
    '''
    Compute distances between storage locations and create a lookup mapping.

    Args:
        tx: Database transaction object
        storage_locations: List of storage location records
        dest_id: Destination node identifier (default: 'dest1')
        exhaustive: Whether to use exhaustive distance calculation (default: False)

    Returns:
        Tuple containing:
        - 2D list representing the distance matrix
        - Dictionary mapping node IDs to their matrix indices
    '''
    storage_ids = list({loc['storageId'] for loc in storage_locations}) + list({start_id, dest_id})
    matrix_size = len(storage_ids)
    
    node_to_index = {id_: i for i, id_ in enumerate(storage_ids)}
    distance_matrix = [[0] * matrix_size for _ in range(matrix_size)]
    
    query = NODE_DISTANCES if not exhaustive else NODE_DISTANCE_EXHAUSTIVE
    results = tx.run(
        query,
        ids=storage_ids
    )

    for record in results:
        from_idx = node_to_index[record['from']]
        to_idx = node_to_index[record['to']]
        distance = record['distance']

        distance_matrix[from_idx][to_idx] = distance
        distance_matrix[to_idx][from_idx] = distance

    return distance_matrix, node_to_index


class Tour:
    def __init__(self, tour, optimal_value):
        self.tour = tour
        self.optimal_value = optimal_value


class TSPSolver:
    def __init__(
            self, 
            distance_matrix: list[list[float]], 
            start_index: int, 
            dest_index: int, 
            num_vehicles: int = 1
        ):
        
        self.data = self.create_data_model(
            distance_matrix, start_index, dest_index, num_vehicles
        )

    def create_data_model(
            self, 
            distance_matrix: list[list[float]],
            start_index: int, 
            dest_index: int, 
            num_vehicles: int
        ) -> dict:

        '''Stores the data for the problem.'''
        data = {}
        data['distance_matrix'] = np.array(distance_matrix).astype(int).tolist()
        data['num_vehicles'] = num_vehicles

        data['starts'] = [start_index] * data['num_vehicles']
        data['ends'] = [dest_index] * data['num_vehicles']

        data['visit_counter'] = len(data['distance_matrix']) * [1]
        data['visit_counter'][0] = 0
        return data

    @staticmethod
    def get_routes(manager, routing, solution) -> list[list[int]]:
        '''Get vehicle routes from a solution and store them in an array'''
        # Get vehicle routes and store them in a two dimensional array whose
        # i,j entry is the jth location visited by vehicle i along its route.
        routes = []
        for route_nbr in range(routing.vehicles()):
            index = routing.Start(route_nbr)
            route = [manager.IndexToNode(index)]
            while not routing.IsEnd(index):
                index = solution.Value(routing.NextVar(index))
                route.append(manager.IndexToNode(index))
            routes.append(route)
        return routes
    
    def __call__(self) -> list[Tour]:
        '''Entry point of the program.'''
        # Create the routing index manager.
        manager = pywrapcp.RoutingIndexManager(
            len(self.data['distance_matrix']), 
            self.data['num_vehicles'], 
            self.data['starts'],
            self.data['ends']
        )

        # Create Routing Model.
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            '''Returns the distance between the two nodes'''
            # Convert from routing variable Index to distance matrix NodeIndex.
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return self.data['distance_matrix'][from_node][to_node]

        def get_route_cost(route):
            return sum(
                [distance_callback(route[i], route[i + 1]) for i in range(len(route) - 1)]
            )
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)

        # Define cost of each arc.
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # theory_max = sum(max(row) for row in self.data['distance_matrix'])
        # theory_min = sum(min(x for x in row if x > 0) for row in self.data['distance_matrix'])

        # # Add distance dimension
        # dimension_name = 'Distance'
        # routing.AddDimension(
        #     transit_callback_index,
        #     0,  # no slack
        #     theory_max, # maximum distance per vehicle
        #     True,  # start cumul to zero
        #     dimension_name)
        # distance_dimension = routing.GetDimensionOrDie(dimension_name)
        
        # print(theory_min//self.data['num_vehicles'])
        # print(theory_max//self.data['num_vehicles'])

        # for vehicle_idx in range(self.data['num_vehicles']):
        #     routing.AddVariableMinimizedByFinalizer(
        #         distance_dimension.CumulVar(routing.End(vehicle_idx))
        #     )
        
        # Use Global Span Cost Coefficient to minimize the longest route
        # distance_dimension.SetGlobalSpanCostCoefficient(int(1000))


        dimension_name = 'Counter'
        routing.AddVectorDimension(
            self.data['visit_counter'],
            manager.GetNumberOfNodes(),
            True,  # start cumul to zero
            dimension_name
        )
        counter_dimension = routing.GetDimensionOrDie(dimension_name)
        num_visit = sum(self.data['visit_counter']) // manager.GetNumberOfVehicles()
        # print(f'num of visit per vehicle: {num_visit}')

        # Create and set the objective function
        for vehicle_idx in range(self.data['num_vehicles']):
            index = routing.End(vehicle_idx)
            #counter_dimension.SetCumulVarSoftLowerBound(index, num_visit//4, int(1e9))
            counter_dimension.SetCumulVarSoftUpperBound(index, num_visit + 1, int(1e9))
        
        # Set the cost of each route to be its length
        routing.SetPrimaryConstrainedDimension(dimension_name)
        

        # Setting first solution heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 5

        # Solve the problem.
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            routes = self.get_routes(manager, routing, solution)
            return [
                Tour(route, get_route_cost(route)) 
                for route in routes
            ]
        
        return [Tour([], 0)]
    

def get_picking_summary(
        tour: list, 
        storage_locations: list[Record]
    ) -> dict[str, dict[str, int]]:
    '''
    Generate a picking summary report ordered by tour sequence.
    
    Args:
        tour: List of storage location indices representing picking order
        storage_locations: List of storage location records with product details
        
    Returns:
        Nested dictionary mapping storage IDs to their PRODUCTs and picking details
    '''

    storage_ids = list({loc['storageId'] for loc in storage_locations})
    tour_nodes = set(tour)

    locations = [
        (loc, tour.index(i)) 
        for loc in storage_locations 
        if (i := storage_ids.index(loc['storageId'])) in tour_nodes
    ]
    sorted_locations = [loc for loc, _ in sorted(locations, key=lambda x: x[1], reverse=False)]

    summary = dict()

    for location in sorted_locations:
        storage_id = location['storageId']
        product_id = location['productId']
        
        if storage_id not in summary:
            summary[storage_id] = {}
            
        summary[storage_id][product_id] = {
            'quantity': location['quantity'],
            'take': location['take']
        }
    
    return summary


def find_path(
        tx: Transaction, 
        tour: list[int], 
        node_to_index: dict[str, int]
    ) -> list[dict]:
    '''
    Given a TSP tour (where every element is the index of a pallet to be visited) and
    the id to which each index refers to, this function returns a detailed path of
    the nodes that must be traveled to move from one pallet to another, from start to end.
    '''

    index_to_node = [x for x,_ in sorted(node_to_index.items(), key=lambda x: x[1])]
    sorted_nodes = [index_to_node[i] for i in tour]

    result = tx.run(
        FIND_PATH,
        sortedNodes=sorted_nodes
    )

    return [record.data() for record in result]


class ACO:
    def __init__(self, distance_matrix):
        self.distance_matrix = distance_matrix

    def get_distance(self, c1, c2) -> float:
        return self.distance_matrix[c1][c2]

    def get_cost(self, tour) -> float:
        ''' Calcular costo de un tour dado '''
        return sum(
            [
                self.get_distance(tour[i], tour[i + 1])
                for i in range(len(tour) - 1)
            ]
        ) + self.get_distance(tour[-1], tour[0])

    @staticmethod
    def to_triag(i, j):
        return (j * (j - 1))//2 + i
    
    def update_pheromones(self, pheromones: list[float],
                        rho: float, solutions: list[dict]):
        ''' Actualizar las feromonas con el factor de decadencia
        y recompensando las rutas con menor costo'''

        pheromones = list(map(lambda x: x * (1 - rho), pheromones))

        for solution in solutions:
            cities = solution['tour']
            for i in range(len(cities) - 1, -1, -1):
                k = self.to_triag(*sorted([cities[i], cities[i - 1]]))
                pheromones[k] += 1 / solution['cost']

        return pheromones


    def get_choices(self, curr_tour: list[int],
                    pheromones: list[float], a: float, b: float):
        ''' Obtener las opciones restantes para la ruta
        y su correspondiente heurística '''

        choices = list()
        remaining_cities_idx = set(range(len(self.distance_matrix[0]))) - set(curr_tour)

        for i in remaining_cities_idx:
            d = self.get_distance(self.distance_matrix, curr_tour[-1], i)

            k = self.to_triag(*sorted([curr_tour[-1], i]))
            history = pheromones[k] ** a

            heuristic = (1 / (d + 1e-6)) ** b

            prob = {
                'city': i,
                'prob': history * heuristic,
            }
            choices.append(prob)
        return choices


    @staticmethod
    def select_next(choices: list[dict]):
        ''' Seleccionar la siguiente ciudad en la ruta a partir
        de las opciones dadas y sus heurísticas con aleatoriedad '''
        p_sum = sum(map(lambda x: x['prob'], choices))

        if p_sum == 0:
            rand = np.random.randint(len(choices))
            return choices[rand]['city']

        return random.choices(
            choices,
            weights=list(map(lambda x: x['prob'], choices)),
            k=1)[0]['city']


    def generate_tour(self, pheromones: list[float], a: float, b: float):
        ''' Generar un tour aleatorio considerando las feromonas actuales '''

        tour = [0]

        for _ in range(len(self.distance_matrix[0]) - 1):
            choices = self.get_choices(tour, pheromones, a, b)
            tour.append(self.select_next(choices))

        return tour

    def solve(self, a: float, b: float, rho: float, max_iter: int,
            n_ants: int, debug: bool = True) -> dict:
        ''' Implementación del algoritmo Ant Colony Optimization '''

        n = len(self.distance_matrix[0])
        # Inicializar una ruta aleatoria
        tour = np.random.permutation(n)

        best = {
            'cost': self.get_cost(tour),
            'tour': tour,
        }

        pheromones = [1.0 for _ in range(n*(n-1)//2)] # Inicializar feromonas

        for i in range(max_iter):
            solutions = []
            for j in range(n_ants):
                # Generar una nueva ruta basada en las feromonas
                tour = self.generate_tour(pheromones, a, b)
                candidate = {
                    'cost': self.get_cost(tour),
                    'tour': tour,
                }

                solutions.append(candidate)

                # Actualizar mejor solución
                if candidate['cost'] < best['cost']:
                    best = candidate
                    if debug: print(f'New best found - {best}')

            # Actualizar feromonas
            pheromones = self.update_pheromones(pheromones, rho, solutions)

        return best
    
    def __call__(self, debug=True):
        solution = self.solve(1, 8, 0.5, 50, 50, debug)
        return Tour(
            solution['tour'] + [0], 
            solution['cost']
        )