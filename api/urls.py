from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    UserViewSet,
    GetUser,
    GetProduct,
    GetProductsWithParam,
    GetCategories,
    AddActToCommnet,
    AddFavoriteProduct,
    GetComments,
)
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    path("login/", obtain_auth_token, name="login"),
    path("", include(router.urls)),
    path("get-user/", GetUser.as_view(), name="getuser"),
    path("get-product/<int:id>/", GetProduct.as_view(), name="getproduct"),
    path("get-product-with-param/", GetProductsWithParam.as_view(), name="getproducts"),
    path("get-categories/", GetCategories.as_view(), name="getproducts"),
    path("add-commnet-like/", AddActToCommnet.as_view(), name="addCommentLike"),
    path("add-product-fav/", AddFavoriteProduct.as_view(), name="addProductFav"),
    path("get-comments/", GetComments.as_view(), name="getComments"),
]
