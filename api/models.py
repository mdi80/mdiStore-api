from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.db.models import Avg
import datetime
from .utils import get_color_name

# Create your models here.


class ImageProduct(models.Model):
    image = models.ImageField(upload_to="product_image/")


class CommentProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    comment = models.CharField(max_length=1000)
    created = models.DateField(auto_now_add=True)
    created = models.DateField(auto_now_add=True)


class Category(models.Model):
    title = models.CharField(max_length=50)
    image = models.ImageField(
        upload_to="category_image/", default="product_image/p1.jpg"
    )


class Product(models.Model):
    title = models.CharField(max_length=100)
    productCategory = models.ForeignKey(Category, null=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=1000)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    isAmazing = models.BooleanField(default=False)
    image = models.ManyToManyField(ImageProduct)

    @property
    def category_name(self):
        return self.productCategory.title


class ProductColors(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.CharField(max_length=7)

class Rating(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rate = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created = models.DateField(auto_now_add=True)


class ViewProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)


class SearchProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
    created = models.DateField(auto_now_add=True)
