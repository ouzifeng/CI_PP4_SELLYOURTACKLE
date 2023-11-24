from .views import Cart


def cart_processor(request):
    """
    Compile the total number of items in the cart
    """
    cart = Cart(request)
    return {'total_items_in_cart': len(cart)}
