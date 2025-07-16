from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import os
import uuid
from userauths.models import User
from taggit.managers import TaggableManager
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils import timezone
import shortuuid

STATUS_CHOICES = (
    ('drafted', _('Drafted')),
    ('pending', _('Pending')),
    ('processing', _('Processing')),
    ('awaiting_payment', _('Awaiting Payment')),
    ('awaiting_dispatch', _('Awaiting Dispatch')),
    ('shipping', _('Shipping')),
    ('delivered', _('Delivered')),
    ("published", _('Published')),
    ('completed', _('Completed')),
    ('cancelled', _('Cancelled')),
    ('returned', _('Returned')),
    ('refunded', _('Refunded')),
    ('failed', _('Failed')),
    ('rejected', _('Rejected')),
    ('on_hold', _('On Hold')),
    ('disputed', _('Disputed')),
    ('under_review', _('Under Review')),
    ('active', _('Active')),
    ('inactive', _('Inactive')),
    ('archived', _('Archived')),
)

RATING_CHOICES = (
    (1, _("⭐★★★★")),
    (2, _("⭐⭐★★★")),
    (3, _("⭐⭐⭐★★")),
    (4, _("⭐⭐⭐⭐★")),
    (5, _("⭐⭐⭐⭐⭐")),
)

def user_directory_path(instance, filename):
    ext = os.path.splitext(filename)[-1]
    filename = f"{uuid.uuid4().hex}{ext}"
    return '{0}/{1}/{2}'.format(
        instance.__class__.__name__.lower(),
        instance.user.id if hasattr(instance, 'user') and instance.user else 'default',
        filename
    )

def validate_image_size(value):
    limit = 2 * 1024 * 1024
    if value.size > limit:
        raise ValidationError(_('Image size cannot exceed 2MB.'))

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        abstract = True

class Category(models.Model):
    cid = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix='cat_',
        editable=True,
        verbose_name=_('Category ID')
    )
    title = models.CharField(max_length=100, unique=True, verbose_name=_('Title'))
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        validators=[validate_image_size],
        verbose_name=_('Image')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['title']

    def category_image(self):
        if self.image:
            return mark_safe(
                f'<img src="{self.image.url}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />'
            )
        return mark_safe('<div style="width:50px;height:50px;background:#f0f0f0;display:inline-block;"></div>')

    category_image.short_description = _('Image Preview')

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'cid': self.cid})

    def __str__(self):
        return self.title

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return self.user.username

class Vendor(TimeStampedModel):
    vid = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix='ven_',
        editable=True,
        verbose_name=_('Vendor ID')
    )
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Vendor Name'))
    email = models.EmailField(max_length=254, unique=True, verbose_name=_('Email Address'))
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name=_('Phone Number'))
    image = models.ImageField(
        upload_to=user_directory_path,
        blank=True,
        null=True,
        validators=[validate_image_size],
        verbose_name=_('Logo Image')
    )
    description = RichTextUploadingField(blank=True, null=True, verbose_name=_('Description'))
    website = models.URLField(blank=True, null=True, verbose_name=_('Website URL'))
    address = models.TextField(blank=True, null=True, verbose_name=_('Business Address'))
    shipping_on_time = models.CharField(
        max_length=20,
        choices=[('yes', _('Yes')), ('no', _('No'))],
        default='yes',
        verbose_name=_('On-Time Shipping')
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)],
        verbose_name=_('Customer Rating')
    )
    authentic_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)],
        verbose_name=_('Authenticity Rating')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vendors',
        blank=True,
        null=True,
        verbose_name=_('User Account')
    )
    is_verified = models.BooleanField(default=False, verbose_name=_('Is Verified'))
    slug = models.SlugField(max_length=150, unique=True, blank=True, verbose_name=_('Slug'))

    class Meta:
        verbose_name = _('Vendor')
        verbose_name_plural = _('Vendors')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Vendor.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def vendor_image(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />')
        return mark_safe('<div style="width:50px;height:50px;background:#f0f0f0;display:inline-block;"></div>')

    vendor_image.short_description = _('Logo Preview')

    def get_absolute_url(self):
        return reverse('vendor_detail', kwargs={'slug': self.slug})

    def clean(self):
        if self.phone and not self.phone.isdigit():
            raise ValidationError({'phone': _('Phone number should contain only digits.')})

    def __str__(self):
        return f"{self.name} ({'Verified' if self.is_verified else 'Not Verified'})"

class Product(TimeStampedModel):
    pid = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix='prod_',
        editable=True,
        verbose_name=_('Product ID')
    )
    sku = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix='sku_',
        editable=False,
        verbose_name=_('SKU')
    )
    slug = models.SlugField(max_length=150, unique=True, blank=True, verbose_name=_('Slug'))
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('Owner')
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('Vendor')
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='category_products',
        verbose_name=_('Category')
    )
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    description = RichTextUploadingField(blank=True, null=True, verbose_name=_('Description'))
    specifications = models.TextField(blank=True, null=True, verbose_name=_('Specifications'))
    image = models.ImageField(
        upload_to=user_directory_path,
        blank=True,
        null=True,
        validators=[validate_image_size],
        verbose_name=_('Main Image')
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Stock Quantity')
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Current Price')
    )
    items_sold = models.PositiveIntegerField(default=0, verbose_name=_('Items Sold'))
    old_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.01)],
        verbose_name=_('Original Price')
    )
    tags = TaggableManager(blank=True, verbose_name=_('Tags'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='drafted',
        verbose_name=_('Status')
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)],
        verbose_name=_('Rating')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    is_published = models.BooleanField(default=False, verbose_name=_('Published'))
    digital = models.BooleanField(default=False, verbose_name=_('Digital Product'))
    is_featured = models.BooleanField(default=False, verbose_name=_('Featured'))
    is_new = models.BooleanField(default=True, verbose_name=_('New Arrival'))
    is_best_seller = models.BooleanField(default=False, verbose_name=_('Best Seller'))
    is_discounted = models.BooleanField(default=False, verbose_name=_('Discounted'))
    is_on_sale = models.BooleanField(default=False, verbose_name=_('On Sale'))
    is_returnable = models.BooleanField(default=True, verbose_name=_('Returnable'))
    is_refundable = models.BooleanField(default=True, verbose_name=_('Refundable'))
    is_verified = models.BooleanField(default=False, verbose_name=_('Verified'))
    is_archived = models.BooleanField(default=False, verbose_name=_('Archived'))

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        if self.old_price and self.old_price > self.price:
            self.is_discounted = True
        else:
            self.is_discounted = False
            
        super().save(*args, **kwargs)

    def get_percentage_discount(self):
        if self.old_price and self.old_price > 0:
            return round(((self.old_price - self.price) / self.old_price) * 100, 2)
        return 0

    def product_image(self):
        if self.image:
            return mark_safe(
                f'<img src="{self.image.url}" width="50" height="50" '
                'style="object-fit: cover; border-radius: 5px;" />'
            )
        return mark_safe(
            '<div style="width:50px;height:50px;background:#f0f0f0;'
            'display:inline-block;"></div>'
        )
    product_image.short_description = _('Image Preview')

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return f"{self.title} (PID: {self.pid})"

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='additional_images',
        verbose_name=_('Product')
    )
    image = models.ImageField(
        upload_to=user_directory_path,
        validators=[validate_image_size],
        verbose_name=_('Image')
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name=_('Date Added'))

    def image_preview(self):
        return mark_safe(f'<img src="{self.image.url}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />')
    
    image_preview.short_description = _('Image Preview')
    
    class Meta:
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')  
        ordering = ['-date']

    def __str__(self):  
        return f"{self.product.title} - Image {self.id}" if self.product else "Orphaned Image"

    def save(self, *args, **kwargs):
        if not self.product:
            raise ValidationError(_('Product must be set for additional images.'))
        super().save(*args, **kwargs)


class Cart(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='carts')
    completed = models.BooleanField(default=False, verbose_name=_("Completed"))
    order = models.ForeignKey(
        'CartOrder', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='cart'
    )

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())















class CartOrder(TimeStampedModel):
    order_id = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix='ord_',
        editable=False,
        verbose_name=_('Order ID')
    )
    invoice_no = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_('Invoice Number')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('User')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Order Status')
    )
    paid_status = models.BooleanField(
        default=False,
        verbose_name=_('Payment Status')
    )
    sub_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Subtotal')
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Tax Amount')
    )
    shipping_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Shipping Cost')
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Order Total')
    )
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Payment Method')
    )
    payment_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Payment Date')
    )
    shipping_address = models.ForeignKey(
        'Address',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='shipping_orders',
        verbose_name=_('Shipping Address')
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Phone Number'))

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.invoice_no:
            date_val = self.created_at if self.created_at else timezone.now()
            self.invoice_no = f"INV-{date_val.strftime('%Y%m%d')}-{shortuuid.random(length=4)}"
        # نسخ رقم الهاتف من Customer عند الإنشاء فقط
        if not self.phone_number and hasattr(self.user, 'customer'):
            self.phone_number = self.user.customer.phone
        # إنشاء عنوان افتراضي إذا لم يوجد أي عنوان للمستخدم
        if not self.user.addresses.exists():
            from core.models import Address
            Address.objects.create(
                user=self.user,
                address_type='shipping',
                address_line1='Default Address',
                city='Default City',
                state='Default State',
                postal_code='00000',
                country='Default Country',
                is_default=True
            )
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        items = self.items.all()
        self.sub_total = sum(item.total_price for item in items)
        self.total = self.sub_total + self.tax_amount + self.shipping_amount
        self.save()
    
    def __str__(self):
        return f"Order #{self.order_id} - {self.user.username}"

class CartItem(TimeStampedModel):
    cart = models.ForeignKey(  # ✅ العلاقة الجديدة مع Cart
        'Cart',
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Cart'),
        blank=True,
        null=True
    )
    order = models.ForeignKey(
        CartOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Order'),
        blank=True,
        null=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('User')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('Product')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name=_('Quantity')
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Unit Price')
    )
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Color'))
    size = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Size'))
    color_hex = models.CharField(max_length=7, blank=True, null=True, verbose_name=_('Color Hex'))
    color_name = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Color Name'))
    item_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Item Status')
    )

    @property
    def total_price(self):
        return self.price * self.quantity

    class Meta:
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')
        ordering = ['-created_at']
        unique_together = [['order', 'product'], ['cart', 'product']]  # ✅ دعم uniqueness في الحالتين

    def save(self, *args, **kwargs):
        if not self.price and self.product:
            self.price = self.product.price
        super().save(*args, **kwargs)

    def image_preview(self):
        if self.product.image:
            return mark_safe(
                f'<img src="{self.product.image.url}" width="50" height="50" '
                'style="object-fit: cover; border-radius: 5px;" />'
            )
        return mark_safe(
            '<div style="width:50px;height:50px;background:#f0f0f0;'
            'display:inline-block;"></div>'
        )
    image_preview.short_description = _('Image Preview')

    def __str__(self):
        return f"{self.quantity}x {self.product.title} ({self.user.username})"


class ProductReview(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Product')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_reviews',
        verbose_name=_('User')
    )
    review = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Review')
    )
    rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        default=5,
        verbose_name=_('Rating')
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Comment')
    )
    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date Added')
    )

    class Meta:
        verbose_name = _('Product Review')
        verbose_name_plural = _('Product Reviews')
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.rating} stars)"
    
    def get_rating_display(self):
        return dict(RATING_CHOICES).get(self.rating, _('No Rating'))
    
    def save(self, *args, **kwargs):
        qs = ProductReview.objects.filter(product=self.product, user=self.user)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(_('You have already reviewed this product.'))
        super().save(*args, **kwargs)

class Wishlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlists',
        verbose_name=_('User')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlists',
        verbose_name=_('Product')
    )
    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date Added')
    )

    class Meta:
        verbose_name = _('Wishlist Item')
        verbose_name_plural = _('Wishlist Items')
        ordering = ['-date_added']
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_user_product_wishlist')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.title} (Added on {self.date_added})"

class Address(TimeStampedModel):
    ADDRESS_TYPE_CHOICES = [
        ('billing', _('Billing')),
        ('shipping', _('Shipping')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    address_type = models.CharField(
        max_length=10,
        choices=ADDRESS_TYPE_CHOICES,
        default='shipping'
    )
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Phone Number'))

    class Meta:
        verbose_name_plural = "Addresses"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'is_default'],
                name='unique_user_default_address',
                condition=models.Q(is_default=True)
            )
        ]

    def __str__(self):
        return f"{self.get_address_type_display()} address for {self.user.username}"

def brand_logo_upload_path(instance, filename):
    return f"brand/logo/{filename}"

class BrandInfo(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Brand Name"))
    title = models.CharField(max_length=100, verbose_name=_("Brand Tagline"))
    description = models.TextField(max_length=255, verbose_name=_("Brand Description"))
    advertisement = models.CharField(
        max_length=100,
        verbose_name=_("Promotional Header"),
        blank=True,
        null=True
    )
    logo = models.ImageField(
        upload_to=brand_logo_upload_path,
        verbose_name=_("Logo"),
        blank=True,
        null=True
    )
    favicon = models.ImageField(
        upload_to='brand/favicon/',
        verbose_name=_("Favicon"),
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Brand Info")
        verbose_name_plural = _("Brand Info")

class SiteSetting(models.Model):
    shipping_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, verbose_name='Shipping Price')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Site Settings (Shipping: {self.shipping_price})"

    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percent')
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    min_cart_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self, cart_total):
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.expiry_date and self.expiry_date < timezone.now():
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        if cart_total < self.min_cart_total:
            return False
        return True

    def get_discount_amount(self, cart_total):
        if self.discount_type == 'percent':
            return (cart_total * self.discount_value / 100).quantize(self.discount_value)
        else:
            return min(self.discount_value, cart_total)

    def __str__(self):
        return f"{self.code} ({self.discount_type}: {self.discount_value})"

    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'

class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='colors')
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, blank=True, null=True, help_text='مثال: #ff0000')

    def __str__(self):
        return self.name

class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes')
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name