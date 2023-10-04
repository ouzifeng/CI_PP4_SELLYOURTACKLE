from .views import Cart

def cart_processor(request):
    cart = Cart(request)
    return {'total_items_in_cart': len(cart)}
