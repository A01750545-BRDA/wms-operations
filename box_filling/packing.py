import random
import numpy as np
from py3dbp import Packer, Bin, Item
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Constants
CONTAINER_DIMS = [70, 50, 40]
PROPORTION = 1/5

def xyz_2_xzy(lst):
    return [lst[0], lst[2], lst[1]]

map_rotation_types = [
    lambda item: [item.width, item.height, item.depth],
    lambda item: [item.height, item.width, item.depth],
    lambda item: [item.height, item.depth, item.width],
    lambda item: [item.depth, item.height, item.width],
    lambda item: [item.depth, item.width, item.height],
    lambda item: [item.width, item.depth, item.height],
]

def compute_boxes_data(container_dims, packer):
    boxes_data = [
        {
            'pos': xyz_2_xzy([float(x) for x in item.position]),
            'size': xyz_2_xzy([float(x) for x in map_rotation_types[item.rotation_type](item)])
        }
        for item in packer.bins[0].items
    ]
    return {
        'dimensions': container_dims,
        'boxes_data': sorted(boxes_data, key=lambda x: x['pos'][1])
    }

def generate_packing_result():
    packer = Packer()
    box = Bin('Little box', *CONTAINER_DIMS, 30)
    packer.add_bin(box)
    
    upper = (np.array(CONTAINER_DIMS) * PROPORTION * 2).astype(int)
    lower = (np.array(CONTAINER_DIMS) * PROPORTION).astype(int)
    
    for i in range(round(1/PROPORTION**3)):
        item = Item(
            i,
            random.randint(lower[0], upper[0]),
            random.randint(lower[1], upper[1]),
            random.randint(lower[2], upper[2]),
            0
        )
        packer.add_item(item)
    
    packer.pack()
    return compute_boxes_data(CONTAINER_DIMS, packer)

# Pre-calculate result
RESULT = generate_packing_result()

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/data')
def get_boxes_data():
    return RESULT

if __name__ == '__main__':
    uvicorn.run(app, port=8001)