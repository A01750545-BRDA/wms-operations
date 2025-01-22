from neo4j import Record
from collections import defaultdict
import plotly.graph_objects as go
from IPython.display import HTML
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt

def plot_3d_coords(coords):
    """
    Generates an interactive 3D plot of the given coordinates.

    Args:
      coords: A list of tuples, where each tuple represents a 3D point (x, y, z).
    """
    x = [coord[0] for coord in coords]
    y = [coord[1] for coord in coords]
    z = [coord[2] for coord in coords]

    fig = go.Figure(data=[go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode='markers',
        marker=dict(
            size=5,
            color=z,  # Set color based on z-coordinate
            colorscale='Viridis',  # Choose a colorscale
            opacity=0.8
        )
    )])

    max_ = max(max(x), max(y), max(z))

    # Update layout for equal proportions
    fig.update_layout(
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            xaxis=dict(range=[min(x), max(x)]),  # Set the range for x-axis
            yaxis=dict(range=[min(y), max(y)]),  # Set the range for y-axis
            zaxis=dict(range=[min(z), max(z)]),  # Set the range for y-axis
            aspectmode='manual',
            aspectratio=dict(x=max(x)/max_,y=5*max(y)/max_,z=max(z)/max_)
        ),
        title='3D Coordinates Plot'
    )

    fig.show()


def animate_tsp_path(coords: list, best_tour: list[int], interval: int = 75):
    fig, ax = plt.subplots(figsize=(7, 7))

    tour_coords = [coords[i] for i in best_tour]
    xs, ys = zip(*tour_coords)

    # Añadir padding
    x_pad = 0.2 * (max(xs) - min(xs))
    y_pad = 0.2 * (max(ys) - min(ys))
    ax.set_xlim(min(xs) - x_pad, max(xs) + x_pad)
    ax.set_ylim(min(ys) - y_pad, max(ys) + y_pad)

    ax.scatter(xs, ys, c='black', s=15, zorder=2) # Graficar ciudades
    line, = ax.plot([], [], 'b-', lw=2, zorder=1) # Inicializar linea
    point, = ax.plot([], [], 'ro', markersize=10, zorder=3) # Inicializar punto

    def init():
        line.set_data([], [])
        point.set_data([], [])
        return line, point

    def animate(frame):
        x_data = xs[:frame+1]
        y_data = ys[:frame+1]

        line.set_data(x_data, y_data)

        # Mover punto a la siguiente ciudad
        if frame < len(tour_coords):
            point.set_data([x_data[-1]], [y_data[-1]])

        return line, point

    anim = FuncAnimation(fig, animate, init_func=init,
                         frames=len(tour_coords),
                         interval=interval, blit=True)

    plt.axis('equal')
    plt.tight_layout()
    html_anim = HTML(anim.to_jshtml())
    return html_anim


def animate_computed_path(path: list[Record], interval: int = 50):
    ground_nodes_visited = [
        (node['x'], node['y']) 
        for step in path for node in step['path'] 
        #if node['z'] == 0
    ]
    
    coords_to_index = {coord: i for i, coord in enumerate(list(set(ground_nodes_visited)))}
    detailed_tour = [coords_to_index[coord] for coord in ground_nodes_visited]

    return animate_tsp_path(list(coords_to_index.keys()), detailed_tour, interval)

def animate_multiple_tsp_paths(coords_list: list[list], tours_list: list[list[int]], interval: int = 75):
    fig, ax = plt.subplots(figsize=(7, 7))
    
    # Flatten the list of coordinates and generate unique coordinates for each tour.
    all_coords = [coord for coords in coords_list for coord in coords]
    all_tours = [tour for tour in tours_list]

    # Create a mapping from coordinates to a unique index
    coord_to_index = {tuple(coord): i for i, coord in enumerate(all_coords)}

    # Prepare multiple tours by converting coordinates to indices
    indexed_tours = [
        [coord_to_index[tuple(coord)] for coord in coords_list[i]] 
        for i in range(len(tours_list))
    ]

    # Flatten all coordinates for the plot bounds
    xs, ys = zip(*all_coords)
    x_pad = 0.2 * (max(xs) - min(xs))
    y_pad = 0.2 * (max(ys) - min(ys))
    
    ax.set_xlim(min(xs) - x_pad, max(xs) + x_pad)
    ax.set_ylim(min(ys) - y_pad, max(ys) + y_pad)

    # Plot cities as static points
    ax.scatter(xs, ys, c='black', s=15, zorder=2)

    # Initialize the lines and points for each tour
    lines = [ax.plot([], [], 'b-', lw=2, zorder=1)[0] for _ in tours_list]
    points = [ax.plot([], [], 'ro', markersize=10, zorder=3)[0] for _ in tours_list]

    def init():
        for line, point in zip(lines, points):
            line.set_data([], [])
            point.set_data([], [])
        return [line for line in lines] + [point for point in points]

    def animate(frame):
        # Update each tour's path up to the current frame
        for tour_idx, (tour, line, point) in enumerate(zip(indexed_tours, lines, points)):
            x_data = [all_coords[i][0] for i in tour[:frame+1]]
            y_data = [all_coords[i][1] for i in tour[:frame+1]]

            line.set_data(x_data, y_data)

            if frame < len(tour):
                point.set_data([x_data[-1]], [y_data[-1]])

        return [line for line in lines] + [point for point in points]

    # Create the animation
    anim = FuncAnimation(fig, animate, init_func=init,
                         frames=max(len(tour) for tour in indexed_tours),
                         interval=interval, blit=True)

    plt.axis('equal')
    plt.tight_layout()
    html_anim = HTML(anim.to_jshtml())
    return html_anim

def animate_computed_multiple_paths(paths: list[list], interval: int = 50):
    # Extract coordinates and tours from the computed path list
    coords_list = []
    tours_list = []

    for path in paths:
        ground_nodes_visited = [
            (node['x'], node['y']) 
            for step in path for node in step['path']
        ]
        coords_list.append(ground_nodes_visited)
        
        coords_to_index = {coord: i for i, coord in enumerate(set(ground_nodes_visited))}
        detailed_tour = [coords_to_index[coord] for coord in ground_nodes_visited]
        tours_list.append(detailed_tour)

    return animate_multiple_tsp_paths(coords_list, tours_list, interval)

def product_list_from_summary(summary):
    res = defaultdict(int)
    for _, products in summary.items():
        for product, info in products.items():
            res[product] += info['take']

    return dict(res)

def product_list_from_summaries(summaries):

    product_list = defaultdict(int)
    dicts = [product_list_from_summary(summary) for summary in summaries]

    for d in dicts:
        for key, value in d.items():
            product_list[key] += value

    return dict(product_list)

def product_list_from_flat_summaries(summaries):

    product_list = defaultdict(int)

    for summary in summaries:
        for element in summary:
            key = element['product_id']
            value = element['take']

            product_list[key] += value

    return dict(product_list)