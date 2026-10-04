from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
# Create your views here.


def api_response(status_text,code,message,data=None,https_status=status.HTTP_200_OK):
    body={"status":status_text,"code":code,"message":message}
    if data is not None:
        body["data"]=data
    return Response(
        body,status=https_status
    )


class PublicApiView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]
    throttle_classes=[ScopedRateThrottle]