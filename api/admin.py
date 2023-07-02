from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Product)
admin.site.register(CommentProduct)
admin.site.register(ImageProduct)
admin.site.register(Rating)
admin.site.register(Category)
admin.site.register(ViewProduct)
admin.site.register(SearchProduct)
admin.site.register(ProductColors)
