from scipy.spatial import KDTree
import webcolors


def convert_rgb_to_names(rgb_tuple):
    # a dictionary of all the hex and their respective names in css3
    css3_db = webcolors.CSS3_HEX_TO_NAMES
    names = []
    rgb_values = []
    for color_hex, color_name in css3_db.items():
        names.append(color_name)
        rgb_values.append(webcolors.hex_to_rgb(color_hex))

    kdt_db = KDTree(rgb_values)
    distance, index = kdt_db.query(rgb_tuple)
    return names[index]


def get_color_name(hex):
    try:
        return webcolors.hex_to_name(hex)

    except ValueError:
        return convert_rgb_to_names(webcolors.hex_to_rgb(hex))


def calculate_post_price(products_cart, state, city):
    total_weight = 0

    for pr in products_cart:
        weight = pr.product.price / 100  # TODO add weight to product
        total_weight += weight

    if weight < 2:
        return 2
    if weight < 10:
        return 5
    if weight < 50:
        return 10

    return 20


def calculate_total_price(products_cart):
    total_price = 0

    for pr in products_cart:
        price = pr.product.price
        discount = pr.product.discount
        count = pr.count
        total_price += count * (price - discount)

    return total_price
