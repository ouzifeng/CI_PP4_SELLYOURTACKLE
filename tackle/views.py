from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Brand, Category, Product, ProductImage
from slugify import slugify
from decimal import Decimal, InvalidOperation


@method_decorator(login_required, name='dispatch')
class ListProduct(View):
    template_name = 'list-product.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        # Get data from the form
        brand_name = request.POST.get('brand')
        category_name = request.POST.get('category')
        price = request.POST.get('price', 0)
        shipping = request.POST.get('shipping', 0)
        
        # Validation for positive price
        try:
            price = float(price)
            if price < 0:
                raise ValueError
        except ValueError:
            context = {
                'error_message': 'Please enter a valid positive price.'
            }
            return render(request, self.template_name, context)

        # Validation for positive shipping
        try:
            shipping = float(shipping)
            if shipping < 0:
                raise ValueError
        except ValueError:
            context = {
                'error_message': 'Please enter a valid positive shipping cost.'
            }
            return render(request, self.template_name, context)

        try:
            # Fetch brand and category from the database
            brand_instance = Brand.objects.get(name=brand_name)
            category_instance = Category.objects.get(name=category_name)
        except ObjectDoesNotExist:
            # Handle error if brand or category is not found
            context = {
                'error_message': 'Invalid brand or category. Please select from the suggestions.'
            }
            return render(request, self.template_name, context)

        name = request.POST.get('name')
        variation1 = request.POST.get('more-info-1', "")
        variation2 = request.POST.get('more-info-2', "")
        condition = request.POST.get('condition')
        description = request.POST.get('description')

        # Create product instance
        product = Product(
            brand=brand_instance,
            category=category_instance,
            name=name,
            variation1=variation1,
            variation2=variation2,
            condition=condition,
            description=description,
            price=price,
            shipping=shipping,
            user=request.user
        )
        product.save()

        # Handle images
        for image in request.FILES.getlist('images'):
            product_image = ProductImage(product=product, image=image)
            product_image.save()

        # If successful:
        context = {
            'success_message': 'Product added successfully!'
        }
        return render(request, self.template_name, context)
    
class SearchBrands(View):
    def get(self, request, *args, **kwargs):
        if 'term' in request.GET:
            brands = Brand.objects.filter(name__icontains=request.GET.get('term'))
            brand_list = list(brands.values_list('name', flat=True))
            return JsonResponse(brand_list, safe=False)
        return JsonResponse([], safe=False)

class SearchCategories(View):
    def get(self, request, *args, **kwargs):
        if 'term' in request.GET:
            cats = Category.objects.filter(name__icontains=request.GET.get('term'))
            cat_list = list(cats.values_list('name', flat=True))
            return JsonResponse(cat_list, safe=False)
        return JsonResponse([], safe=False)


def home(request):
    return render(request, 'index.html')


@method_decorator(login_required, name='dispatch')
class EditProduct(View):
    template_name = 'product-seller-page.html'

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, user=request.user)
        context = {
            'product': product
        }
        return render(request, self.template_name, context)

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, user=request.user)
    
        # Update product name
        product.name = request.POST.get('name')
        
        # Update price
        product.price = request.POST.get('price')
        
        # Update shipping
        product.shipping = request.POST.get('shipping')
        
        # Update brand - assuming you're setting it by name
        brand_name = request.POST.get('brand')
        brand_instance = Brand.objects.get(name=brand_name)
        product.brand = brand_instance
        
        # Update category - assuming you're setting it by name
        category_name = request.POST.get('category')
        category_instance = Category.objects.get(name=category_name)
        product.category = category_instance
        
        # Update additional info
        product.variation1 = request.POST.get('more-info-1')
        product.variation2 = request.POST.get('more-info-2')
        
        # Update description
        product.description = request.POST.get('description')
        
        # Save the product instance
        product.save()
    
        # Handle image deletion
        images_to_delete = request.POST.getlist('delete_images')
        for image_id in images_to_delete:
            image = ProductImage.objects.get(id=image_id)
            image.delete()

        # Handle new image uploads
        for uploaded_file in request.FILES.getlist('images'):
            ProductImage.objects.create(product=product, image=uploaded_file)        

        return redirect('selling')

