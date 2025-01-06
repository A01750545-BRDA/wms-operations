# Project README

## Overview

This project is a warehouse management system that includes a box filling animation interface, utilizes FastAPI for the backend and Neo4j for database management. It includes functionalities for optimizing picking routes, managing inventory, and visualizing warehouse data.

## Project Structure

The project is organized into several key directories and files, each serving a specific purpose:

```
wms-operations/
│
├── api/                        # Contains the FastAPI application and route definitions
│   ├── routes/                 # API route definitions
│   │   ├── __init__.py         # Initializes the routes package
│   │   ├── picking.py          # Routes for picking operations
│   │   └── warehouse.py        # (Placeholder for future warehouse routes)
│   ├── schemas/                # Pydantic models for request and response validation
│   │   ├── __init__.py         # Initializes the schemas package
│   │   ├── request_models.py    # Request models for API endpoints
│   │   └── response_models.py   # Response models for API endpoints
│   └── __init__.py             # Initializes the api package
│
├── config/                     # Configuration settings for the application
│   ├── __init__.py             # Initializes the config package
│   └── settings.py             # Configuration settings and database connections
│
├── data/                       # Data models and warehouse specifications
│   ├── __init__.py             # Initializes the data package
│   └── warehouse_details.py     # Warehouse specifications and dimensions
│
├── docs/                       # Documentation for the project
│   ├── box_filling_usage.md    # Instructions for setting up and running the box filling animation
│   └── usage.md                # Examples of using the warehouse management system programmatically with Python
|
├── graph_db/                   # Database queries and connection management
│   ├── __init__.py             # Initializes the graph_db package
│   ├── connection.py            # Neo4j database connection management
│   ├── queries/                 # Database query definitions
│   │   ├── __init__.py         # Initializes the queries package
│   │   ├── creation_queries.py  # Queries for creating nodes and relationships
│   │   ├── manipulation_queries.py # Queries for manipulating data
│   │   └── utility_queries.py   # Utility queries for data retrieval
│   └── seed.py                  # Script for seeding the database with initial data
│
├── logic/                      # Business logic and operations
│   ├── __init__.py             # Initializes the logic package
│   ├── packing_operations.py    # Logic for packing operations
│   ├── routing_operations.py    # Logic for routing and distance calculations
│   └── warehouse_operations.py   # Logic for warehouse operations
│
├── services/                   # Service layer for handling business logic
│   ├── __init__.py             # Initializes the services package
│   ├── packing_service.py       # Service for packing operations
│   └── picking_service.py       # Service for picking operations
│
├── tests/                      # Unit tests for the application
│   ├── __init__.py             # Initializes the tests package
│   └── test_picking_service.py  # Tests for the picking service
│
├── box_filling/                # Frontend for the box filling animation
│   ├── index.html              # HTML file for the animation interface
│   ├── main.js                 # JavaScript file for handling the animation logic
│   └── packing.py              # FastAPI application for box packing logic
│
├── .gitignore                   # Git ignore file
├── requirements.txt             # Python dependencies
├── api_server.py                # Entry point for the FastAPI application
└── main.py                      # Main application file to run the server
```

## Key Components

- **API**: The `api` directory contains the FastAPI application, including route definitions and request/response schemas. The `picking.py` file handles endpoints related to picking operations.

- **Configuration**: The `config` directory holds configuration settings, including database connection details.

- **Data**: The `data` directory defines the warehouse specifications, including dimensions and details.

- **Database**: The `graph_db` directory manages database connections and queries for interacting with the Neo4j database.

- **Logic**: The `logic` directory contains the core business logic for packing and routing operations.

- **Services**: The `services` directory provides a layer for handling business logic, separating it from the API layer.

- **Tests**: The `tests` directory includes unit tests to ensure the functionality of the application.

- **Box Filling**: The `box_filling` directory contains the frontend and backend code for the box filling animation, including HTML and JavaScript files.

## Getting Started

To get started with the project, follow these steps:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables**: Create a `.env` file in the root directory to configure your database connection and other settings.

3. **Run the FastAPI application**:
   ```bash
   python main.py
   ```

For further implementation details and usage instructions, please refer to the documentation located in the `docs/` folder, specifically `docs/box_filling_usage.md` and `docs/usage.md`.