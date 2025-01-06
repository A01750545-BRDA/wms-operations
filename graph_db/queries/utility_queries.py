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

GET_RAND_N_SKUS = '''
MATCH (sku: Sku)
RETURN sku.id as id
ORDER BY RAND()
LIMIT $n
'''

GENERAL_SKU_OFFER = '''
MATCH (sku: Sku)<-[contains: CONTAINS]-()
RETURN sku.id as id, sum(contains.quantity) as contained
ORDER BY contained DESC
'''

SPECIFIC_SKU_OFFER = '''
MATCH (sku: Sku)<-[contains: CONTAINS]-()
WHERE sku.id IN $skuIds
RETURN sku.id as id, sum(contains.quantity) as contained
ORDER BY contained DESC
'''