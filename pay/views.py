from django.shortcuts import render, redirect, reverse
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.conf import settings
from api.models import InProgressCart, PaidCart, ProductPaidCart
import requests
import json
import random
from . import models
from api.utils import *
import decimal


ZP_API_REQUEST = f"https://api.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = f"https://api.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = f"https://www.zarinpal.com/pg/StartPay/"

description = "پرداخت سبد خرید"


CallbackURL = settings.HOST_NAME + "/pay/verify/"


def send_request(request):
    cartId = int(request.GET["cart"])
    # authoization = request.headers["Authoization"]
    pCart = InProgressCart.objects.get(id=cartId)
    products = pCart.ipproductcart_set.all()
    amount = calculate_total_price(products) + calculate_post_price(
        products, pCart.address.state, pCart.address
    )
    data = {
        "merchant_id": settings.MERCHANT,
        "description": description,
        "amount": int(amount),
        "callback_url": CallbackURL,
    }

    data = json.dumps(data)
    # set content length by data
    h = {"content-type": "application/json", "content-length": str(len(data))}
    try:
        # response = requests.post(ZP_API_REQUEST, data=data, headers=h, timeout=10)
        # print(response)
        # if response.status_code == 200:
        #     response = response.json()
        #     print(response)
        #     if not len(response["data"]) == 0:
        #         return redirect(ZP_API_STARTPAY + str(response["data"]["authority"]))
        #     else:
        #         return redirect("/failed")

        # return redirect("/failed")

        # get authority and save it in db
        num = int(random.random() * 100000000000)
        authority = "A00000000000000000000000" + str(num)

        try:
            cart = InProgressCart.objects.get(id=cartId)
            aModel = models.AuthorityCart(authority=authority, cart=cart, price=amount)
            aModel.save()
            return redirect(
                "/pay/pay/?amount=" + str(amount) + "&authority=" + authority
            )
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    except requests.exceptions.Timeout:
        return redirect("/Timeout")
    except requests.exceptions.ConnectionError:
        return redirect("/ConnectionError")


def verify(request):
    status = request.GET["Status"]
    authority = request.GET["Authority"]

    aModel = models.AuthorityCart.objects.get(authority=authority)
    if status == "OK":
        redirect_template = loader.get_template("redirect.html")
        data = {
            "MerchantID": settings.MERCHANT,
            "amount": aModel.price,
            "authority": authority,
        }
        # Should verify data in api zarinpal

        # If ok to this
        refid = int(random.random() * 100000000)
        code = 100
        if code >= 100:
            cart = aModel.cart
            products = cart.ipproductcart_set.all()
            post_price = calculate_post_price(
                products, cart.address.state, cart.address
            )
            pCart = PaidCart(user=cart.user)
            pCart.recorded_date = cart.recorded_date
            pCart.address = cart.address.address
            pCart.ref_id = refid
            pCart.phone = cart.address.phone
            pCart.postal_code = cart.address.postal_code
            pCart.post_amount = post_price
            pCart.authority = authority
            pCart.total_amount = aModel.price
            pCart.save()

            products = cart.ipproductcart_set.all()
            productPaidCart = ProductPaidCart(
                cart=pCart,
            )
            for pr in products:
                productPaidCart.product = pr.product
                productPaidCart.count = pr.count
                productPaidCart.discount = pr.product.discount
                productPaidCart.unitPrice = pr.product.price
                productPaidCart.save()
            cart.delete()

            # aModel.cart.
            return HttpResponse(
                redirect_template.render(
                    {
                        "status": "OK",
                        "refId": refid,
                        "code": code,
                        "cart": pCart.id,
                    }
                )
            )
        else:
            return HttpResponse(
                redirect_template.render(
                    {
                        "status": "NOK",
                        "refId": 0,
                        "code": code,
                        "cart": aModel.cart.id,
                    }
                )
            )
        # data = json.dumps(data)
        # # set content length by data
        # h2 = {"content-type": "application/json", "content-length": str(len(data))}
        # response = requests.post(ZP_API_VERIFY, data=data, headers=h2)

        # if response.status_code == 200:
        #     response = response.json()
        #     if response["Status"] == 100:
        #         return {"status": True, "RefID": response["RefID"]}
        #     else:
        #         return {"status": False, "code": str(response["Status"])}
        # return response
    else:
        redirect_template = loader.get_template("redirect.html")
        refid = 0
        return HttpResponse(
            redirect_template.render(
                {
                    "status": "NOK",
                    "refId": 0,
                    "code": -5,
                    "cart": aModel.cart.id,
                }
            )
        )


def payCartView(requst):
    pay_template = loader.get_template("pay.html")
    context = {
        "data": {"amount": requst.GET["amount"], "authority": requst.GET["authority"]},
    }
    print("dsadsa")

    return HttpResponse(pay_template.render(context, requst))
