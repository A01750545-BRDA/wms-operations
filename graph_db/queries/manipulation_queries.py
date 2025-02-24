STORAGE_LOCATION_RETRIEVER = '''
MATCH (from)
WHERE from.id = $startId
UNWIND $productList as productItem
WITH from, productItem[0] as productId, productItem[1] as desiredQuantity

MATCH (product:Product {id: productId})<-[contains:CONTAINS]-(storage:Storage)
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
    productId as product_id,
    storage.quantity as quantity,
    storage.storageId as storage_id,
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
    from.id as from_location,
    to.id as to_location,
    weight as distance,
    [n in nodes(path) WHERE n.z = 0] as path
'''

RESERVE_PRODUCTS = '''
UNWIND $pickingList as item
MATCH (storage :Storage {id: item.from_location})-[contains: CONTAINS]-(product: Product {id: item.gwin})
MERGE (storage)-[r: RESERVE]->(product)
ON CREATE SET r.quantity = item.quantity
ON MATCH SET r.quantity = r.quantity + item.quantity
WITH contains.quantity - item.quantity as new_quantity, contains
CALL apoc.do.when(
    new_quantity > 0,
    "SET contains.quantity = new_quantity",
    "DELETE contains",
    {new_quantity: new_quantity, contains: contains}
) YIELD value
RETURN value
'''

CANCEL_RESERVED_PRODUCTS = '''
UNWIND $pickingList as item
MATCH (storage :Storage {id: item.from_location})-[reserve: RESERVE]-(product: Product {id: item.gwin})
MERGE (storage)-[c: CONTAINS]->(product)
ON CREATE SET c.quantity = item.quantity
ON MATCH SET c.quantity = c.quantity + item.quantity
WITH reserve.quantity - item.quantity as new_quantity, reserve
CALL apoc.do.when(
    new_quantity > 0,
    "SET reserve.quantity = new_quantity",
    "DELETE reserve",
    {new_quantity: new_quantity, reserve: reserve}
) YIELD value
RETURN value
'''

RELEASE_RESERVED_PRODUCTS = '''
UNWIND $pickingList as item
MATCH (:Storage {id: item.from_location})-[reserve: RESERVE]-(product: Product {id: item.gwin})
WITH reserve.quantity - item.quantity as new_quantity, reserve
CALL apoc.do.when(
    new_quantity > 0,
    "SET reserve.quantity = new_quantity",
    "DELETE reserve",
    {new_quantity: new_quantity, reserve: reserve}
) YIELD value
RETURN value
'''

ADD_PRODUCT_TO_LOCATION = """
MATCH (s: Storage {id: $location})
MATCH (product: Product {id: $productId})
MERGE (s)-[c:CONTAINS]->(product)
ON MATCH SET c.quantity = c.quantity + $quantity
ON CREATE SET c.quantity = $quantity
"""

MOVE_PRODUCT_TO_LOCATION = """
MATCH (product: Product {id: $gwin})
OPTIONAL MATCH (:Storage {id: $fromLocation})-[c1: CONTAINS]-(product)
CALL apoc.util.validate(c1 IS NULL, $fromLocation + " does not have product: " + $gwin, [product])

WITH c1.quantity - $quantity as new_quantity, c1, product
CALL apoc.util.validate(new_quantity < 0, $fromLocation + " has " + c1.quantity + " products of: " + $gwin + ", not enough to move " + $quantity, [new_quantity])

MATCH (s:Storage {id: $toLocation})
MERGE (s)-[c: CONTAINS]->(product)
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
OPTIONAL MATCH (s)-[:CONTAINS]->(product)
WITH collect(product) as products, s
WITH s.rack as rack, 
     max(s.level) as level_count,
     COUNT(DISTINCT s.id) as total,
     COUNT(CASE WHEN NOT isEmpty(products) THEN 1 ELSE NULL END) as occupied
ORDER BY size(rack), rack
RETURN collect({
    rack: rack,
    level_count: level_count,
    total: total,
    occupied: occupied
}) as data
"""

GET_RACK_LEVELS = """
MATCH (s: Storage)
WHERE s.rack = $rack
OPTIONAL MATCH (s)-[:CONTAINS]->(product)
WITH collect(product) as products, s
WITH s.level as level,
     COUNT(DISTINCT s.id) as total,
     COUNT(CASE WHEN NOT isEmpty(products) THEN 1 ELSE NULL END) as occupied
ORDER BY level
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
MATCH (s:Storage)-[c:CONTAINS]->(product:Product)
WHERE s.id = $storageId
RETURN collect({
    gwin: product.id,
    quantity: c.quantity
}) as data
"""

GET_RACK_LEVEL_PRODUCTS = """
MATCH (s:Storage)
WHERE s.rack = $rack AND s.level = $level
OPTIONAL MATCH (s)-[c:CONTAINS]->(product:Product)
WITH s.id AS storageId, 
     collect(CASE 
                WHEN product.id IS NULL OR c.quantity IS NULL THEN NULL
                ELSE {gwin: product.id, quantity: c.quantity}
             END) AS data, s.index as index
ORDER BY index ASC
WITH collect([storageId, data]) AS allData
RETURN apoc.map.fromPairs(allData) AS result
"""