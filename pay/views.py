from django.shortcuts import render, redirect, reverse
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.conf import settings
from api.models import InProgressCart, PaidCart, ProductPaidCart
import requests
import json
import random
from . import models


ZP_API_REQUEST = f"https://api.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = f"https://api.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = f"https://www.zarinpal.com/pg/StartPay/"

description = "پرداخت سبد خرید"

CallbackURL = "http://localhost:8000/pay/verify/"


def send_request(request):
    cartId = int(request.GET["cart"])
    # authoization = request.headers["Authoization"]
    resprice = requests.get(
        f"http://localhost:8000/api/get-ipcart-price/?cart={cartId}"
    )
    if not resprice.ok:
        return HttpResponseBadRequest("Unkowon error happend!")
    price = resprice.json()
    cart = InProgressCart.objects.get(id=cartId)
    amount = price["totalPrice"]

    data = {
        "merchant_id": settings.MERCHANT,
        "description": description,
        "amount": amount,
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

    if status == "OK":
        print(authority)
        aModel = models.AuthorityCart.objects.get(authority=authority)
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
            print("here2")

            cart = aModel.cart
            pCart = PaidCart(user=cart.user)
            pCart.recorded_date = cart.recorded_date
            pCart.address = cart.address
            pCart.ref_id = refid
            pCart.authority = authority
            pCart.amount = aModel.price
            pCart.save()
            print("here3")

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
            print("here4")

            # aModel.cart.
            return HttpResponse(
                redirect_template.render(
                    {
                        "status": "OK",
                        "refId": refid,
                        "code": code,
                        "paidcartId": pCart.id,
                    }
                )
            )
        else:
            return HttpResponse(
                redirect_template.render({"status": "NOK", "code": code})
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
        return HttpResponse(redirect_template.render({"status": "NOK", "refId": refid}))


def payCartView(requst):
    pay_template = loader.get_template("pay.html")
    print("sdaasd")
    context = {
        "data": {"amount": requst.GET["amount"], "authority": requst.GET["authority"]},
    }
    print("dsadsa")

    return HttpResponse(pay_template.render(context, requst))
