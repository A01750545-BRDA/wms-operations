STORAGE_LOCATION_RETRIEVER = '''
MATCH (from:Origin {id: 'start'})
UNWIND $productList as product
WITH from, product[0] as skuId, product[1] as desiredQuantity

MATCH (sku:Sku {id: skuId})<-[contains:CONTAINS]-(palett:Palett)<-[:STORES]-(storage:Storage)
WITH from, skuId, storage, contains.quantity as quantity, desiredQuantity,
    abs(from.x - storage.x) + abs(from.y - storage.y) + abs(from.z - storage.z)*100 as distance
ORDER BY skuId, distance, quantity DESC

WITH skuId, from, desiredQuantity, collect({
    storageId: storage.id,

    quantity: quantity,
    distance: distance
}) as storagesList

UNWIND range(0, size(storagesList)-1) as index
WITH skuId, from, desiredQuantity, storagesList,
    index,
    reduce(s = 0, i IN range(0, index-1) |
        s + CASE
            WHEN i >= 0 THEN storagesList[i].quantity
            ELSE 0
        END
    ) as previousSum
WHERE previousSum < desiredQuantity

WITH skuId, from, desiredQuantity, storagesList[index] as storage,
    previousSum,
    CASE
        WHEN desiredQuantity - previousSum > storagesList[index].quantity
        THEN storagesList[index].quantity
        ELSE desiredQuantity - previousSum
    END as take
WHERE take > 0

RETURN
    skuId,
    storage.quantity as quantity,
    storage.storageId as storageId,
    take
ORDER BY skuId, storage.distance
'''

# NODE_DISTANCES = '''
# // Query for start-to-storage distances
# MATCH (from: Origin {id: 'start'}), (to: Storage)
# WHERE to.id IN $ids
# MATCH path = shortestPath((from)-[:CONNECTED_TO*]-(to))
# RETURN from.id as from, to.id as to,
#     reduce(distance = 0, r IN relationships(path) | distance + r.distance) as distance

# UNION ALL

# // Query for storage-to-storage distances
# MATCH (from: Storage), (to: Storage)
# WHERE from.id IN $ids AND to.id IN $ids AND from.id <> to.id AND from.id > to.id
# MATCH path = shortestPath((from)-[:CONNECTED_TO*]-(to))
# RETURN from.id as from, to.id as to,
#     reduce(distance = 0, r IN relationships(path) | distance + r.distance) as distance

# UNION ALL

# // Query for storage-to-end distances
# MATCH (from: Storage), (to: Origin {id: $destId})
# WHERE from.id IN $ids
# MATCH path = shortestPath((from)-[:CONNECTED_TO*]-(to))
# RETURN from.id as from, to.id as to,
#     reduce(distance = 0, r IN relationships(path) | distance + r.distance) as distance
# '''
NODE_DISTANCES = '''
// Query for storage-to-storage distances
MATCH (from), (to)
WHERE from.id IN $ids AND to.id IN $ids AND from.id <> to.id AND from.id > to.id
MATCH path = shortestPath((from)-[:CONNECTED_TO*]-(to))
RETURN from.id as from, to.id as to,
    reduce(distance = 0, r IN relationships(path) | distance + r.distance) as distance
'''
# NODE_DISTANCES = '''
# // Query for storage-to-storage distances
# MATCH (from), (to)
# WHERE from.id IN $ids AND to.id IN $ids AND from.id <> to.id AND from.id > to.id
# CALL apoc.algo.dijkstra(from, to, 'CONNECTED_TO', 'distance')
# YIELD path, weight
# RETURN from.id as from, to.id as to, weight as distance
# '''

NODE_DISTANCE_EXHAUSTIVE = '''
// Query for start-to-storage distances
MATCH (from: Origin {id: 'start'}), (to: Storage)
WHERE to.id IN $ids
CALL apoc.algo.dijkstra(from, to, 'CONNECTED_TO', 'distance')
YIELD path, weight
RETURN from.id as from, to.id as to, weight as distance

UNION ALL

// Query for storage-to-storage distances
MATCH (from: Storage), (to: Storage)
WHERE from.id IN $ids AND to.id IN $ids AND from.id <> to.id AND from.id > to.id
CALL apoc.algo.dijkstra(from, to, 'CONNECTED_TO', 'distance')
YIELD path, weight
RETURN from.id as from, to.id as to, weight as distance

UNION ALL

// Query for storage-to-end distances
MATCH (from: Storage), (to: Origin {id: $destId})
WHERE from.id IN $ids
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