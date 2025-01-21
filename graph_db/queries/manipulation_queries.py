STORAGE_LOCATION_RETRIEVER = '''
MATCH (from)
WHERE from.id = $startId
UNWIND $productList as productItem
WITH from, productItem[0] as productId, productItem[1] as desiredQuantity

MATCH (product:Product {id: productId})<-[contains:CONTAINS]-(pallet:Pallet)<-[:STORES]-(storage:Storage)
WITH from, productId, storage, contains.quantity as quantity, desiredQuantity,
    abs(from.x - storage.x) + abs(from.y - storage.y) + abs(from.z - storage.z)*100 as distance
ORDER BY productId, distance, quantity DESC

WITH productId, from, desiredQuantity, collect({
    storageId: storage.id,
    quantity: quantity,
    distance: distance
}) as storagesList

UNWIND range(0, size(storagesList)-1) as index
WITH productId, from, desiredQuantity, storagesList,
    index,
    reduce(s = 0, i IN range(0, index-1) |
        s + CASE
            WHEN i >= 0 THEN storagesList[i].quantity
            ELSE 0
        END
    ) as previousSum
WHERE previousSum < desiredQuantity

WITH productId, from, desiredQuantity, storagesList[index] as storage,
    previousSum,
    CASE
        WHEN desiredQuantity - previousSum > storagesList[index].quantity
        THEN storagesList[index].quantity
        ELSE desiredQuantity - previousSum
    END as take
WHERE take > 0

RETURN
    productId,
    storage.quantity as quantity,
    storage.storageId as storageId,
    take
ORDER BY productId, storage.distance
'''

NODE_DISTANCES = '''
// Query for storage-to-storage distances
MATCH (from), (to)
WHERE from.id IN $ids AND to.id IN $ids AND from.id <> to.id AND from.id > to.id
MATCH path = shortestPath((from)-[:CONNECTED_TO*]-(to))
RETURN from.id as from, to.id as to,
    reduce(distance = 0, r IN relationships(path) | distance + r.distance) as distance
'''

NODE_DISTANCE_EXHAUSTIVE = '''
// Query for storage-to-storage distances
MATCH (from), (to)
WHERE from.id IN $ids AND to.id IN $ids AND from.id <> to.id AND from.id > to.id
CALL apoc.algo.dijkstra(from, to, 'CONNECTED_TO', 'distance')
YIELD path, weight
RETURN from.id as from, to.id as to, weight as distance
'''

FIND_PATH = '''
WITH $sortedNodes as sortedNodes
UNWIND range(0, size(sortedNodes)-1) as i
MATCH (from), (to)
WHERE from.id = sortedNodes[i] AND to.id = sortedNodes[i+1]
CALL apoc.algo.dijkstra(from, to, 'CONNECTED_TO', 'distance')
YIELD path, weight
RETURN
    from.id as from,
    to.id as to,
    weight as distance,
    [n in nodes(path) WHERE n.z = 0] as path
'''

RESTORE_ORDER_SUMMARY = '''
WITH $summary AS data
UNWIND data AS item
MATCH (product: Product {id: item.productId}), (p)-[:STORES]-(storage: Storage {id: item.storageId})
MERGE (p)-[contains: CONTAINS]->(product)
ON CREATE SET contains.quantity = item.quantity
ON MATCH SET contains.quantity = item.quantity
'''

MISMATCHES_ORDER_SUMMARY = '''
WITH $summary AS data
UNWIND data AS item
MATCH (product: Product {id: item.productId})-[contains: CONTAINS]-()-[:STORES]-(storage: Storage {id: item.storageId})
WHERE contains.quantity <> item.quantity
RETURN collect({
    storageId: item.storageId,
    productId: item.productId,
    expectedQuantity: item.quantity,
    actualQuantity: contains.quantity
}) AS failedItems
'''

PROCESS_ORDER_SUMMARY = '''
WITH $summary AS data
UNWIND data AS item
MATCH (product: Product {id: item.productId})-[contains: CONTAINS]-()-[:STORES]-(storage: Storage {id: item.storageId})
CALL apoc.util.validate(contains.quantity <> item.quantity, "Expected " + item.quantity + " of '" + product.id + "' in " + storage.id + ", but found " + contains.quantity, [product])

WITH contains.quantity - item.take as new_quantity, contains
CALL apoc.do.when(
    new_quantity > 0,
    "SET c1.quantity = new_quantity",
    "DELETE c1",
    {new_quantity: new_quantity, contains: contains}
) YIELD value
RETURN value
'''

ADD_PRODUCT_TO_LOCATION = """
MATCH (s: Storage {id: $location})-[:STORES]-(p: Pallet)
MATCH (product: Product {id: $productId})
MERGE (p)-[c:CONTAINS]->(product)
ON MATCH SET c.quantity = c.quantity + $quantity
ON CREATE SET c.quantity = $quantity
"""

MOVE_PRODUCT_TO_LOCATION = """
MATCH (product: Product {id: $gwin})
OPTIONAL MATCH (:Storage {id: $fromLocation})-[:STORES]-()-[c1: CONTAINS]-(product)
CALL apoc.util.validate(c1 IS NULL, $fromLocation + " does not have product: " + $gwin, [product])

WITH c1.quantity - $quantity as new_quantity, c1, product
CALL apoc.util.validate(new_quantity < 0, $fromLocation + " has " + c1.quantity + " products of: " + $gwin + ", not enough to move " + $quantity, [new_quantity])

MATCH (:Storage {id: $toLocation})-[:STORES]-(p: Pallet)
MERGE (p)-[c: CONTAINS]->(product)
ON CREATE SET c.quantity = $quantity
ON MATCH SET c.quantity = c.quantity + $quantity

WITH new_quantity, c1
CALL apoc.do.when(
    new_quantity > 0,
    "SET c1.quantity = new_quantity",
    "DELETE c1",
    {new_quantity: new_quantity, c1: c1}
) YIELD value
RETURN value
"""

GET_ALL_STORAGES = """
MATCH (s: Storage)
RETURN collect(s.id) as storage_id
"""

GET_ALL_RACKS = """
MATCH (s: Storage)
OPTIONAL MATCH (s)-[:STORES]->(p:Pallet)
WITH s.rack as rack, 
     COUNT(DISTINCT s.id) as total,
     COUNT(DISTINCT p) as occupied
RETURN collect({
    rack: rack,
    total: total,
    occupied: occupied
}) as data
"""

GET_RACK_LEVELS = """
MATCH (s: Storage)
WHERE s.rack = $rack
OPTIONAL MATCH (s)-[:STORES]->(p:Pallet)
WITH s.level as level, 
     COUNT(DISTINCT s) as total,
     COUNT(CASE WHEN p IS NOT NULL THEN 1 ELSE NULL END) as occupied
RETURN collect({
    level: level,
    total: total,
    occupied: occupied
}) as data
"""

GET_RACK_LEVEL_STORAGES = """
MATCH (s: Storage)
WHERE s.rack = $rack AND s.level = $level
RETURN collect(s.id) as storage_id
"""

GET_STORAGE_PRODUCTS = """
MATCH (s:Storage)-[:STORES]->(p:Pallet)-[c:CONTAINS]->(product:Product)
WHERE s.id = $storageId
RETURN collect({
    gwin: product.id,
    quantity: c.quantity
}) as data
"""