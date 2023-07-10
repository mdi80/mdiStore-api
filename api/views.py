import json
from django.shortcuts import render
from django.contrib.auth import get_user_model, authenticate, login

from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework import viewsets, status, generics

from .models import Product, Category
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

        return Response(serialized_data)


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
        return li


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
