COUNT_ALL_NODES = '''
MATCH (n)
RETURN count(n) as count
'''

DELETE_ALL_NODES = '''
MATCH (n)
DETACH DELETE n
'''

GET_COORDS = '''
MATCH (n)-[:CONNECTED_TO]-()
RETURN DISTINCT n.x as x, n.y as y, n.z as z
'''

GET_STORAGES = '''
MATCH (s: Storage)
RETURN s.id as id
LIMIT $n
'''

GET_RAND_N_PRODUCTS = '''
MATCH (product: Product)
RETURN product.id as id
ORDER BY RAND()
LIMIT $n
'''

GENERAL_PRODUCT_OFFER = '''
MATCH (product: Product)<-[contains: CONTAINS]-()
RETURN product.id as id, sum(contains.quantity) as contained
ORDER BY contained DESC
'''

SPECIFIC_PRODUCT_OFFER = '''
UNWIND $productIds AS productId
OPTIONAL MATCH (product: Product {id: productId})
CALL apoc.util.validate(product IS NULL, "Warehouse has no registered product: " + productId, [productId])
OPTIONAL MATCH (product)<-[contains: CONTAINS]-()
RETURN product.id as id, sum(coalesce(contains.quantity, 0)) as contained
ORDER BY contained DESC
'''