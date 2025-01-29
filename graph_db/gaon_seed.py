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
    CREATE_PRODUCT,
    CREATE_PALLET,
    ADD_PRODUCT_TO_PALLET,
    ADD_PALLET_TO_STORAGE
)
from graph_db.queries.utility_queries import GET_STORAGES
from data import WarehouseSpecs
from neo4j import Transaction
from config.settings import Config
import random

def number_to_letters(n):
    result = []
    
    while n > 0:
        n -= 1
        remainder = n % 26
        result.append(chr(remainder + 65))
        n //= 26
    
    return ''.join(result[::-1])

def create_standard_row_layout(n_halls: int):
    return [
        x for _ in range(n_halls - 1)
        for x in [
            {"type": "hall"},
            [
                {"type": "rack"},
                {"type": "rack"} 
            ]
        ]
    ] + [{"type": "hall"}]

details = {
    'rack': {
        'indexes': 18,
        'levels': 4,
    },
    'row_configs': [
        {
            "row_id": 2,
            "row_layout": create_standard_row_layout(n_halls=14),
            "id_suffix": ""   
        },
        {
            "row_id": 1,
            "row_layout": create_standard_row_layout(n_halls=10),
            "id_suffix": "2"
        },
    ]
}

details['row_configs'][0]['row_layout'][1].pop()
details['row_configs'][0]['row_layout'].pop(0)
details['row_configs'][1]['row_layout'][1].pop()
details['row_configs'][1]['row_layout'].pop(0)

dimensions = {
    'hall': {
        'x': 4,
        'y': 4,
    },
    'pallet': {
        'x': 1.2,
        'y': 1,
        'z': 2,
    }
}

def create_gaon_warehouse(tx: Transaction) -> None:
    n_cols = 0
    total_halls = 0
    hall_x_row_coords = []

    for row_config in details['row_configs']:
        n_hall = 0
        n_rack = 0
        hall_x_coords = []

        y_hall = (
            row_config['row_id'] * dimensions['hall']['y'] + # The amount of halls
            (row_config['row_id'] - 1) * dimensions['pallet']['y'] * details['rack']['indexes'] # The amount of pallets
        )

        for element in row_config['row_layout']:
            if isinstance(element, list):
                adjacent_rack_cols = [[n_hall, n_hall + 1]] if len(element) == 1 else [[n_hall], [n_hall + 1]]
                
                for adjacent_cols in adjacent_rack_cols:
                    n_rack += 1
                    rack_id = number_to_letters(n_rack)

                    x = (
                        n_hall * dimensions['hall']['x'] + # The amount of halls
                        (n_rack - 0.5) * dimensions['pallet']['x'] # The amount of pallets
                    )
                    
                    for index in range(1, details['rack']['indexes'] + 1):
                        y = y_hall + (index - 0.5) * dimensions['pallet']['y']

                        for level in range(1, details['rack']['levels'] + 1):
                            z = (level - 1) * dimensions['pallet']['z']

                            tx.run(
                                CREATE_STORAGE,
                                id=f'{rack_id}{row_config['id_suffix']}-{level}-{index}',
                                rack=rack_id + row_config['id_suffix'],
                                index=index,
                                level=level,
                                row=row_config['row_id'],
                                adjacentCols=adjacent_cols,
                                x=x,
                                y=y,
                                z=z
                            )
            else:
                n_hall += 1
                total_halls += 1
                hall_id = number_to_letters(total_halls)
                n_cols = max(n_cols, n_hall)

                x = (
                    (n_hall - 0.5) * dimensions['hall']['x'] + # The amount of halls
                    n_rack * dimensions['pallet']['x'] # The amount of pallets
                )
                hall_x_coords.append(x)

                for index in range(1, details['rack']['indexes'] + 1):
                    y = y_hall + (index - 0.5) * dimensions['pallet']['y']

                    adjacent_row = row_config['row_id'] if index == 1 else (row_config['row_id'] + 1 if index == details['rack']['indexes'] else None)

                    tx.run(
                        CREATE_HALL,
                        id=hall_id,
                        col=n_hall,
                        row=row_config['row_id'],
                        index=index,
                        adjacentRow=adjacent_row,
                        x=x,
                        y=y
                    )
        
        hall_x_row_coords.append(hall_x_coords)

    # Intersection row
    hall_x_coords = max(hall_x_row_coords, key=lambda x: len(x))
    n_rows = len(hall_x_row_coords) + 1
    
    for row in range(1, n_rows + 1):
        y = (row - 0.5) * dimensions['hall']['y'] + (row - 1) * dimensions['pallet']['y'] * details['rack']['indexes']

        # Intersection col
        for col in range(1, n_cols + 1):
            # IMPORTANT!!!! Wall separates first and second row, and is connected till last column
            if row == 2 and col != n_cols:
                continue

            x = hall_x_coords[col - 1]

            tx.run(
                CREATE_INTERSECTION,
                id=f'C{col}.R{row}',
                row=row,
                col=col,
                x=x,
                y=y
            )
    
    tx.run(CONNECT_STORAGE_VERTICALLY)
    tx.run(CONNECT_INTERSECTION)
    tx.run(CONNECT_INTERSECTION_HALL)
    tx.run(CONNECT_HALL)
    tx.run(CONNECT_HALL_STORAGE)

    # Starting point
    tx.run(CREATE_ORIGIN, id=f'start', x=hall_x_coords[-4], y=-2)
    tx.run(CONNECT_IN_ORIGIN, originIds=['start'], intersectionIds=[f"C{n_cols - 3}.R1"])
    
    tx.run(CREATE_ORIGIN, id=f'dest1', x=hall_x_coords[-3], y=-2)
    tx.run(CONNECT_OUT_ORIGIN, originIds=['dest1'], intersectionIds=[f"C{n_cols - 2}.R1"])

    # Patio
    floor_level = 5
    x_floor = (hall_x_coords[-3] + hall_x_coords[-2]) / 2
    y_floor = (1.5 * dimensions['hall']['y'] + dimensions['pallet']['y'] * details['rack']['indexes']) / 2
    z_floor = (floor_level - 1) * dimensions['pallet']['z']
    tx.run(
        CREATE_STORAGE,
        id='Patio',
        rack='Patio',
        index=None,
        row=None,
        adjacentCols=None,
        level=floor_level,
        x=x_floor,
        y=y_floor,
        z=z_floor
    )
    connect_floor_to_intersection = """
    MATCH (s: Storage {id: 'Patio'})
    MATCH (i: Intersection)
    WHERE i.id IN $intersectionIds
    WITH s, i, abs(s.x - i.x) as x, abs(s.y - i.y) as y, abs(s.z - i.z) as z
    CREATE (i)-[:CONNECTED_TO {
        distance: (x^2 + y^2)^0.5 + z,
        x: x,
        y: y,
        z: z
    }]->(s)
    """
    tx.run(
        connect_floor_to_intersection, 
        intersectionIds=[f"C{col}.R1" for col in range(n_cols - 3, n_cols + 1)] + [f"C{n_cols}.R2"]
    )

unique_products = WarehouseSpecs.unique_products
unique_pallets = sum(
    len(element) * details['rack']['indexes'] * details['rack']['levels']
    for row_config in details['row_configs'] 
    for element in row_config['row_layout'] 
    if isinstance(element, list)
) + 1

def create_gaon_products(tx: Transaction) -> None:
    for i in range(1, unique_products + 1):
        tx.run(
            CREATE_PRODUCT,
            id=f'Product_{i}',
            volume=random.randint(1, 10),
        )

def create_gaon_pallets(tx: Transaction) -> None:
    for i in range(1, unique_pallets + 1):
        volume = 500
        tx.run(
            CREATE_PALLET,
            id=f'Pallet_{i}',
            volume=volume,
        )

def add_gaon_products_to_pallets(tx: Transaction) -> None:
    for i in range(1, unique_pallets + 1):
        distinct_products = random.randint(1, 5)
        product_index_options = random.sample(range(1, unique_products + 1), distinct_products)
        
        for index in product_index_options:
            product_id = f'Product_{index}'
            quantity = random.randint(50, 300)

            tx.run(
                ADD_PRODUCT_TO_PALLET,
                productId=product_id,
                palletId=f'Pallet_{i}',
                quantity=quantity,
            )

def add_gaon_pallets_to_storage(tx: Transaction) -> None:
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