
class WarehouseSpecs:
    dimensions = {
        'hall': {
            'x': 4,
            'y': 6,
        },
        'pallet': {
            'x': 1.2,
            'y': 1,
            'z': 2,
        }
    }

    details = {
        'hall': {
            'n_cols': 3 + 1,
            'n_rows': 2 + 1,
        },
        'rack': {
            'indexes': 4,
            'levels': 1,
        }
    }

    X = (
        details['hall']['n_cols'] * dimensions['hall']['x'] +
        (details['hall']['n_cols'] - 1) * dimensions['pallet']['x'] * 2
    )
    Y = (
        details['hall']['n_rows'] * dimensions['hall']['y'] +
        (details['hall']['n_rows'] - 1) * dimensions['pallet']['y'] * details['rack']['indexes']
    )
    Z = dimensions['pallet']['z'] * details['rack']['levels']

    unique_positions = (
        (details['hall']['n_rows'] - 1) *
        (details['hall']['n_cols'] - 1) *
        2 *
        details['rack']['indexes'] *
        details['rack']['levels']
    )
    unique_products = 10