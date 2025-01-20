# Example Usage with Python

This document provides examples of how to use the warehouse management system programmatically with Python.

## Prerequisites

Make sure you have the required dependencies installed. You can do this by running:

```bash
pip install -r requirements.txt
```

## Example: Optimizing Picking

Here’s how you can use the `PickingService` to optimize the picking process:

### Step 1: Import Required Modules

```python
from services.picking_service import PickingService
```

### Step 2: Define product list

```python
product_list = {
    'Product_1': 10,
    'Product_2': 5
}
```

Or generate one randomly:

```python
from config.settings import Config
from logic.warehouse_operations import simulate_product_list

product_list_size = 300

with Config.db.driver.session() as session:
    product_list = session.execute_read(
        simulate_product_list, 
        n=product_list_size
    )
```

### Step 3: Use the picking service

You can create an instance of `PickingService` and call its methods directly:

```python
# Create an instance of PickingService
picking_service = PickingService(is_testing=True)

# Optimize picking
picking_solution = picking_service.optimize(
    product_list,  
    debug=True
)
```

## Running the Application

To run the FastAPI application, use the following command:

```bash
python main.py
```

You can then access the API at `http://0.0.0.0:8000`.

To optimize a picking route, access `http://0.0.0.0:8000/picking/optimize`
, where the request body is a product list like the one shown in step 3 of the example.

To get the latest picking order and optimize it's route, access `http://0.0.0.0:8000/picking/latest-order`.
No request arguments are needed.