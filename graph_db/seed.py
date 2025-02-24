from graph_db.queries.creation_queries import (
    CREATE_STORAGE,
    CONNECT_STORAGE_VERTICALLY,
    CREATE_INTERSECTION,
    CONNECT_INTERSECTION,
    CREATE_HALL,
    CONNECT_HALL,
    CONNECT_HALL_STORAGE,
    CONNECT_INTERSECTION_HALL,
    CREATE_ORIGIN,
    CONNECT_IN_ORIGIN,
    CONNECT_OUT_ORIGIN,
    CREATE_PRODUCT
)
from graph_db.queries.utility_queries import GET_STORAGES
from graph_db.queries.manipulation_queries import ADD_PRODUCT_TO_LOCATION
from data import WarehouseSpecs
from neo4j import Transaction
from config.settings import Config
import random

details = WarehouseSpecs.details
dimensions = WarehouseSpecs.dimensions
X = WarehouseSpecs.X
Y = WarehouseSpecs.Y
Z = WarehouseSpecs.Z

def number_to_letters(n):
    result = []
    
    while n > 0:
        n -= 1
        remainder = n % 26
        result.append(chr(remainder + 65))
        n //= 26
    
    return ''.join(result[::-1])

def create_warehouse(tx: Transaction) -> None:
    n_rack = 0

    for row in range(1, details['hall']['n_rows']):
        y_hall = row * dimensions['hall']['y'] + (row - 1) * dimensions['pallet']['y'] * details['rack']['indexes']

        for col in range(1, details['hall']['n_cols']):
            x_hall = col * dimensions['hall']['x'] + (col - 1) * dimensions['pallet']['x'] * 2

            # Back to back racks
            for rack_column in range(2):
                x = x_hall + (rack_column + 0.5) * dimensions['pallet']['x']
                
                n_rack += 1
                rack_id = number_to_letters(n_rack)

                # Rack locations
                for index in range(1, details['rack']['indexes'] + 1):
                    y = y_hall + (index - 0.5) * dimensions['pallet']['y']

                    # Level within each rack
                    for level in range(1, details['rack']['levels'] + 1):
                        z = (level - 1) * dimensions['pallet']['z']

                        tx.run(
                            CREATE_STORAGE,
                            id=f'{rack_id}.{level}.{index}',
                            rack=rack_id,
                            index=index,
                            level=level,
                            row=row,
                            adjacentCols=[col + rack_column],
                            x=x,
                            y=y,
                            z=z
                        )

    tx.run(CONNECT_STORAGE_VERTICALLY)

    # Intersection row
    for row in range(1, details['hall']['n_rows'] + 1):
        y = (row - 0.5) * dimensions['hall']['y'] + (row - 1) * dimensions['pallet']['y'] * details['rack']['indexes']

        # Intersection col
        for col in range(1, details['hall']['n_cols'] + 1):
            x = (col - 0.5) * dimensions['hall']['x'] + (col - 1) * dimensions['pallet']['x'] * 2

            tx.run(
                CREATE_INTERSECTION,
                id=f'C{col}.R{row}',
                row=row,
                col=col,
                x=x,
                y=y
            )

    # Intersection row
    for row in range(1, details['hall']['n_rows']):
        y_hall = row * dimensions['hall']['y'] + (row - 1) * dimensions['pallet']['y'] * details['rack']['indexes']

        # Intersection col
        for col in range(1, details['hall']['n_cols'] + 1):
            x = (col - 0.5) * dimensions['hall']['x'] + (col - 1) * dimensions['pallet']['x'] * 2

            for index in range(1, details['rack']['indexes'] + 1):
                y = y_hall + (index - 0.5) * dimensions['pallet']['y']
                adjacent_row = row if index == 1 else (row + 1 if index == details['rack']['indexes'] else None)

                tx.run(
                    CREATE_HALL,
                    id=f'C{col}.R{row}.{index}',
                    col=col,
                    row=row,
                    index=index,
                    adjacentRow=adjacent_row,
                    x=x,
                    y=y
                )

    tx.run(CONNECT_INTERSECTION)
    tx.run(CONNECT_INTERSECTION_HALL)
    tx.run(CONNECT_HALL)
    tx.run(CONNECT_HALL_STORAGE)

    # Starting point
    tx.run(CREATE_ORIGIN, id=f'start', x=X//2, y=-10)
    tx.run(
        CONNECT_IN_ORIGIN,
        originIds=['start'],
        intersectionIds=[f"C{col}.R1" for col in range(1, details['hall']['n_cols'] + 1)]
    )

    # Destinations
    tx.run(CREATE_ORIGIN, id=f'dest1', x=X//3, y=Y+10)
    tx.run(CREATE_ORIGIN, id=f'dest2', x=X//2, y=Y+10)
    tx.run(CREATE_ORIGIN, id=f'dest3', x=X//1.5, y=Y+10)
    tx.run(
        CONNECT_OUT_ORIGIN,
        originIds=['dest1', 'dest2', 'dest3'],
        intersectionIds=[f"C{col}.R{details['hall']['n_rows']}" for col in range(1, details['hall']['n_cols'] + 1)]
    )

unique_products = WarehouseSpecs.unique_products
unique_locations = WarehouseSpecs.unique_positions

def create_products(tx: Transaction) -> None:
    for i in range(1, unique_products + 1):
        tx.run(
            CREATE_PRODUCT,
            id=f'Product_{i}',
            volume=random.randint(1, 10),
        )

def add_products_to_locations(tx: Transaction) -> None:
    locations = tx.run(
        GET_STORAGES,
        n=unique_locations
    )
    for location in locations:
        distinct_products = random.randint(1, 5)
        product_index_options = random.sample(range(1, unique_products + 1), distinct_products)

        for index in product_index_options:
            product_id = f'Product_{index}'
            quantity = random.randint(50, 300)

            tx.run(
                ADD_PRODUCT_TO_LOCATION,
                productId=product_id,
                locationId=location.get('id'),
                quantity=quantity,
            )

if __name__ == '__main__':
    with Config.db.driver.session() as session:
        session.execute_write(create_warehouse)
        session.execute_write(create_products)
        session.execute_write(add_products_to_locations)