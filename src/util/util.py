|
from colorsys import rgb_to_hls, hls_to_rgb




def find_id_in_parents(searcher, target_id):
    """
    Searches recursively for an element among the ancestors of a Kivy element by its id

    Args:
        searcher (_type_): the object that starts the search, usually a Kivy widget.
        target_id (_type_): the object's id to find.

    Returns:
        _type_: the found object or None
    """    

    
    parent = searcher.parent
    while parent:
        if hasattr(parent, 'ids') and target_id in parent.ids:
            return parent.ids[target_id]
        parent = parent.parent
    return None




def tame_color(color, desaturation=0.0, lighten=0.0):
    """
    Desaturates and lightens an RGB colour.

    Args:
        color (tuple): A 3-tuple of RGB in range 0–1, e.g., (0.5, 0.2, 0.8)
        desaturation (float): 0 = no change, 1 = fully desaturated (greyscale)
        lighten (float): 0 = no change, 1 = fully white

    Returns:
        tuple: Modified RGB tuple in range 0–1
    """
    r, g, b = color
    h, l, s = rgb_to_hls(r, g, b)

    s = s * (1 - desaturation)
    l = l + (1 - l) * lighten  # shift l toward 1 (white)

    r_out, g_out, b_out = hls_to_rgb(h, l, s)
    return (r_out, g_out, b_out)