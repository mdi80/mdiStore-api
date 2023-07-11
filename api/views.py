import json
from django.shortcuts import render
from django.contrib.auth import get_user_model, authenticate, login

from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework import viewsets, generics, status

from .models import (
    Product,
    Category,
    UserFavoriteProduct,
    commentUserLike,
    CommentProduct,
)
from .serilizers import UserSerilizer, ProductSerilizer, CategorySerilizer

User = get_user_model()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    serilizer = UserSerilizer(request.user)
    return Response(serilizer.data)


class GetProduct(generics.RetrieveAPIView):
    permission_classes = [
        AllowAny,
    ]
    queryset = Product.objects.all()
    serializer_class = ProductSerilizer
    lookup_field = "id"


class GetProductsWithParam(generics.ListAPIView):
    permission_classes = [
        AllowAny,
    ]
    queryset = Product.objects.all()
    serializer_class = ProductSerilizer

    def get_queryset(self):
        queryset = super().get_queryset()
        print(self.request.GET)
        if "amazing" in self.request.GET:
            queryset = queryset.filter(isAmazing=True)
        if "categoryId" in self.request.GET:
            queryset = queryset.filter(
                productCategory=int(self.request.GET["categoryId"])
            )
        if "minPrice" in self.request.GET:
            queryset = queryset.exclude(price__lt=float(self.request.GET["minPrice"]))
        if "maxPrice" in self.request.GET:
            queryset = queryset.exclude(price__gt=float(self.request.GET["maxPrice"]))
        if "hasDiscount" in self.request.GET:
            queryset = queryset.exclude(discount=0)
        if "sort-mostExpensive" in self.request.GET:
            queryset = queryset.order_by("price")
        if "sort-lessExpensive" in self.request.GET:
            queryset = queryset.order_by("-price")

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        serializer = self.get_serializer(queryset, many=True)
        serialized_data = serializer.data
        print(len(serialized_data))
        for row in serialized_data[:]:
            if "minRating" in self.request.GET:
                if row["rating"] < float(self.request.GET["minRating"]):
                    serialized_data.remove(row)

            if "colors" in self.request.GET:
                if not set(self.request.GET["colors"].split(",")).intersection(
                    set(row["color_values"])
                ):
                    serialized_data.remove(row)

        returnedData = dict()
        returnedData["lenght"] = len(serialized_data)

        if "sort-mostSale" in self.request.GET:
            serialized_data = sorted(
                serialized_data, key=lambda row: row["sales"], reverse=True
            )
        if "sort-mostRating" in self.request.GET:
            serialized_data = sorted(
                serialized_data, key=lambda row: row["rating"], reverse=True
            )
        if "sort-mostView" in self.request.GET:
            serialized_data = sorted(
                serialized_data, key=lambda row: row["views"], reverse=True
            )

        if "endIndex" in self.request.GET:
            serialized_data = serialized_data[: int(self.request.GET["endIndex"])]
        if "startIndex" in self.request.GET:
            serialized_data = serialized_data[int(self.request.GET["startIndex"]) :]
        returnedData["data"] = serialized_data
        return Response(returnedData)


class GetCategories(generics.ListAPIView):
    permission_classes = [
        AllowAny,
    ]
    queryset = Category.objects.all()
    serializer_class = CategorySerilizer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def list(self, request, *args, **kwargs):
        li = self.get_queryset()
        print(li)
        return Response(li)


class AddFavoriteProduct(APIView):
    # authentication_classes = [
    #     TokenAuthentication,
    # ]
    permission_classes = [
        AllowAny,
    ]

    def get(self, request):
        try:
            user = get_user_model().objects.filter(id=request.GET["user"]).first()
            productId = request.GET["product"]
            liked = request.GET["liked"] == 1
            if liked:
                fav = UserFavoriteProduct(
                    user=user, product=Product.objects.filter(id=productId).first()
                )
                fav.save()
            else:
                fav = UserFavoriteProduct.objects.get(
                    user=user, product=Product.objects.filter(id=productId).first()
                )
                if fav:
                    fav.delete()
                    return Response(status=status.HTTP_202_ACCEPTED)

            return Response(status=status.HTTP_201_CREATED)

        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class AddActToCommnet(APIView):
    # authentication_classes = [
    #     TokenAuthentication,
    # ]
    # permission_classes = [
    #     IsAuthenticated,
    # ]
    permission_classes = [
        AllowAny,
    ]

    def get(self, request):
        try:
            user = get_user_model().objects.filter(id=request.GET["user"]).first()
            commentId = request.GET["comment"]
            mstatus = int(request.GET["status"])

            if (
                commentUserLike.objects.filter(
                    user=user,
                    comment=CommentProduct.objects.filter(id=commentId).first(),
                ).count()
                == 0
            ):
                if not mstatus == -1:  # ignore if row does not exists
                    actOnComment = commentUserLike(
                        user=user,
                        comment=CommentProduct.objects.filter(id=commentId).first(),
                        liked=(mstatus == 1),
                    )
                    actOnComment.save()
            else:
                comAct = commentUserLike.objects.filter(
                    user=user,
                    comment=CommentProduct.objects.filter(id=commentId).first(),
                ).first()
                if mstatus == -1:  # delete row
                    comAct.delete()
                else:
                    comAct.liked = mstatus == 1
            return Response(status=status.HTTP_202_ACCEPTED)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class GetUser(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        user = request.user
        return Response({"username": user.username, "email": user.email})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerilizer
    permission_classes = (AllowAny,)

    def create(self, request):
        print("here")
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if User.objects.filter(username=username).exists():
            return Response(
                {"message": "Username already exists!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the user account
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user = authenticate(request, username=username, password=password)

        login(request, user)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})
