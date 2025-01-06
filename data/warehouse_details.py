
class WarehouseSpecs:
    dimensions = {
        'hall': {
            'x': 6,
            'y': 4,
        },
        'palett': {
            'x': 1.2,
            'y': 1,
            'z': 2,
        }
    }

    details = {
        'hall': {
            'n_cols': 10 + 1,
            'n_rows': 5 + 1,
        },
        'rack': {
            'indexes': 13,
            'levels': 5,
        }
    }

    X = (
        details['hall']['n_cols'] * dimensions['hall']['x'] +
        (details['hall']['n_cols'] - 1) * dimensions['palett']['x'] * details['rack']['indexes']
    )
    Y = (
        details['hall']['n_rows'] * dimensions['hall']['y'] +
        (details['hall']['n_rows'] - 1) * dimensions['palett']['y'] * 2
    )
    Z = dimensions['palett']['z'] * details['rack']['levels']

    unique_positions = (
        (details['hall']['n_rows'] - 1) *
        (details['hall']['n_cols'] - 1) *
        2 *
        details['rack']['indexes'] *
        details['rack']['levels']
    )
    unique_products = 1000