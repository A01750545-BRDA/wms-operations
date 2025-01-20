### Spatial Nodes
CREATE_STORAGE = '''
CREATE (:Storage {
    id: $id,
    rack: $rack,
    index: $index,
    level: $level,
    cornerType: $cornerType,
    colHall: $colHall,
    rowHall: $rowHall,
    x: $x,
    y: $y,
    z: $z
})'''

CREATE_INTERSECTION = '''
CREATE (:Intersection {
    id: $id,
    row: $row,
    col: $col,
    x: $x,
    y: $y,
    z: 0
})'''

CREATE_ORIGIN = '''
CREATE (:Origin {
    id: $id,
    x: $x,
    y: $y,
    z: 0
})'''

### Spatial relationships
CONNECT_STORAGE_VERTICALLY = '''
MATCH (s1: Storage), (s2: Storage)
WHERE s1.rack = s2.rack
  AND s1.index = s2.index
  AND s1.level + 1 = s2.level
WITH s1, s2, abs(s1.x - s2.x) as x, abs(s1.y - s2.y) as y, abs(s1.z - s2.z) as z
CREATE (s1)-[:CONNECTED_TO {
    distance: x + y + z,
    x: x,
    y: y,
    z: z
}]->(s2)
'''

CONNECT_STORAGE_HORIZONTALLY = '''
MATCH (s1: Storage), (s2: Storage)
WHERE s1.rack = s2.rack
AND s1.level = s2.level
AND s1.level = 1
AND abs(s1.index - s2.index) = 1
WITH s1, s2, abs(s1.x - s2.x) as x, abs(s1.y - s2.y) as y
CREATE (s1)-[:CONNECTED_TO {
    distance: x + y,
    x: x,
    y: y,
    z: 0
}]->(s2)
'''

CONNECT_INTERSECTION_STORAGE = '''
MATCH (i: Intersection), (s: Storage)
WHERE s.level = 1 AND (
    (s.cornerType = 'first' AND i.row = s.rowHall AND i.col = s.colHall) OR
    (s.cornerType = 'last' AND i.row = s.rowHall + 1 AND i.col = s.colHall)
)

WITH i, s, abs(i.x - s.x) as x, abs(i.y - s.y) as y
CREATE (i)-[:CONNECTED_TO {
    distance: x + y,
    x: x,
    y: y,
    z: 0
}]->(s)
'''

CONNECT_INTERSECTION = '''
MATCH (i1: Intersection), (i2: Intersection)
WHERE (abs(i1.row - i2.row) = 1 AND i1.col = i2.col) OR
    (abs(i1.col - i2.col) = 1 AND i1.row = i2.row)

WITH i1, i2, abs(i1.x - i2.x) as x, abs(i1.y - i2.y) as y
CREATE (i1)-[:CONNECTED_TO {
    distance: x + y,
    x: x,
    y: y,
    z: 0
}]->(i2)
'''

CONNECT_IN_ORIGIN = '''
MATCH (o: Origin), (i: Intersection)
WHERE o.id IN $originIds AND i.id IN $intersectionIds
WITH o, i, (o.x - i.x) as x, (o.y - i.y) as y
CREATE (o)-[:CONNECTED_TO {
    distance: (x^2 + y^2)^0.5,
    x: x,
    y: y,
    z: 0
}]->(i)
'''

CONNECT_OUT_ORIGIN = '''
MATCH (o: Origin), (i: Intersection)
WHERE o.id IN $originIds AND i.id IN $intersectionIds
WITH o, i, (o.x - i.x) as x, (o.y - i.y) as y
CREATE (i)-[:CONNECTED_TO {
    distance: (x^2 + y^2)^0.5,
    x: x,
    y: y,
    z: 0
}]->(o)
'''

### Objects
CREATE_PALLET = '''
CREATE (:Pallet {
    id: $id
})'''

ADD_PALLET_TO_STORAGE = '''
MATCH (s: Storage), (p: Pallet)
WHERE s.id = $storageId AND p.id = $palletId
CREATE (s)-[:STORES]->(p)
'''

CREATE_PRODUCT = '''
CREATE (:Product {
    id: $id
})'''

ADD_PRODUCT_TO_PALLET = '''
MATCH (pallet: Pallet), (product: Product)
WHERE pallet.id = $palletId AND product.id = $productId
CREATE (pallet)-[:CONTAINS {quantity: $quantity}]->(product)
'''