from dataclasses import dataclass
from typing import Optional
from time import time
from neo4j import Transaction
from logic.warehouse_operations import get_storage_locations, assert_enough_offer, assert_route, assert_order_summary
from logic.routing_operations import get_distance_matrix, get_picking_summary, TSPSolver, find_path
from graph_db.queries.manipulation_queries import PROCESS_ORDER_SUMMARY, RESTORE_ORDER_SUMMARY
from config.settings import Config
import warnings

@dataclass
class PickingSolution:
    summaries: list[dict[str, dict[str, dict[str, int]]]]
    paths: list[list[dict]]
    performance_metrics: Optional[dict[str, float]]

class TimedOperation:
    def __init__(self, name: str, debug: bool):
        self.name = name
        self.start_time = None
        self.duration = None
        self.debug = debug

    def __enter__(self):
        self.start_time = time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time() - self.start_time
        
        if self.debug:
            print(f'{self.duration:.4f} s. \t {self.name}')

class PickingService:
    def __init__(self, is_testing: bool):
        self.is_testing = is_testing

    @staticmethod
    def _solve_test(
            tx: Transaction,
            product_list: dict[str, int],
            start_id: str,
            dest_id: str,
            num_routes: int,
            debug: bool
        ) -> PickingSolution:
        '''
        Solve the optimal picking order for a given product list.
        
        Args:
            tx: Database transaction object
            product_list: Dictionary mapping product IDs to quantities
            start_id: Node of starting id
            dest_id: Node of destination id
            num_routes: Number of distinct picking routes
            debug: Bool that determines if times are printed
            
        Returns:
            PickingSolution containing picking summaries, paths, and performance metrics
        
        Raises:
            AssertionError: If product availability or route requirements are not met
        '''
        metrics = {}
        
        # Validate and get storage locations
        with TimedOperation('location_search', debug) as op:
            assert_enough_offer(tx, product_list)
            storage_locations = get_storage_locations(tx, product_list)
            assert_route(product_list, storage_locations)

        metrics['location_search'] = op.duration
        
        # Compute distance matrix
        with TimedOperation('distance_matrix', debug) as op:
            distance_matrix, node_to_index = get_distance_matrix(
                tx, storage_locations, start_id, dest_id
            )

        metrics['distance_matrix'] = op.duration
        
        #Solve TSP
        with TimedOperation('tour_optimization', debug) as op:
            start_index = node_to_index[start_id]
            dest_index = node_to_index[dest_id]

            solutions = TSPSolver(
                distance_matrix, 
                start_index=start_index,
                dest_index=dest_index,
                num_vehicles=num_routes
            )()

        metrics['tour_optimization'] = op.duration
        
        paths, summaries = list(), list()
        metrics['path_finding'] = 0
        metrics['summary_generation'] = 0

        for solution in solutions:
            # Find path
            with TimedOperation('path_finding', debug) as op:
                path = find_path(tx, solution.tour, node_to_index)
            metrics['path_finding'] += op.duration
            
            # Generate picking summary
            with TimedOperation('summary_generation', debug) as op:
                summary = get_picking_summary(solution.tour, storage_locations)
            metrics['summary_generation'] += op.duration

            paths.append(path)
            summaries.append(summary)
        
        return PickingSolution(
            summaries=summaries,
            paths=paths,
            performance_metrics=metrics
        )

    @staticmethod
    def _solve(
            tx: Transaction,
            product_list: dict[str, int],
            start_id: str,
            dest_id: str,
            num_routes: int
        ) -> PickingSolution:
        '''
        Solve the optimal picking order for a given product list.
        
        Args:
            tx: Database transaction object
            product_list: Dictionary mapping product IDs to quantities
            start_id: Node of starting id
            dest_id: Node of destination id
            num_routes: Number of distinct picking routes
            
        Returns:
            PickingSolution containing picking summaries and paths
        
        Raises:
            AssertionError: If product availability or route requirements are not met
        '''
        
        # Validate and get storage locations
        assert_enough_offer(tx, product_list)
        storage_locations = get_storage_locations(tx, product_list)
        assert_route(product_list, storage_locations)

        
        # Compute distance matrix
        distance_matrix, node_to_index = get_distance_matrix(
            tx, storage_locations, start_id, dest_id
        )
        
        #Solve TSP
        start_index = node_to_index[start_id]
        dest_index = node_to_index[dest_id]

        solutions = TSPSolver(
            distance_matrix, 
            start_index=start_index,
            dest_index=dest_index,
            num_vehicles=num_routes
        )()

        paths, summaries = list(), list()

        for solution in solutions:
            # Find path
            path = find_path(tx, solution.tour, node_to_index)
            paths.append(path)
            
            # Generate picking summary
            summary = get_picking_summary(solution.tour, storage_locations)
            summaries.append(summary)
        
        return PickingSolution(
            summaries=summaries,
            paths=paths,
            performance_metrics=None
        )
    
    def optimize(
            self, 
            product_list: dict[str, int], 
            start_id: str = 'start',
            dest_id: str = 'dest1',
            num_routes: int = 1,
            debug: Optional[bool] = None
        ) -> PickingSolution:

        if self.is_testing:
            debug = True if debug is None else debug

            with Config.db.driver.session() as session:
                picking_solution = session.execute_read(
                    self._solve_test,
                    product_list,
                    start_id,
                    dest_id,
                    num_routes,
                    debug
                )
        else:
            if debug is not None:
                warnings.warn('Picking service is not on testing mode, therefore debug arg is ignored')

            with Config.db.driver.session() as session:
                picking_solution = session.execute_read(
                    self._solve,
                    product_list,
                    start_id,
                    dest_id,
                    num_routes
                )
        
        return picking_solution
    
    @staticmethod
    def _process_order_summary(
        tx: Transaction,
        summary: dict[str, dict[str, dict[str, int]]]
        ) -> None:

        flat_summary = [
            {'storageId': storage_id, 'productId': product_id, 'quantity': data['quantity'], 'take': data['take']} 
            for storage_id, products in summary.items()
            for product_id, data in products.items()
        ]

        assert_order_summary(tx, flat_summary)
        tx.run(PROCESS_ORDER_SUMMARY, summary=flat_summary)

    def process_order_summary(
            self, 
            summary: dict[str, dict[str, dict[str, int]]]
        ) -> None:

        with Config.db.driver.session() as session:
            session.execute_write(
                self._process_order_summary,
                summary
            )
    
    @staticmethod
    def _restore_order_summary(
        tx: Transaction,
        summary: dict[str, dict[str, dict[str, int]]]
        ) -> None:

        flat_summary = [
            {'storageId': storage_id, 'productId': product_id, 'quantity': data['quantity'], 'take': data['take']} 
            for storage_id, products in summary.items()
            for product_id, data in products.items()
        ]

        tx.run(RESTORE_ORDER_SUMMARY, summary=flat_summary)

    def restore_order_summary(
            self, 
            summary: dict[str, dict[str, dict[str, int]]]
        ) -> None:

        with Config.db.driver.session() as session:
            session.execute_write(
                self._restore_order_summary,
                summary
            )
    