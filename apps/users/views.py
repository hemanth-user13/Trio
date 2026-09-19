from django.http import JsonResponse
from .serializers import *

# Create your views here.


def currentUserApi(request):
    obj={
        "first_name":"Rukmini",
        "password":"1123232",
        "last_name":"Mammu",
        "username":"Mammmu"
    }
    serializer=UserModalSerializer(data=obj)
    if serializer.is_valid():
        users=serializer.save()
        return JsonResponse({
        "message":"hello hemanth",
        "data":UserModalSerializer(users).data,
        "status":True
        })
    return JsonResponse({
        "message":"validation error",
        "error":serializer.errors,
        "status":False
    },status=400)


def getUserList(request):
    data=User.objects.all()
    serilazerdata=UserModalSerializer(data,many=True)
    return JsonResponse({
        "status":"Success",
        "data":serilazerdata.data
    })