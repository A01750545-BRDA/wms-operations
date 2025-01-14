from graph_db.queries.creation_queries import (
    CREATE_STORAGE,
    CONNECT_STORAGE_VERTICALLY,
    CONNECT_STORAGE_HORIZONTALLY,
    CREATE_INTERSECTION,
    CONNECT_INTERSECTION,
    CONNECT_INTERSECTION_STORAGE,
    CREATE_ORIGIN,
    CONNECT_IN_ORIGIN,
    CONNECT_OUT_ORIGIN,
    CREATE_SKU,
    CREATE_PALLET,
    ADD_SKU_TO_PALLET,
    ADD_PALLET_TO_STORAGE
)
from graph_db.queries.utility_queries import GET_STORAGES
from data import WarehouseSpecs
from neo4j import Transaction
from config.settings import Config
import random

details = WarehouseSpecs.details
dimensions = WarehouseSpecs.dimensions
X = WarehouseSpecs.X
Y = WarehouseSpecs.Y
Z = WarehouseSpecs.Z

def create_warehouse(tx: Transaction) -> None:
    n_rack = 0

    for row in range(1, details['hall']['n_rows']):
        y_hall = row * dimensions['hall']['y'] + (row - 1) * dimensions['pallet']['y'] * 2

        for col in range(1, details['hall']['n_cols']):
            x_hall = col * dimensions['hall']['x'] + (col - 1) * dimensions['pallet']['x'] * details['rack']['indexes']

            # Back to back racks
            for rack_column in range(2):
                y = y_hall + (rack_column + 0.5) * dimensions['pallet']['y']
                n_rack += 1

                # Rack locations
                for index in range(1, details['rack']['indexes'] + 1):
                    x = x_hall + (index - 0.5) * dimensions['pallet']['x']

                    # Level within each rack
                    for level in range(1, details['rack']['levels'] + 1):
                        z = (level - 1) * dimensions['pallet']['z']

                        tx.run(
                            CREATE_STORAGE,
                            id=f'{row}.{col}-FACE_{rack_column}_I{index}_L{level}',
                            rack=n_rack,
                            index=index,
                            level=level,
                            isEdge=(index==1) or (index==details['rack']['indexes']),
                            x=x,
                            y=y,
                            z=z
                        )

    tx.run(CONNECT_STORAGE_VERTICALLY)
    tx.run(CONNECT_STORAGE_HORIZONTALLY)

    # Intersection row
    for row in range(1, details['hall']['n_rows'] + 1):
        y = (row - 0.5) * dimensions['hall']['y'] + (row - 1) * dimensions['pallet']['y'] * 2

        # Intersection col
        for col in range(1, details['hall']['n_cols'] + 1):
            x = (col - 0.5) * dimensions['hall']['x'] + (col - 1) * dimensions['pallet']['x'] * details['rack']['indexes']

            tx.run(
                CREATE_INTERSECTION,
                id=f'{row}.{col}',
                row=row,
                col=col,
                x=x,
                y=y
            )

    tx.run(CONNECT_INTERSECTION)
    tx.run(
        CONNECT_INTERSECTION_STORAGE,
        hDistanceFromIntersection=(dimensions['hall']['x'] + dimensions['pallet']['x'])/2,
        vDistanceFromIntersection=(dimensions['hall']['y'] + dimensions['pallet']['y'])/2
    )

    # Starting point
    tx.run(CREATE_ORIGIN, id=f'start', x=X//2, y=-10)
    tx.run(
        CONNECT_IN_ORIGIN,
        originIds=['start'],
        intersectionIds=[f"1.{details['hall']['n_cols']//2 + 1}"]
    )

    # Destinations
    tx.run(CREATE_ORIGIN, id=f'dest1', x=X//3, y=Y+10)
    tx.run(CREATE_ORIGIN, id=f'dest2', x=X//2, y=Y+10)
    tx.run(CREATE_ORIGIN, id=f'dest3', x=X//1.5, y=Y+10)
    tx.run(
        CONNECT_OUT_ORIGIN,
        originIds=['dest1', 'dest2', 'dest3'],
        intersectionIds=[f"{details['hall']['n_rows']}.{col}" for col in range(1, details['hall']['n_cols'] + 1)]
    )

unique_products = WarehouseSpecs.unique_products
unique_pallets = WarehouseSpecs.unique_positions

def create_skus(tx: Transaction) -> None:
    for i in range(1, unique_products + 1):
        tx.run(
            CREATE_SKU,
            id=f'Sku_{i}',
            volume=random.randint(1, 10),
        )

def create_pallets(tx: Transaction) -> None:
    for i in range(1, unique_pallets + 1):
        volume = 500
        tx.run(
            CREATE_PALLET,
            id=f'Pallet_{i}',
            volume=volume,
        )

def add_skus_to_pallets(tx: Transaction) -> None:
    for i in range(1, unique_pallets + 1):
        distinct_skus = random.randint(1, 5)

        for _ in range(distinct_skus):
            product_id = f'Sku_{random.randint(1, unique_products)}'
            quantity = random.randint(50, 300)

            tx.run(
                ADD_SKU_TO_PALLET,
                skuId=product_id,
                palletId=f'Pallet_{i}',
                quantity=quantity,
            )

def add_pallets_to_storage(tx: Transaction) -> None:
    result = tx.run(
        GET_STORAGES,
        n=unique_pallets
    )
    
    i = 1
    for record in result:
        tx.run(
            ADD_PALLET_TO_STORAGE,
            palletId=f'Pallet_{i}',
            storageId=record.get('id'),
        )
        i += 1

if __name__ == '__main__':
    with Config.db.driver.session() as session:
        session.execute_write(create_warehouse)
        session.execute_write(create_skus)
        session.execute_write(create_pallets)
        session.execute_write(add_skus_to_pallets)
        session.execute_write(add_pallets_to_storage)