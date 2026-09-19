from django.http import JsonResponse
from .serializers import *

from rest_framework.decorators import api_view

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

@api_view(["GET","POST"])
def UserActions(request,user_id=None):
    if request.method=="GET":
        if user_id is  None:
            try:
                users=User.objects.all()
                serializerdata=UserModalSerializer(users,many=True)
                return JsonResponse({
                    "message":"user list",
                    "data":serializerdata.data
                })
            except:
                return JsonResponse({
                    "message":"No Users Exists",
                    "data":[]
                })

    if request.method=="POST":
        try:
            data=UserModalSerializer(data=request.data)
            if data.is_valid():
                return JsonResponse({
                    "message":"User created Successfull"

                },status=200)
            data.save()
        except:
            return JsonResponse({
                "message":"There is an issue in creating an user",
                "error":data.errors
            },status=500)

