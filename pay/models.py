from django.db import models
from api.models import InProgressCart
# Create your models here.

class AuthorityCart(models.Model):
    authority = models.CharField(max_length=36,primary_key=True)
    cart = models.ForeignKey(InProgressCart,on_delete=models.CASCADE)
