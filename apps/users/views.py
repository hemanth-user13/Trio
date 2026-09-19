from django.shortcuts import render
from django.http import JsonResponse
from .serializers import *

# Create your views here.
def currentUserApi(request):
    data=UserSeralizers(request.data)
    return JsonResponse({
        "message":"hello hemanth",
        "data":data,
        "status":True
    })