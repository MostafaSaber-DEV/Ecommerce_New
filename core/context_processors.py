from core.models import Category, Vendor, Product
from django.db.models import Count, Q
from taggit.models import Tag

def categories_processor(request):
    return {
        'categories': Category.objects.annotate(
            product_count=Count('category_products',
                                filter=Q(category_products__status='published'))
        ).filter(product_count__gt=0).order_by('title'),
        
        'vendors': Vendor.objects.all()[:10],

        'tags': Tag.objects.annotate(
            tagged_count=Count('taggit_taggeditem_items')
        ).order_by('-tagged_count')[:15],

        'featured_products': Product.objects.filter(
            is_featured=True,
            status='published'
        ).select_related('vendor', 'category')[:5],
    }
