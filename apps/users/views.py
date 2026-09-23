from django.http import JsonResponse
from .serializers import *
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import APIView

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

@api_view(["GET","POST","DELETE"])
@permission_classes([AllowAny])
def UserActions(request,pk=None):
    if request.method=="GET":
        if pk is  None:
            try:
                users=User.objects.all()
                serializerdata=UserModalSerializer(users,many=True)
                return Response({
                    "message":"user list",
                    "data":serializerdata.data
                })
            except:
                return Response({
                    "message":"No Users Exists",
                    "data":[]
                })

    if request.method=="GET":
        if pk is not None:
            try:
                user=User.objects.get(id=pk)
            except User.DoesNotExist:
                return Response({
                    "message":"User doesn't exists",
                    "status":False
                },status=status.HTTP_404_NOT_FOUND)
            return Response({
                "message":"User found",
                "data":UserModalSerializer(user).data,
                "status":True
            },status=status.HTTP_200_OK)

    if request.method=="POST":
        try:
            data=UserModalSerializer(data=request.data)
            if data.is_valid():
                user=data.save()
                return Response({
                    "message":"User created Successfull",
                    "data":UserModalSerializer(user).data

                },status=200)
            return Response({
                "message":"there is an issue in creating the user",
                "status":False,
                "error":data.errors
            })
        except:
            return Response({
                "message":"There is an issue in creating an user",
                "error":data.errors
            },status=500)


    if request.method=="DELETE":
            if pk is None:
                return Response({
                    "message":"User id is required",
                    "status":False
                },status=status.HTTP_404_NOT_FOUND)
            try:
                userdata=User.objects.get(id=pk)
            except User.DoesNotExist:
                return Response({
                    "message":"User not found",
                    "error":False
                },status=status.HTTP_404_NOT_FOUND)
            userdata.delete()
            return Response({
                "message":"user Deleted successfully",
                "status":True
            },status=status.HTTP_200_OK)

    
            
class UserClassActions(APIView):
    permission_classes=[AllowAny]
    def get(self,request,user_id=None):
        if user_id is not None:
            try:
                user=User.objects.get(id=user_id)
                serilazeruser=UserModalSerializer(user)
            except User.DoesNotExist:
                return Response({
                    "message":"User doesn't exists",
                    "status":True
                })
            return Response({
                "message":"there is a user",
                "data":serilazeruser.data

            })
        user=User.objects.all()
        userlist=UserModalSerializer(user,many=True)
        return Response({
            "message":"user list",
            "data":userlist.data,
            "status":True
        })


from rest_framework import generics

class UserGenericView(generics.ListCreateAPIView):
    permission_classes=[AllowAny]
    serializer_class=UserModalSerializer

    def get_queryset(self):
        return User.objects.filter(is_active=True)



### organizations apis
class OrganizationListCreateView(generics.ListCreateAPIView):

    permission_classes=[AllowAny]

    queryset=Organization.objects.all()
    serializer_class=OrganizationSerializer


### organization detail api
class OrganizationDetailView(generics.RetrieveUpdateDestroyAPIView):

    permission_classes=[AllowAny]

    queryset=Organization.objects.all()
    serializer_class=OrganizationSerializer




### redis concept
from .redis_client import redis_client

class RedisTestApi(APIView):

    permission_classes=[AllowAny]

    def get(self,request):
        redis_client.set(
            "knowledgehub:test",
            "hello these is hemanth",
            ex=60
        )

        value=redis_client.get("knowledgehub:test")
        return Response({
            "status":"success",
            "data":value
        })



import json
from .redis_key import orgnaization_detail_key,ORGANIZATION_LIST_KEY


class RedisOrganization(APIView):

    permission_classes=[AllowAny]

    def get(self,request):
        #### check the redis first
        cached_data=redis_client.get("organization:list")

        if cached_data:
            data=json.loads(cached_data)
            return Response({
                "status":True,
                "data":data
            },status=status.HTTP_200_OK)

        organization=Organization.objects.all()
        print("hemanth")
        serializer=OrganizationSerializer(
            organization,
            many=True
        )

        redis_client.set(
            "organization:list",
            json.dumps(serializer.data),
            ex=60
        )

        return Response({
            "status":True,
            "data":serializer.data
        },status=status.HTTP_200_OK)

    def post(self,request):
        serializer=OrganizationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            redis_client.delete("organization:list")

            return Response({
                    "message":"organization created successfully!",
                    "data":serializer.data,
                    "status":True
                },status=status.HTTP_201_CREATED)
        return Response({
                    "message":"There is an issue in creating the organization",
                    "error":serializer.errors,
                    "status":False
                },status=status.HTTP_400_BAD_REQUEST)

    def patch(self,request,organization_id):
        try:
            organization=Organization.objects.get(id=organization_id)

        except Organization.DoesNotExist:
            return Response({
                "status":False,
                "message":"Organization not found"
            },status=status.HTTP_404_NOT_FOUND)

        serializer=OrganizationSerializer(
            organization,
            data=request.data,
            partial=True
        )       

        if not serializer.is_valid():
            return Response({
                "status":False,
                "errors":serializer.errors
            },status=status.HTTP_404_NOT_FOUND)

        serializer.save()

        redis_client.delete(
            orgnaization_detail_key(organization_id)
        )

        redis_client.delete(
            ORGANIZATION_LIST_KEY
        )

        return Response({
            "status":True,
            "message":"Organization updated successfully!",
            "data":serializer.data
        })
        
       
class RedisOrganizationDetail(APIView):

    permission_classes=[AllowAny]

    def get(self,request,organization_id):
        cache_key=orgnaization_detail_key(organization_id)

        cache_data=redis_client.get(
            cache_key
        )

        if cache_data:
            data=json.loads(cache_data)

            return Response({
                "status":True,
                "data":data
            })

        try:
            organization=Organization.objects.get(id=organization_id)

        except Organization.DoesNotExist:
            return Response({
                "status":False,
                "message":"Organization not found"

            },status=status.HTTP_404_NOT_FOUND)

        serializer=OrganizationSerializer(organization)

        data=serializer.data

        redis_client.set(
            cache_key,
            json.dumps(data),
            ex=300
        )

        return Response({
            "status":True,
            "data":data
        })


class OrganizationListApi(APIView):

    permission_classes=[AllowAny]

    def get(self,request):
        data=Organization.objects.raw(
            "SELECT * FROM users_organization"
        )
        serializer=OrganizationSerializer(data,many=True)

        return Response({
            "status":True,
            "data":serializer.data,
            "message":"hello "
        })


    