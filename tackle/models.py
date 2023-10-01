from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.conf import settings
from decimal import Decimal

class Brand(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        db_table = "tackle_brand"

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        db_table = "tackle_category"

    def __str__(self):
        return self.name

class Condition(models.TextChoices):
    PERFECT = "Perfect", "Perfect - never been used and no blemishes"
    EXCELLENT = "Excellent", "Excellent- a few minor cosmetic issues"
    GOOD = "Good", "Good - some dings and scratches"
    FAIR = "Fair", "Fair - extensive cosmetic issues"

    def __str__(self):
        return f"{self.label} {self.additional_info}"

class ProductStatus(models.TextChoices):
    UNSOLD = 'unsold', 'Unsold'
    SOLD = 'sold', 'Sold'

class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=210, unique=True)
    variation1 = models.CharField(max_length=100, blank=True, null=True)
    variation2 = models.CharField(max_length=100, blank=True, null=True)
    condition = models.CharField(max_length=100, choices=Condition.choices)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(
        max_length=10,
        choices=ProductStatus.choices,
        default=ProductStatus.UNSOLD
    )

    def __str__(self):
        return f"Product id: {str(self.id)}, name: {self.name}, brand: {self.brand.name}, category: {self.category.name}, condition: {self.condition}"

    def save(self, *args, **kwargs):
        # Combine the item name with variations before saving
        variations = []
        if self.variation1:
            variations.append(self.variation1)
        if self.variation2:
            variations.append(self.variation2)
        if variations:
            self.name = f"{self.name} - {', '.join(variations)}"
        
        # Generate the slug
        slug_str = slugify(self.name)
        unique_slug = slug_str
        num = 1
        
        while Product.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{slug_str}-{num}"
            num += 1

        self.slug = unique_slug

        super(Product, self).save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="product-images/")

    def __str__(self):
        return str(self.id)

