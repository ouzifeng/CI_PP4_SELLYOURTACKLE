# Python standard library imports
from decimal import Decimal, InvalidOperation

# Django core imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import RedirectView, TemplateView
from django.views.generic.edit import DeleteView
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q
from io import BytesIO
from django.core.mail import EmailMessage

# Third-party imports
import stripe
from PIL import Image
from slugify import slugify
from stripe.error import StripeError

# App-specific imports
from .forms import CheckoutForm, ContactSellerForm
from .models import (
    Brand, Category, Product, ProductImage,
    ProductVisibility, WebhookLog
)
from auth_app.models import Address, CustomUser, CustomUserManager, Order, OrderItem



stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, user=request.user)
    product.delete()
    return redirect(reverse('selling'))


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
            user=request.user,
            visibility=ProductVisibility.LIVE
        )
        product.save()

        # Handle images
        for uploaded_file in request.FILES.getlist('images'):
            processed_image = process_image(uploaded_file)
            # Convert the processed image back to a Django InMemoryUploadedFile to save to the model
            from io import BytesIO
            from django.core.files.uploadedfile import InMemoryUploadedFile
            temp_file = BytesIO()
            processed_image.save(temp_file, format='JPEG')
            uploaded_file = InMemoryUploadedFile(temp_file, None, uploaded_file.name, 'image/jpeg', temp_file.tell(), None)
            
            product_image = ProductImage(product=product, image=uploaded_file)
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


class HomeView(TemplateView):
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(visibility=ProductVisibility.LIVE).exclude(financial_status="sold")
        return context



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
        
    
        # Check if the "delete_product" button was clicked
        if 'delete_product' in request.POST:
            product.delete()
            return redirect('selling')
        
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.shipping = request.POST.get('shipping')
        brand_name = request.POST.get('brand')
        brand_instance = Brand.objects.get(name=brand_name)
        product.brand = brand_instance
        category_name = request.POST.get('category')
        category_instance = Category.objects.get(name=category_name)
        product.category = category_instance
        product.variation1 = request.POST.get('more-info-1')
        product.variation2 = request.POST.get('more-info-2')
        product.description = request.POST.get('description')
        product.visibility = request.POST.get('visibility')
        
        product.save()
    
        images_to_delete = request.POST.getlist('delete_images')
        for image_id in images_to_delete:
            image = ProductImage.objects.get(id=image_id)
            image.delete()

        for uploaded_file in request.FILES.getlist('images'):
            processed_image = process_image(uploaded_file)
            temp_file = BytesIO()
            processed_image.save(temp_file, format='JPEG')
            uploaded_file = InMemoryUploadedFile(temp_file, None, uploaded_file.name, 'image/jpeg', temp_file.tell(), None)
            
            ProductImage.objects.create(product=product, image=uploaded_file)
     
        return redirect('selling')

class ProductPage(View):
    template_name = 'product.html'
    
    def get(self, request, slug, *args, **kwargs):
        product = get_object_or_404(Product, slug=slug)
        images = product.images.all()
        context = {
            'product': product,
            'images': images
        }
        return render(request, self.template_name, context)
    
    
@method_decorator(login_required, name='dispatch')
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product_confirm_delete.html'
    success_url = reverse_lazy('selling')

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)    
    

def process_image(image, target_filesize=2.5*1024*1024, max_width=894):
    """
    Process an uploaded image using Pillow to fit the intrinsic size, compress it, and ensure max width.
    """
    img = Image.open(image)
    print(f"Original Image Size: {img.size}, Original Image Format: {img.format}")

    # Check if the width exceeds the maximum width and resize if necessary
    if img.width > max_width:
        aspect_ratio = img.height / img.width
        new_height = int(aspect_ratio * max_width)
        img = img.resize((max_width, new_height), Image.LANCZOS)
        print(f"Resized to: {img.size}")

    # Save the image to BytesIO to check the file size
    buffer = BytesIO()
    quality = 100
    img.save(buffer, format="JPEG", quality=quality)
    
    # Reduce quality to meet target file size
    while len(buffer.getvalue()) > target_filesize and quality > 30: # Set a lower bound for quality
        buffer = BytesIO()
        quality -= 2  # Decrease by smaller steps
        img.save(buffer, format="JPEG", quality=quality)

    # Convert BytesIO buffer image back to PIL Image
    compressed_image = Image.open(buffer)

    return compressed_image  
 



class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, price):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'price': str(price),
                'quantity': 1,
                'product_id': product.id,
                'thumbnail_id': product.images.first().id if product.images.first() else None,
                'shipping_cost': str(product.shipping)
            }
        else:
            self.cart[product_id]['quantity'] += 1
        self.save()



    def save(self):
        """
        Mark the session as "modified" to ensure it's saved.
        """
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database.
        """
        product_ids = self.cart.keys()
        # Get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids).prefetch_related('images')
        for product in products:
            self.cart[str(product.id)]['product'] = product
            self.cart[str(product.id)]['product_id'] = product.id
            self.cart[str(product.id)]['thumbnail'] = product.images.first()
            self.cart[str(product.id)]['shipping_cost'] = product.shipping

        for item in self.cart.values():
            item['price'] = Decimal(item['price'])
            item['shipping_cost'] = Decimal(item.get('shipping_cost', 0))
            item['total_price'] = (item['price'] * item['quantity']) + item['shipping_cost']
            item['thumbnail'] = (item['thumbnail'])
            yield item



    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
    
    def get_shipping_total(self):
        return sum(Decimal(item['shipping_cost']) * item['quantity'] for item in self.cart.values())
    
    def get_combined_total(self):
        """
        Get the combined total of product prices and shipping costs.
        """
        return self.get_total_price() + self.get_shipping_total()


    def clear(self):
        """
        Remove the cart from session.
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()
        
    def contains(self, product):
        """Check if the cart contains a particular product."""
        product_id = str(product.id)
        return product_id in self.cart
     


class AddToCartView(View):
    def post(self, request, product_id):
        cart = Cart(request) 
        product = get_object_or_404(Product, id=product_id)

        if not product.is_in_stock():
            messages.warning(request, f"{product.name} is already sold!")
            return redirect('product', slug=product.slug)

        if cart.contains(product):
            messages.warning(request, f"{product.name} is already in your cart!")
            return redirect('product', slug=product.slug)

        cart.add(product, price=product.price)
        messages.success(request, f"{product.name} has been added to your cart!")
        return redirect('cart')


class CartView(TemplateView):
    template_name = 'cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = Cart(self.request)  
        return context

class RemoveFromCartView(View):
    def post(self, request, product_id):
        cart = Cart(request)  
        product = get_object_or_404(Product, id=product_id)

        cart.remove(product)

        return redirect('cart')

class CheckoutView(TemplateView):
    template_name = 'checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Create a SetupIntent
        try:
            setup_intent = stripe.SetupIntent.create()
            context['client_secret'] = setup_intent['client_secret']
        except StripeError as e:
            context['error'] = str(e)  # Handle this error as you see fit
        
        context['cart'] = Cart(self.request)
        
        data = {}  # Initialize an empty dictionary

        # Check if user is authenticated
        if self.request.user.is_authenticated:
            user = self.request.user
            billing_address = Address.objects.filter(user=user, address_type='billing').first()
            
            # For billing address
            if billing_address:
                data.update({
                    'first_name': billing_address.first_name,
                    'last_name': billing_address.last_name,
                    'email': billing_address.email,
                    'phone_number': billing_address.phone_number,
                    'billing_address_line1': billing_address.address_line1,
                    'billing_address_line2': billing_address.address_line2,
                    'billing_city': billing_address.city,
                    'billing_state': billing_address.state,
                    'billing_postal_code': billing_address.postal_code,
                })
        else:
            # If user is not authenticated, just initialize the form with empty values
            data.update({
                'first_name': "",
                'last_name': "",
                'email': "",
                'phone_number': "",
                'billing_address_line1': "",
                'billing_address_line2': "",
                'billing_city': "",
                'billing_state': "",
                'billing_postal_code': "",
            })

        # Initialize the form with the data dictionary outside of the checks
        context['form'] = CheckoutForm(initial=data)

        return context



    def post(self, request, *args, **kwargs):
        # This will be where your handle_payment logic will reside
        return HttpResponse("index.html")
    
    

class CheckoutSuccessView(View):
    def post(self, request):
        cart = Cart(request)
        return redirect('home')


def distribute_pending_funds():
    # Fetch all paid orders that haven't been distributed yet.
    paid_orders = Order.objects.filter(payment_status='completed', status='paid')

    for order in paid_orders:
        for order_item in order.items.all():
            seller = order_item.seller
            amount_due = order_item.get_total_item_price_with_shipping()

            # Use the Stripe API to transfer funds
            try:
                transfer = stripe.Transfer.create(
                    amount=int(amount_due * 100),  # Convert to cents
                    currency='gbp',
                    destination=seller.stripe_account_id,
                    transfer_group=str(order.id)
                )
                # Optionally, mark this order or order item as distributed in your database.
                # order.distributed = True
                # order.save()

            except stripe.error.StripeError as e:
                # Handle any Stripe errors (e.g., insufficient funds, account not fully set up, etc.)
                print(str(e))
                # Optionally, log the error or send a notification.


class ProductSoldView(View):
    template_name = "product-sold-page.html"

    def get(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=kwargs['pk'])
        
        # Get the order item associated with the product
        order_item = OrderItem.objects.filter(product=product).first()

        # Ensure we have an order item before trying to access its order
        if order_item:
            order = order_item.order
            shipping_address = order.shipping_address
        else:
            order = None
            shipping_address = None

        context = {
            'product': product,
            'order': order,
            'shipping_address': shipping_address
        }
        
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=kwargs['pk'])
        order_item = OrderItem.objects.filter(product=product).first()

        if order_item:
            order = order_item.order
            action = request.POST.get('action')
            
            # Check if the action is to mark as dispatched
            if action == 'mark_dispatched':
                order.status = 'shipped'
                order.save()
                # Redirect back to the product sold page after updating
                return redirect('product_sold', pk=product.id)
            
            # Check if the action is to mark as refunded
            elif action == 'mark_refunded':
                # Refund the order
                try:
                    stripe.Refund.create(
                        payment_intent=order.payment_intent_id
                    )
                    order.status = 'refunded'
                    order.save()
                except stripe.error.StripeError as e:
                    messages.error(request, f"Stripe error: {str(e)}")
                return redirect('product_sold', pk=product.id)

            # Handle updating tracking info
            tracking_company = request.POST.get('tracking_company')
            tracking_number = request.POST.get('tracking_number')

            if tracking_company and tracking_number:
                order.tracking_company = tracking_company
                order.tracking_number = tracking_number
                order.save()
        
        return redirect('product_sold', pk=product.id)        

class OrderPageView(View):
    template_name = "detailed-order-page.html"
    form_class = ContactSellerForm

    def get(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'])

        # Get the product associated with the order.
        order_item = OrderItem.objects.filter(order=order).first()
        
        product = None
        if order_item:
            product = order_item.product
        
        context = {
            'product': product,
            'order': order,
            'shipping_address': order.shipping_address,
            'form': self.form_class()
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'])
        order_item = OrderItem.objects.filter(order=order).first()
        product = order_item.product if order_item else None

        form = self.form_class(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message_content = form.cleaned_data['message']
            buyer_email = order.user.email
            seller_email = order_item.seller.email if order_item else None

            # Append the link to the seller's order management page
            seller_order_link = request.build_absolute_uri(reverse('product_sold', args=[order_item.product.id]))
            message_content += f"\n\nManage the order details here: {seller_order_link}"

            if seller_email:
                # Create and send the email to the seller with the buyer's details for reply
                email = EmailMessage(
                    subject,
                    message_content,
                    'hello@sellyourtackle.co.uk',
                    [seller_email],
                    reply_to=[buyer_email],
                )
                email.send()
                messages.success(request, "Your message has been sent to the seller.")
            else:
                messages.error(request, "Could not send email. Seller's email not found.")

            return redirect('order-page', pk=kwargs['pk'])

        context = {
            'product': product,
            'order': order,
            'shipping_address': order.shipping_address,
            'form': form
        }
        
        return render(request, self.template_name, context)
    

class OrderConfirmation(View):
    template_name = 'order-confirmation.html'
    
    def get(self, request, pk, *args, **kwargs):
        order = get_object_or_404(Order, pk=pk)

        # Fetch all order items associated with the order
        order_items = OrderItem.objects.filter(order=order)
        
        # Extract products from the order items
        products = [item.product for item in order_items]
        
        context = {
            'products': products,  # List of products
            'order': order,
            'shipping_address': order.shipping_address
        }

        return render(request, self.template_name, context)

class SearchView(View):
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('search_text', '')
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        ).values('name', 'slug')[:5]  # Limit to top 5 results for dropdown
        
        return JsonResponse(list(products), safe=False)
    
    
class ShopView(TemplateView):
    template_name = 'shop.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        products = Product.objects.filter(visibility=ProductVisibility.LIVE).exclude(financial_status="sold")
        
        # Retrieve filter criteria from GET parameters
        max_price = self.request.GET.get('price')
        selected_brand = self.request.GET.get('brand')
        selected_category = self.request.GET.get('category')

        # Apply filters based on the criteria
        if max_price:
            products = products.filter(price__lte=max_price)

        if selected_brand:
            products = products.filter(brand__name=selected_brand)

        if selected_category:
            products = products.filter(category__id=selected_category)

        context['products'] = products
        
        # Fetch the available brands and categories from the filtered products
        context['available_brands'] = Brand.objects.filter(id__in=products.values_list('brand', flat=True)).distinct()
        context['available_categories'] = Category.objects.filter(id__in=products.values_list('category', flat=True)).distinct()

        return context

