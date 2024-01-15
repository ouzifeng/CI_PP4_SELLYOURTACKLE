from django.urls import path
from . import views
from .views import (
    ListProduct,
    EditProduct,
    ProductPage,
    HomeView,
    AddToCartView,
    CartView,
    RemoveFromCartView,
    CheckoutSuccessView,
    CheckoutView,
    ProductSoldView,
    OrderPageView,
    OrderConfirmation,
    SearchView,
    ShopView
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path(
        'list-product/', ListProduct.as_view(), name='list-product'
    ),
    path(
        'search_brands/', views.SearchBrands.as_view(), name='search_brands'
    ),
    path(
        'search_categories/', views.SearchCategories.as_view(),
        name='search_categories'
    ),
    path(
        'edit-product/<int:product_id>/', EditProduct.as_view(),
        name='edit_product'
    ),
    path('product/<slug:slug>', ProductPage.as_view(), name='product'),
    path(
        'delete-product/<int:product_id>/', views.delete_product,
        name='delete_product'
    ),
    path('cart/', CartView.as_view(), name='cart'),
    path(
        'add_to_cart/<int:product_id>/', AddToCartView.as_view(),
        name='add_to_cart'
    ),
    path(
        'remove_from_cart/<int:product_id>/', RemoveFromCartView.as_view(),
        name='remove_from_cart'
        ),
    path(
        'checkout_success/', CheckoutSuccessView.as_view(),
        name='checkout_success'
    ),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path(
        'product-sold/<int:pk>/', ProductSoldView.as_view(),
        name='product_sold'
    ),
    path('order-page/<int:pk>/', OrderPageView.as_view(), name='order-page'),
    path(
        'order-confirmation/<int:pk>/', OrderConfirmation.as_view(),
        name='order-confirmation'
    ),
    path('search/', SearchView.as_view(), name='search'),
    path('shop/', ShopView.as_view(), name='shop'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
