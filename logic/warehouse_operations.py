import random
from neo4j import Record, Transaction
from graph_db.queries.utility_queries import GET_RAND_N_PRODUCTS, SPECIFIC_PRODUCT_OFFER
from graph_db.queries.manipulation_queries import STORAGE_LOCATION_RETRIEVER, MISMATCHES_ORDER_SUMMARY

def simulate_product_list(
        tx: Transaction, 
        n: int, 
        min_: int = 10, 
        max_: int = 100
    ) -> dict[str, int]:

    result = tx.run(
        GET_RAND_N_PRODUCTS,
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

    result = tx.run(SPECIFIC_PRODUCT_OFFER, productIds=list(product_list.keys()))
    insufficiencies = dict()

    for record in result:
        id = record.get('id')
        offer = record.get('contained')

        if offer < product_list.get(id):
            insufficiencies[id] = {'need': product_list.get(id), 'available': offer}
    
    assert not insufficiencies, f'Insufficient PRODUCT offer: {insufficiencies}'

def assert_route(
        product_list: dict[str, int], 
        storage_locations: list[Record]
    ) -> None:

    built_product_list = dict()
    for location in storage_locations:
        product_id = location['productId']
        
        if product_id in built_product_list:
            built_product_list[product_id] += location['take']
        else:
            built_product_list[product_id] = location['take']
    
    # Get differences
    differences = dict()
    for product in product_list:
        if product_list[product] != built_product_list[product]:
            differences[product] = {'need': product_list[product], 'took': built_product_list[product]}
    
    assert not differences, f'Unsatisfied demand {differences}'

def assert_order_summary(
        tx: Transaction,
        flat_summary: list[dict]
    ) -> None:
    
    mismatches = tx.run(
        MISMATCHES_ORDER_SUMMARY,
        summary=flat_summary
    ).single()['failedItems']

    assert not mismatches, f'{len(mismatches)} mismatches found. {[mismatch for mismatch in mismatches]}'