import json
from django.shortcuts import render
from django.contrib.auth import get_user_model, authenticate, login
from django.db import IntegrityError, ProgrammingError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework import viewsets, generics, status

from .models import *
from .serilizers import *

User = get_user_model()


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


class GetProduct(generics.RetrieveAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = Product.objects.all()
    serializer_class = ProductSerilizer
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        try:
            productId = self.kwargs.get("id")
            product = Product.objects.get(id=productId)
            user = request.user

            if ViewProduct.objects.filter(user=user, product=product).count() == 0:
                print("Add view")
                view = ViewProduct(user=user, product=product)
                view.save()

        except:
            print("Error while add Product view")
            pass

        return super().get(request, *args, **kwargs)


class GetProductsWithParam(generics.ListAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = Product.objects.all()
    serializer_class = ProductSerilizer

    def get_queryset(self):
        queryset = super().get_queryset()
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
            queryset = queryset.order_by("-price")
        if "sort-lessExpensive" in self.request.GET:
            queryset = queryset.order_by("price")

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        serializer = self.get_serializer(queryset, many=True)
        serialized_data = serializer.data
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
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
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
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user
            productId = request.GET["product"]
            liked = request.GET["liked"] == "1"
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
        except IntegrityError:
            return Response("Already saved!", status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response("Already deleted!", status=status.HTTP_200_OK)

        except ProgrammingError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class AddActToCommnet(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user
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


class GetComments(generics.ListAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    queryset = CommentProduct.objects.all()
    serializer_class = CommentSerilizer

    def get_queryset(self):
        queryset = super().get_queryset()
        pId = self.request.GET["productId"]
        queryset = queryset.filter(product=Product.objects.get(id=pId))

        return queryset

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()

            serializer = self.get_serializer(queryset, many=True)
            serialized_data = serializer.data

            returnedData = dict()
            returnedData["lenght"] = len(serialized_data)

            for row in serialized_data:
                userId = row["user"]
                try:
                    row["username"] = get_user_model().objects.get(id=userId).username
                except:
                    row["username"] = "Unknown User"

            if "endIndex" in self.request.GET:
                serialized_data = serialized_data[: int(self.request.GET["endIndex"])]
            if "startIndex" in self.request.GET:
                serialized_data = serialized_data[int(self.request.GET["startIndex"]) :]
            returnedData["data"] = serialized_data
            return Response(returnedData)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class AddComment(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        try:
            productId = request.POST["productId"]
            comment = request.POST["comment"]
            isLike = request.POST["liked"] == 1

            user = request.user
            product = Product.objects.get(id=productId)

            if (
                not CommentProduct.objects.filter(product=product, user=user).count()
                == 0
            ):
                return Response(
                    "Comment Already exists!", status=status.HTTP_400_BAD_REQUEST
                )

            comment = CommentProduct(
                product=product, user=user, comment=comment, isLiked=isLike
            )
            comment.save()

            return Response("Created Successfuly.", status=status.HTTP_201_CREATED)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class AlterComment(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user

            commentId = int(request.GET["commentId"])
            comment = CommentProduct.objects.get(id=commentId)
            if not comment.user == user:
                return Response(
                    "Current User Not Allowed!", status=status.HTTP_403_FORBIDDEN
                )
            if "delete" in request.GET:
                comment.delete()
                return Response("Successfuly Deleted", status=status.HTTP_202_ACCEPTED)

            if "comment" in request.GET:
                comment.comment = request.GET["comment"]
            if "isLike" in request.GET:
                comment.isLiked = request.GET["isLike"] == "1"
            comment.save()

            return Response("Successfuly edited.", status=status.HTTP_202_ACCEPTED)
        except ObjectDoesNotExist:
            return Response(
                "Comment ID does not exists!", status=status.HTTP_406_NOT_ACCEPTABLE
            )
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
