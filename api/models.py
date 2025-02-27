from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.db.models import Avg
import datetime
from .utils import get_color_name
from django.core.exceptions import ValidationError

# Create your models here.


class HomeContent(models.Model):
    contnetTypeChoice = (
        ("HeaderComponent", "Image Header"),
        ("CategoryCom", "Category"),
        ("ScrollableRowList", "Scrollable Content"),
        ("GridProductView", "Grid Poduct"),
        ("SimpleRowComp", "Simple Row Content"),
    )

    contentType = models.CharField(max_length=100, choices=contnetTypeChoice)
    title = models.CharField(max_length=50)
    subtitle = models.CharField(max_length=50, blank=True)
    api_name = models.CharField(max_length=200)
    params = models.JSONField(blank=True, null=True)
    order = models.IntegerField(unique=True)


class Header(models.Model):
    image = models.ImageField(upload_to="header_images/")
    link = models.CharField(max_length=200)


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
    recDays = models.IntegerField(default=7)
    added = models.DateField(auto_now_add=True)

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
        constraints = [
            models.CheckConstraint(
                check=models.Q(rate__gte=0) & models.Q(rate__lte=5),
                name="check_rate_range",
            )
        ]

    # def clean(self):
    #     if (
    #         SaleProduct.objects.filter(user=self.user, product=self.product).count()
    #         == 0
    #     ):
    #         raise ValidationError("User did not buy this product!")


class ViewProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    visited = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")


class SaleProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)


class CurrentCartUser(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through="ProductCart")


class ProductCart(models.Model):
    cart = models.ForeignKey(CurrentCartUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=1)


class AddressUser(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    address = models.CharField(max_length=1000)
    postal_code = models.BigIntegerField()
    phone = models.CharField(max_length=12)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)


class InProgressCart(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through="IPProductCart")
    recorded_date = models.DateTimeField(auto_now_add=True)
    address = models.ForeignKey(AddressUser, on_delete=models.PROTECT)
    # post_price = models.IntegerField()
    # totalPrice = models.DecimalField(max_digits=10, decimal_places=2)
    # send = models.BooleanField(default=False)
    # send_date = models.DateField(null=True, blank=True)
    # paid = models.BooleanField(default=False)


class IPProductCart(models.Model):
    cart = models.ForeignKey(InProgressCart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=1)


class PaidCart(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through="ProductPaidCart")
    recorded_date = models.DateTimeField()
    address = models.CharField(max_length=2000, default="Tehran")
    phone = models.CharField(max_length=15, default="Tehran")
    postal_code = models.BigIntegerField(default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    post_amount = models.DecimalField(max_digits=10, decimal_places=2)
    ref_id = models.PositiveBigIntegerField()
    authority = models.CharField(max_length=36)
    paid_date = models.DateTimeField(auto_now_add=True)
    send = models.BooleanField(default=False)
    send_date = models.DateField(null=True, blank=True)
    recived_date = models.DateField(null=True, blank=True)


class ProductPaidCart(models.Model):
    cart = models.ForeignKey(PaidCart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unitPrice = models.PositiveIntegerField()
    discount = models.IntegerField(default=0)
    count = models.PositiveIntegerField(default=1)


class PurcheseRefCart(models.Model):
    ipcart = models.ForeignKey(
        InProgressCart, on_delete=models.PROTECT, related_name="purchese_ref"
    )
    amount = models.BigIntegerField()
    purcheseId = models.BigIntegerField()
    purcheseDate = models.DateTimeField(auto_now_add=True)


class SearchProduct(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
    searched = models.DateTimeField(auto_now_add=True)


class MessageModel(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    message = models.CharField(max_length=2000)
    send_date = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    active = models.BooleanField(default=True)


class TrackOrderModel(models.Model):
    cart = models.OneToOneField(PaidCart, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
