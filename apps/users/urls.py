from django.urls import path 
from . import views

urlpatterns = [
    path("me/",views.currentUserApi,name="sample_api"),
    path("userList/",views.getUserList,name="user_list")
]
