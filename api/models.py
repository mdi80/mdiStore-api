from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.db.models import Avg
import datetime
from .utils import get_color_name

# Create your models here.


class ImageProduct(models.Model):
    image = models.ImageField(upload_to="product_image/")


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
    active = models.BooleanField(default=True)

    @property
    def category_name(self):
        return self.productCategory.title


class CommentProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    comment = models.CharField(max_length=1000, null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    isLiked = models.BooleanField()
    created = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")


class commentUserLike(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    comment = models.ForeignKey(CommentProduct, on_delete=models.CASCADE)
    liked = models.BooleanField(null=False)


class UserFavoriteProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "product")


class ProductColors(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.CharField(max_length=7)


class Rating(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rate = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")


class ViewProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "product")


class SaleProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)


class CartUser(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    products = models.ManyToManyField(Product)


class CartHistory(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    products = models.ManyToManyField(Product)
    cartPrice = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)


class SearchProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
    created = models.DateField(auto_now_add=True)
