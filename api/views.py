from django.shortcuts import render
from .serilizers import UserSerilizer, ProductSerilizer
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate, login
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from .models import Product
from rest_framework import viewsets, status, generics
import json
User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serilizer = UserSerilizer(request.user)
    return Response(serilizer.data)


class GetProduct(APIView):
    permission_classes = [AllowAny, ]

    def get(self, request):

        id = request.GET['id']
        product = Product.objects.get(id=id)
        serilizer = ProductSerilizer(product)

        return Response(serilizer.data)


class GetProductsWithParam(generics.ListAPIView):
    permission_classes = [AllowAny, ]
    queryset = Product.objects.all()
    serializer_class = ProductSerilizer

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'amazing' in self.request.GET:
            queryset = queryset.filter(isAmazing=True)
        return queryset


class GetUser(APIView):
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        user = request.user
        return Response({'username': user.username, 'email': user.email})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerilizer
    permission_classes = (AllowAny,)

    def create(self, request):
        print("here")
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if User.objects.filter(username=username).exists():
            return Response({'message': "Username already exists!"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the user account
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user = authenticate(request, username=username, password=password)

        login(request, user)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
