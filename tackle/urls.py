from django.urls import path
from . import views
from .views import ListProduct, EditProduct, ProductPage
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('list-product/', ListProduct.as_view(), name='list-product'),
    path('search_brands/', views.SearchBrands.as_view(), name='search_brands'),
    path('search_categories/', views.SearchCategories.as_view(), name='search_categories'),
    path('edit-product/<int:product_id>/', EditProduct.as_view(), name='edit_product'),
    path('product/<slug:slug>', ProductPage.as_view(), name='product'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

