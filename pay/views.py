from django.shortcuts import render, redirect, reverse
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import requests
import json


ZP_API_REQUEST = f"https://api.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = f"https://api.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = f"https://www.zarinpal.com/pg/StartPay/"

description = "پرداخت سبد خرید"

CallbackURL = "http://localhost:8000/pay/verify/"


def send_request(request):
    data = {
        "merchant_id": settings.MERCHANT,
        "amount": request.GET["amount"],
        "description": description,
        "phone": request.GET["phone"],
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
        return redirect("/pay/pay/?amount=" + request.GET["amount"])
    except requests.exceptions.Timeout:
        return redirect("/Timeout")
    except requests.exceptions.ConnectionError:
        return redirect("/ConnectionError")


def verify(request):
    status = request.GET["Status"]
    if status == "OK":
        redirect_template = loader.get_template("redirect.html")
        refid = 323425435532
        return HttpResponse(redirect_template.render({"status": "OK", "refId": refid}))

        # data = {
        #     "MerchantID": settings.MERCHANT,
        #     "mount": 1000,
        #     "authority": request.GET["Authority"],
        # }
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

    context = {
        "data": {"amount": requst.GET["amount"], "name": "Man"},
    }

    return HttpResponse(pay_template.render(context, requst))
