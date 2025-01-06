import random
from neo4j import Record, Transaction
from graph_db.queries.utility_queries import GET_RAND_N_SKUS, SPECIFIC_SKU_OFFER
from graph_db.queries.manipulation_queries import STORAGE_LOCATION_RETRIEVER

def simulate_product_list(
        tx: Transaction, 
        n: int, 
        min_: int = 10, 
        max_: int = 100
    ) -> dict[str, int]:

    result = tx.run(
        GET_RAND_N_SKUS,
        n=n
    )

    return {
        record.get('id'): random.randint(min_, max_) 
        for record in result
    }

def get_storage_locations(
        tx: Transaction, 
        product_list: dict[str, int]
    ) -> list[Record]:
    
    result = tx.run(
        STORAGE_LOCATION_RETRIEVER,
        productList=[list(item) for item in product_list.items()]
    )

    return [record for record in result]

def assert_enough_offer(
        tx: Transaction, 
        product_list: dict[str, int]
    ) -> None:

    result = tx.run(SPECIFIC_SKU_OFFER, skuIds=list(product_list.keys()))
    insufficiencies = dict()

    for record in result:
        id = record.get('id')
        offer = record.get('contained')

        if offer < product_list.get(id):
            insufficiencies[id] = {'need': product_list.get(id), 'available': offer}
    
    assert not insufficiencies, f'Insufficient SKU offer: {insufficiencies}'

def assert_route(
        product_list: dict[str, int], 
        storage_locations: list[Record]
    ) -> None:

    built_product_list = dict()
    for location in storage_locations:
        sku_id = location['skuId']
        
        if sku_id in built_product_list:
            built_product_list[sku_id] += location['take']
        else:
            built_product_list[sku_id] = location['take']
    
    # Get differences
    differences = dict()
    for sku in product_list:
        if product_list[sku] != built_product_list[sku]:
            differences[sku] = {'need': product_list[sku], 'took': built_product_list[sku]}
    
    assert not differences, f'Unsatisfied demand {differences}'