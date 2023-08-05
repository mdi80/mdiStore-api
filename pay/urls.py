from django.urls import path, include
from .views import *


urlpatterns = [
    path("pay/", payCartView, name="pay"),
    path("request/", send_request, name="request"),
    path("verify/", verify, name="verify"),
]
