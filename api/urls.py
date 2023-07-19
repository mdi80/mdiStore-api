from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from .views import *
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    path("login/", obtain_auth_token, name="login"),
    path("", include(router.urls)),
    path("get-user/", GetUser.as_view(), name="getuser"),
    path("get-home-content/", GetHome.as_view(), name="getHome"),
    path("get-product/<int:id>/", GetProduct.as_view(), name="getproduct"),
    path("get-product-with-param/", GetProductsWithParam.as_view(), name="getproducts"),
    path("get-categories/", GetCategories.as_view(), name="getcategory"),
    path("add-commnet-like/", AddActToCommnet.as_view(), name="addCommentLike"),
    path("add-product-fav/", AddFavoriteProduct.as_view(), name="addProductFav"),
    path("get-comments/", GetComments.as_view(), name="getComments"),
    path("add-comment/", AddComment.as_view(), name="addComment"),
    path("alter-comment/", AlterComment.as_view(), name="alterComment"),
    path("can-add-new-comment/", CanAddCommnet.as_view(), name="canAddComment"),
    path("rate-product/", AddRate.as_view(), name="rateProduct"),
    path("get-own-rate/", GetOwnRate.as_view(), name="getOwnRate"),
    path("get-header/", GetHeader.as_view(), name="getheader"),
]
