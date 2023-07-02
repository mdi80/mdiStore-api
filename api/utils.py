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


# def get_color_name(requested_colour):
#     try:
#         return webcolors.hex_to_name(requested_colour)
#     except ValueError:
#         return closest_colour(requested_colour)


def get_color_name(hex):
    try:
        return webcolors.hex_to_name(hex)

    except ValueError:
        return convert_rgb_to_names(webcolors.hex_to_rgb(hex))
