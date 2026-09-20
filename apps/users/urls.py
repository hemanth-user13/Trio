from django.urls import path 
from . import views
from .views import *

urlpatterns = [
    path("me/",views.currentUserApi,name="sample_api"),
    path("userList/",views.UserActions,name="user_list"),
    path("userList/<int:user_id>/",views.UserActions,name="show_user"),
    path("list/",UserClassActions.as_view(),name="class_user")
]
