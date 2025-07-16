from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Category, Product, Vendor, ProductImage, CartOrder, CartItem, ProductReview, Wishlist, Address , BrandInfo, SiteSetting, Coupon, ProductColor, ProductSize
from taggit.managers import TaggableManager
from django.utils.html import format_html, format_html_join
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Prefetch
from django.contrib.auth.models import User

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['image_preview']
    
    def image_preview(self, instance):
        if instance.image:
            return mark_safe(f'<img src="{instance.image.url}" width="50" height="50" />')
        return "No Image"
    image_preview.short_description = 'Preview'

class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('user', 'pid', 'title', 'price', 'category', 'product_image', 'status', 'created_at')
    list_display_links = ('title',)
    search_fields = ('pid', 'title', 'description')
    list_filter = ('category', 'vendor', 'is_featured', 'status')
    inlines = [ProductImageInline, ProductColorInline, ProductSizeInline]
    prepopulated_fields = {'slug': ('title',)}

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'vendor')

    def get_tags(self, obj):
        return ", ".join(tag.name for tag in obj.tags.all())
    get_tags.short_description = "Tags"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'cid', 'category_image')
    readonly_fields = ['category_image']
    search_fields = ('title', 'cid')
    ordering = ('title',)  # لأن 'created_at' محذوف
    # list_filter = ('created_at',) ← نحذفه لأنه مش موجود
    # prepopulated_fields = {'slug': ('title',)} ← نحذفه كمان

    def category_image(self, obj):
        if obj.image:
            return mark_safe(f'<a href="{obj.image.url}" target="_blank"><img src="{obj.image.url}" width="50" height="50" /></a>')
        return "No Image"
    category_image.short_description = 'Image'

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'user__username','vid')

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'image_preview', 'quantity', 'price', 'product_stock', 'product_sku')
    fields = ('product', 'image_preview', 'quantity', 'price', 'product_stock', 'product_sku')
    can_delete = False
    show_change_link = True

    def image_preview(self, obj):
        if obj.product and obj.product.image:
            return mark_safe(f'<img src="{obj.product.image.url}" width="50" height="50" style="object-fit:cover;" />')
        return "-"
    image_preview.short_description = 'صورة المنتج'

    def product_stock(self, obj):
        return obj.product.stock_quantity if obj.product else '-'
    product_stock.short_description = 'المخزون المتبقي'

    def product_sku(self, obj):
        return obj.product.sku if obj.product else '-'
    product_sku.short_description = 'SKU'

@admin.register(CartOrder)
class CartOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'paid_status', 'status', 'created_at')
    list_filter = ('paid_status', 'status')
    search_fields = ('order_id', 'user__username')
    readonly_fields = ('order_full_details',)
    inlines = []
    fieldsets = (
        (None, {
            'fields': ('order_full_details',)
        }),
    )

    def order_full_details(self, obj):
        try:
            # Order Summary
            try:
                summary = format_html(
                    '<div style="font-size:18px;font-weight:bold;">Order #: {}<br>Created At: {}<br>Status: <span style="color:{};font-weight:bold;">{}</span></div>',
                    obj.order_id,
                    obj.created_at.strftime('%Y-%m-%d %H:%M'),
                    '#4caf50' if obj.status == 'completed' else '#f44336' if obj.status == 'cancelled' else '#2196f3',
                    obj.get_status_display()
                )
            except Exception:
                summary = format_html('<div style="color:#f00;">Order summary not available</div>')

            # Customer Information
            try:
                customer_info = format_html(
                    '<div style="margin-top:18px;line-height:2;">'
                    '<b>Name:</b> {}<br>'
                    '<b>Email:</b> {}<br>'
                    '<b>Phone:</b> {}<br>'
                    '<b>Total Orders:</b> {}<br>'
                    '<b>Last Order:</b> {}'
                    '</div>',
                    obj.user.get_full_name() or obj.user.username,
                    obj.user.email,
                    obj.phone_number or 'Not available',
                    obj.user.orders.exclude(pk=obj.pk).count(),
                    self._last_order_html(obj)
                )
            except Exception:
                customer_info = format_html('<div style="color:#f00;">Customer info not available</div>')

            # Customer Addresses (عرض عنوان الشحن فقط)
            addresses_html = format_html('<span style="color:#888;">No shipping address found for this order.</span>')
            try:
                # --- تفاصيل المنتجات المختارة (اسم، لون، مقاس، كمية) ---
                try:
                    items = obj.items.select_related('product')
                    if items and items.exists():
                        products_info = []
                        for item in items:
                            products_info.append(format_html(
                                '<div style="margin-bottom:6px;padding:7px 12px;background:#f7f7f7;border-radius:5px;display:inline-block;min-width:220px;">'
                                '<b>Product:</b> {}<br>'
                                '<b>Color:</b> {}<br>'
                                '<b>Size:</b> {}<br>'
                                '<b>Quantity:</b> {}'
                                '</div>',
                                item.product.title if item.product else '-',
                                item.color_name or '-',
                                item.size or '-',
                                item.quantity
                            ))
                        products_info_html = format_html_join('', '{}', ((info,) for info in products_info))
                    else:
                        products_info_html = format_html('<span style="color:#888;">No products found for this order.</span>')
                except Exception:
                    products_info_html = format_html('<span style="color:#f00;">Error loading product info</span>')

                addresses_html = format_html(
                    '<div style="margin-bottom:8px;padding:10px;background:#e3f7e3;border-radius:6px;border:2px solid #388e3c;font-weight:bold;">'
                    '<span style="color:#388e3c;font-weight:bold;">[Order Info]</span><br>'
                    '<b>{}</b>: {}<br>'
                    '<b>Phone:</b> {}<br>'
                    '<b>City:</b> {}<br>'
                    '<b>Country:</b> {}<br>'
                    '<b>Postal Code:</b> {}<br>'
                    '{}'
                    '</div>',
                    dict(obj.shipping_address.ADDRESS_TYPE_CHOICES)[obj.shipping_address.address_type] if obj.shipping_address else '-',
                    obj.shipping_address.address_line1 if obj.shipping_address else '-',
                    obj.shipping_address.phone if obj.shipping_address and hasattr(obj.shipping_address, 'phone') and obj.shipping_address.phone else (obj.phone_number or 'Not available'),
                    obj.shipping_address.city if obj.shipping_address else '-',
                    obj.shipping_address.country if obj.shipping_address else '-',
                    obj.shipping_address.postal_code if obj.shipping_address else '-',
                    products_info_html
                )
            except Exception:
                pass

            # Order Items (جدول أو رسالة ودية فقط)
            products_table = format_html('<span style="color:#888;">No products found for this order.</span>')
            try:
                items = obj.items.select_related('product')
                if items and items.exists():
                    header_cells = [
                        format_html('<th style="padding:8px;">{}</th>', col)
                        for col in ["Image", "Product Name", "Color", "Size", "Qty", "Price", "Remaining Stock"]
                    ]
                    header = format_html('<tr style="background:#f2f2f2;text-align:center;font-weight:bold;">{}</tr>', format_html_join('', '{}', ((cell,) for cell in header_cells)))
                    row_htmls = []
                    for item in items:
                        product_admin_url = f"/admin/core/product/{item.product.id}/change/" if item.product else "#"
                        row_htmls.append(format_html(
                            '<tr style="text-align:center;">'
                            '<td style="padding:8px;"><img src="{}" width="48" height="48" style="object-fit:cover;border-radius:50%;border:1.5px solid #eee;box-shadow:0 1px 3px #ccc;" /></td>'
                            '<td style="padding:8px;"><a href="{}" style="font-weight:bold;">{}</a></td>'
                            '<td style="padding:8px;">{}</td>'
                            '<td style="padding:8px;">{}</td>'
                            '<td style="padding:8px;">{}</td>'
                            '<td style="padding:8px;">${:.2f}</td>'
                            '<td style="padding:8px;">{}</td>'
                            '</tr>',
                            item.product.image.url if item.product and item.product.image else '',
                            product_admin_url,
                            item.product.title if item.product else '-',
                            item.color or '-',
                            item.size or '-',
                            item.quantity,
                            item.price,
                            item.product.stock_quantity if item.product else '-'
                        ))
                    rows = format_html_join('', '{}', ((row,) for row in row_htmls))
                    products_table = format_html(
                        '<table style="width:100%;background:#fff;border-radius:8px;overflow:hidden;margin-top:18px;border-collapse:collapse;box-shadow:0 1px 3px #eee;">'
                        '<thead>{}</thead>'
                        '<tbody>{}</tbody>'
                        '</table>', 
                        header, 
                        rows
                    )
            except Exception:
                pass

            # Order Details
            try:
                order_details = format_html(
                    '<div style="margin-top:18px;line-height:2;">'
                    '<b>Shipping Address:</b> {}<br>'
                    '<b>Order Status:</b> {}<br>'
                    '<b>Payment Status:</b> {}<br>'
                    '<b>Payment Method:</b> {}<br>'
                    '<b>Subtotal:</b> ${}<br>'
                    '<b>Tax:</b> ${}<br>'
                    '<b>Shipping:</b> ${}<br>'
                    '<b>Grand Total:</b> ${}'
                    '</div>',
                    obj.shipping_address or 'Not available',
                    obj.get_status_display(),
                    'Paid' if obj.paid_status else 'Unpaid',
                    obj.payment_method or 'Not specified',
                    obj.sub_total,
                    obj.tax_amount,
                    obj.shipping_amount,
                    obj.total
                )
            except Exception:
                order_details = format_html('<div style="color:#f00;">Order details not available</div>')

            return format_html(
                '<div style="padding:20px;background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">'
                '{}<hr style="border-top:1px solid #eee;">'
                '{}<hr style="border-top:1px solid #eee;">'
                '<h3 style="margin-top:20px;">Customer Addresses</h3>'
                '{}<hr style="border-top:1px solid #eee;">'
                '<h3 style="margin-top:20px;">Order Items</h3>'
                '{}<hr style="border-top:1px solid #eee;">'
                '<h3 style="margin-top:20px;">Order Summary</h3>'
                '{}'
                '</div>', 
                summary, 
                customer_info, 
                addresses_html, 
                products_table, 
                order_details
            )
        except Exception as e:
            return format_html('<div style="color:#f00;font-weight:bold;">Error displaying order details: {}</div>', str(e))
    
    order_full_details.short_description = 'Complete Order Details'

    def _last_order_html(self, obj):
        last_order = obj.user.orders.exclude(pk=obj.pk).order_by('-created_at').first()
        if last_order:
            return format_html(
                '<span>#{}</span> on <span>{}</span>', 
                last_order.order_id, 
                last_order.created_at.strftime('%Y-%m-%d %H:%M')
            )
        return 'No previous orders'
    
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'quantity', 'price', 'created_at')
    list_filter = ('product', 'user')
    search_fields = ('product__title', 'user__username')

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'date_added') 
    list_filter = ('rating', 'product')
    search_fields = ('product__title', 'user__username')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'date_added')
    list_filter = ('product', 'user')
    search_fields = ('product__title', 'user__username')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_line1', 'city', 'state', 'country', 'postal_code', 'is_default')
    list_filter = ('country', 'state', 'is_default')
    search_fields = ('user__username', 'city', 'state', 'postal_code')

@admin.register(BrandInfo)
class BrandInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'preview_logo', 'preview_favicon')
    readonly_fields = ('preview_logo', 'preview_favicon')
    fieldsets = (
        (None, {
            'fields': ('name', 'title', 'description', 'advertisement')
        }),
        ("Brand Images", {
            'fields': ('logo', 'preview_logo', 'favicon', 'preview_favicon')
        }),
    )

    def preview_logo(self, obj):
        if obj.logo:
            return format_html(f'<img src="{obj.logo.url}" width="120" height="auto" style="object-fit: contain;" />')
        return "-"
    preview_logo.short_description = "Logo Preview"

    def preview_favicon(self, obj):
        if obj.favicon:
            return format_html(f'<img src="{obj.favicon.url}" width="32" height="32" style="object-fit: contain;" />')
        return "-"
    preview_favicon.short_description = "Favicon Preview"

admin.site.register(SiteSetting)
admin.site.register(Coupon)

class CustomerProductReportAdmin(admin.ModelAdmin):
    change_list_template = "admin/customer_product_report.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('customer-product-report/', self.admin_site.admin_view(self.customer_product_report), name='customer-product-report'),
        ]
        return custom_urls + urls

    def customer_product_report(self, request):
        # جلب كل العملاء مع الطلبات وعناصر الطلبات والمنتجات
        customers = User.objects.prefetch_related(
            Prefetch('orders', queryset=CartOrder.objects.prefetch_related(
                Prefetch('items', queryset=CartItem.objects.select_related('product'))
            ))
        )
        context = dict(
            self.admin_site.each_context(request),
            customers=customers,
        )
        return TemplateResponse(request, "admin/customer_product_report.html", context)

# تسجيل التقرير في الأدمن (كزر أو رابط جانبي)
admin.site.register(User, CustomerProductReportAdmin)