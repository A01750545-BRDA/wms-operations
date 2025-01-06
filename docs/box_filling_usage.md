# Box Filling Animation Usage

This document provides instructions on how to set up and run the box filling animation project located in the `box_filling` folder.

## Prerequisites

Make sure you have the following installed on your machine:

- Python (version 3.6 or higher)
- Node.js (version 14 or higher)

## Steps to Use the Box Filling Folder

### 1. Install JavaScript Dependencies

Navigate to the `box_filling` directory in your terminal and run the following command to install the required JavaScript library:

```bash
npm install --save three
```

### 2. Start the Vite Development Server

After installing the dependencies, start the Vite development server by running:

```bash
npx vite
```

This command will start the server and provide you with a local host URL (usually `http://localhost:5173`).

### 3. Run the Python FastAPI Application

In a separate terminal window, navigate to the `box_filling` directory and run the FastAPI application:

```bash
python packing.py
```

This will start the FastAPI server, typically accessible at `http://127.0.0.1:8001`.

### 4. Open the Application in Your Browser

Once both servers are running, open your web browser and go to the URL provided by the Vite server (e.g., `http://localhost:5173`). You should see the box stacking animation interface.

## Conclusion

You are now set up to use the box filling animation project! You can interact with the animation using the provided buttons to start, reset, or step backward through the animation.