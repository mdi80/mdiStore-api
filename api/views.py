import json
from django.shortcuts import render, reverse
from django.contrib.auth import get_user_model, authenticate, login
from django.db import IntegrityError, ProgrammingError
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, JsonResponse
from django.db.models import F, ProtectedError
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework import viewsets, generics, status

from .models import *
from .serilizers import *
from .utils import calculate_post_price, calculate_total_price

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


def getSuggestedCategory(index, user):
    vp = ViewProduct.objects.filter(user=user).select_related("product")
    print(str(vp))
    vpd = ViewProductSerilizer(vp, many=True).data
    categories = dict()
    for item in vpd:
        if item["productobj"]["productCategory"] in categories:
            categories[item["productobj"]["productCategory"]] += 1
        else:
            categories[item["productobj"]["productCategory"]] = 1

    orderedCat = []
    for k in categories.keys():
        orderedCat.append({"id": k, "count": categories[k]})
    orderedCat = sorted(orderedCat, key=lambda row: row["count"], reverse=True)
    if index < len(orderedCat):
        return orderedCat[index]["id"]
    else:
        return -1


class GetHome(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user
            query = HomeContent.objects.all().order_by("order")
            content = HomeContentSerilizer(query, many=True).data
            fetchedItems = []
            mRequest = request._request
            for item in content:
                data = None
                title = item["title"]
                subtitle = item["subtitle"]
                if item["params"]:
                    mRequest.GET = item["params"]

                if item["api_name"] == "getproducts":
                    data = GetProductsWithParam.as_view()(mRequest).data
                elif item["api_name"] == "getcategory":
                    data = GetCategories.as_view()(mRequest).data
                elif item["api_name"] == "getheader":
                    data = GetHeader.as_view()(mRequest).data
                elif item["api_name"] == "getrecent":
                    q = ViewProduct.objects.filter(user=user).order_by("-visited")
                    serializedData = ViewProductSerilizer(q, many=True).data
                    productData = []
                    for i in serializedData:
                        productData.append(i["productobj"])
                    data = {"data": productData, "length": len(productData)}
                elif item["api_name"] == "suggestedCategory":
                    categoryId = getSuggestedCategory(
                        item["params"]["index"] - 1, user.id
                    )
                    if categoryId == -1:
                        continue
                    mRequest.GET = {
                        "categoryId": categoryId,
                        "sort-mostView": True,
                        "endIndex": item["params"]["endIndex"],
                    }
                    title = Category.objects.get(id=categoryId).title
                    data = GetProductsWithParam.as_view()(mRequest).data
                fetchedItems.append(
                    {
                        "contentType": item["contentType"],
                        "title": title,
                        "subtitle": subtitle,
                        "data": data,
                    }
                )
            return Response(fetchedItems)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


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
            else:
                view = ViewProduct.objects.filter(user=user, product=product).first()
                view.visited = datetime.datetime.now()
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
        user = self.request.user
        if "q" in self.request.GET:
            if SearchProduct.objects.filter(
                text=self.request.GET["q"], user=user
            ).exists():
                search = SearchProduct.objects.filter(
                    text=self.request.GET["q"], user=user
                ).first()
                search.searched = datetime.datetime.now()
                search.save()
            else:
                search = SearchProduct(text=self.request.GET["q"], user=user)
                search.save()

            queryset = Product.objects.filter(title__icontains=self.request.GET["q"])

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
        if "sort-mostDiscount" in self.request.GET:
            serialized_data = sorted(
                serialized_data, key=lambda row: row["discount_precent"], reverse=True
            )
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


class GetHeader(generics.ListAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    queryset = Header.objects.all()
    serializer_class = HeaderSerilizer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


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


class AllFavProduct(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        userfav = UserFavoriteProduct.objects.filter(user=request.user)
        products = []
        for row in userfav:
            products.append(row.product)

        return Response(
            ProductSerilizer(products, many=True, context={"request": request}).data
        )


class RemoveFavProduct(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            id = int(request.GET["productId"])
            del_product = Product.objects.get(id=id)
            UserFavoriteProduct.objects.filter(user=request.user).filter(
                product=del_product
            ).delete()
            userfav = UserFavoriteProduct.objects.filter(user=request.user)
            products = []
            for row in userfav:
                products.append(row.product)
            return Response(
                ProductSerilizer(products, many=True, context={"request": request}).data
            )
        except Exception as e:
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
                    comAct.save()
            return Response(status=status.HTTP_202_ACCEPTED)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class GetSelfComments(generics.ListAPIView):
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
        user = self.request.user
        queryset = queryset.filter(user=user)

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
            data = json.loads(request.body)
            productId = data["productId"]
            commentMess = data["comment"]
            isLike = data["liked"] == 1

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
                product=product, user=user, comment=commentMess, isLiked=isLike
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


class CanAddCommnet(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user

            productId = int(request.GET["productId"])

            product = Product.objects.get(id=productId)

            canAdd = (
                CommentProduct.objects.filter(product=product, user=user).count() == 0
            )

            data = {"canAdd": canAdd}
            return Response(data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class AddRate(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user

            productId = int(request.GET["productId"])

            product = Product.objects.get(id=productId)

            rate = int(request.GET["rate"])

            # if not SaleProduct.objects.filter(product=product, user=user).exists():
            #     return Response(
            #         "User does not buy this product!",
            #         status=status.HTTP_400_BAD_REQUEST,
            #     )

            if Rating.objects.filter(product=product, user=user).exists():
                rateobj = Rating.objects.filter(product=product, user=user).first()
                rateobj.rate = rate
                rateobj.save()
                return Response("Rate updated successfully.")

            else:
                rateobj = Rating(product=product, user=user, rate=rate)
                rateobj.save()

                return Response("Rated successfully.")
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class GetOwnRate(generics.ListAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user

            productId = int(request.GET["productId"])

            product = Product.objects.get(id=productId)
            rate = -1
            if Rating.objects.filter(product=product, user=user).exists():
                rate = Rating.objects.filter(product=product, user=user).first().rate

            data = {"rate": rate}
            return Response(data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class Search(generics.ListAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    queryset = Product.objects.all()
    serializer_class = ProductSerilizer3

    def get_queryset(self):
        queryset = super().get_queryset()
        try:
            q = self.request.GET["q"]
            queryset = queryset.filter(title__icontains=q)

            return queryset
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class GetHistSearch(generics.ListAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    queryset = SearchProduct.objects.all()
    serializer_class = SearchHistSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        try:
            user = self.request.user
            queryset = queryset.filter(user=user).order_by("-searched")[:20]
            return queryset
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class GetColors(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        colors = ProductColors.objects.values_list("color", flat=True).distinct()
        data = []
        print(list(colors))
        for color in colors:
            data.append({"color_value": color, "color_name": get_color_name(color)})
        return Response(data)


class RemoveFromCart(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user
            productId = int(request.GET["productId"])
            product = Product.objects.get(id=productId)
            cart = CurrentCartUser.objects.get_or_create(user=user)[0]

            if ProductCart.objects.filter(cart=cart, product=product).exists():
                ProductCart.objects.filter(cart=cart, product=product).first().delete()

            return Response(data=CurrentCartSerializer(cart).data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class AddToCart(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user
            productId = int(request.GET["productId"])
            product = Product.objects.get(id=productId)
            count = int(request.GET["count"])

            cart = CurrentCartUser.objects.get_or_create(user=user)[0]

            if ProductCart.objects.filter(cart=cart, product=product).exists():
                cart_item = ProductCart.objects.filter(
                    cart=cart, product=product
                ).first()
                if count == 0:
                    cart_item.delete()
                else:
                    cart_item.count = count
                    cart_item.save()

            else:
                if not count == 0:
                    cart_item = ProductCart(cart=cart, product=product, count=count)
                    cart_item.save()

            return Response(data=CurrentCartSerializer(cart).data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class GetCurrentCart(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user

            cart = CurrentCartUser.objects.filter(user=user).first()

            return Response(CurrentCartSerializer(cart).data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class AddAdress(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user
            address = request.GET["address"]
            postal_code = int(request.GET["postal_code"])
            phone = request.GET["phone"]
            state = request.GET["state"]
            city = request.GET["city"]
            if "id" in request.GET:
                try:
                    print("here")
                    addressModel = AddressUser.objects.get(
                        id=request.GET["id"], user=user
                    )
                except ObjectDoesNotExist:
                    raise Exception("Address does not exists!")
            else:
                addressModel = AddressUser(user=user)
            addressModel.address = address
            addressModel.phone = phone
            addressModel.postal_code = postal_code
            addressModel.state = state
            addressModel.city = city
            addressModel.save()
            allAddress = reversed(AddressUser.objects.filter(user=user))
            return Response(AddressUserSerializer(allAddress, many=True).data)

        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class RemoveAddress(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            print("2")
            user = request.user
            id = int(request.GET["id"])
            try:
                print(id)
                AddressUser.objects.get(id=id, user=user).delete()

            except ObjectDoesNotExist:
                raise Exception("Address does not exists!")
            allAddress = reversed(AddressUser.objects.filter(user=user))
            return Response(AddressUserSerializer(allAddress, many=True).data)
        except ProtectedError:
            allAddress = reversed(AddressUser.objects.filter(user=user))
            return Response(
                AddressUserSerializer(allAddress, many=True).data,
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class GetAllAddress(generics.ListAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    queryset = AddressUser.objects.all()
    serializer_class = AddressUserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = reversed(queryset.filter(user=user))

        return queryset


class GetCartPrice(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user
            addressId = request.GET["addressId"]

            address = AddressUser.objects.get(id=addressId)
            cart = CurrentCartUser.objects.get(user=user)

            postPrice = calculate_post_price(
                cart.productcart_set.all(), address.state, address.city
            )
            totalPrice = calculate_total_price(cart.productcart_set.all()) + postPrice

            return Response({"postPrice": postPrice, "totalPrice": totalPrice})
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class CloseCart(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user
            addressId = int(request.GET["addressId"])
            print("her")
            if not CurrentCartUser.objects.filter(user=user).exists():
                return Response(
                    "Cart does not exists!", status=status.HTTP_404_NOT_FOUND
                )

            address = AddressUser.objects.get(id=addressId)
            cart = CurrentCartUser.objects.filter(user=user).first()
            pCart = InProgressCart(user=user)
            pCart.address = address
            # postPrice = calculate_post_price(cart.productcart_set.all())
            # pCart.post_price = postPrice
            # pCart.totalPrice = (
            #     calculate_total_price(cart.productcart_set.all()) + postPrice
            # )

            pCart.save()

            product_carts = cart.productcart_set.all()

            for pr in product_carts:
                cart_item = IPProductCart(
                    cart=pCart,
                    product=pr.product,
                    count=pr.count,
                )
                cart_item.save()

            print("here")
            cart.delete()
            return Response(InProgressCartSerializer(pCart).data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class GetAllInProgressCart(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user

            cart = InProgressCart.objects.filter(user=user)

            return Response(InProgressCartSerializer(cart, many=True).data)

        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class GetIPCartPrice(APIView):
    permission_classes = [
        AllowAny,
    ]

    def get(self, request):
        try:
            IPCartId = request.GET["cart"]
            pCart = InProgressCart.objects.get(id=IPCartId)
            products = pCart.ipproductcart_set.all()
            postPrice = calculate_post_price(
                products, pCart.address.state, pCart.address
            )
            totalPrice = calculate_total_price(products) + postPrice
            data = {"postPrice": postPrice, "totalPrice": totalPrice}
            return Response(data)

            # pCart.post_price = postPrice
            # pCart.totalPrice = calculate_total_price(products) + postPrice

            # pCart.save()

            # for pr in products:
            #     pr.discount = pr.product.discount
            #     pr.unitPrice = pr.product.price
            #     pr.save()

            # return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class GetIPCart(generics.RetrieveAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = InProgressCart.objects.all()
    serializer_class = InProgressCartSerializer
    lookup_field = "id"


class GetPaidCart(generics.RetrieveAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = PaidCart.objects.all()
    serializer_class = PaidCartSerializer
    lookup_field = "id"


class GetMassages(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user

            messages = MessageModel.objects.filter(user=user).filter(active=True)

            data = MessageSerializer(messages, many=True).data
            return Response(data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class MarkAsReadMassages(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user
            id = int(request.GET["id"])
            message = MessageModel.objects.filter(user=user).filter(id=id).first()
            message.read = True
            message.save()
            messages = MessageModel.objects.filter(user=user).filter(active=True)
            data = MessageSerializer(messages, many=True).data
            return Response(data)
        except Exception as e:
            messages = MessageModel.objects.filter(user=user).filter(active=True)
            data = MessageSerializer(messages, many=True).data
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class DeleteMassages(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            user = request.user
            id = int(request.GET["id"])
            message = MessageModel.objects.filter(user=user).filter(id=id).first()
            message.active = False
            message.save()
            messages = MessageModel.objects.filter(user=user).filter(active=True)
            data = MessageSerializer(messages, many=True).data
            return Response(data)
        except Exception as e:
            messages = MessageModel.objects.filter(user=user).filter(active=True)
            data = MessageSerializer(messages, many=True).data
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class GetWaiting(generics.ListAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    queryset = InProgressCart.objects.all()
    serializer_class = InProgressCartSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user).order_by("-recorded_date")
        return queryset


class GetProc(generics.ListAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    queryset = PaidCart.objects.all()
    serializer_class = PaidCartSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = queryset.filter(user=user).filter(send=False).order_by("-paid_date")
        return queryset


class GetSent(generics.ListAPIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    queryset = PaidCart.objects.all()
    serializer_class = PaidCartSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = queryset.filter(user=user).filter(send=True).order_by("-send_date")
        return queryset


class DeleteInProgressCart(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            id = int(request.GET["id"])
            user = request.user
            InProgressCart.objects.filter(user=user).get(id=id).delete()
            return Response(status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class ReciveOrder(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            id = int(request.GET["id"])
            cart = PaidCart.objects.get(id=id)
            try:
                TrackOrderModel.objects.filter(cart=cart).delete()
            except:
                pass
            cart.recived_date = datetime.datetime.now().date()
            cart.save()

            return Response(PaidCartSerializer(cart).data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class TrackOrder(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        try:
            cartId = int(request.GET["id"])

            cart = PaidCart.objects.filter(user=request.user).get(id=cartId)

            TrackOrderModel.objects.get_or_create(cart=cart)

            return Response(status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            print(str(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
