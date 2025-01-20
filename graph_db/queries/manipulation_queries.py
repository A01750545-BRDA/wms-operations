STORAGE_LOCATION_RETRIEVER = '''
MATCH (from:Origin {id: 'start'})
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
WHERE contains.quantity = item.quantity
SET contains.quantity = contains.quantity - item.take
WITH item, contains
WHERE contains.quantity = 0
DELETE contains
'''