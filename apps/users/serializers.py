from rest_framework import serializers
from .models import *

class UserSerializer(serializers.Serializer):
    first_name=serializers.CharField()
    last_name=serializers.CharField()

class UserModalSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        # fields="__all__" ## if all fields are you want
        required_fields=["first_name"]
        extra_kwargs={
            "last_name":{
                "required":True
            }
        }
        exclude =[
            "password"
        ]

    def validate_username(self,value):
        if " " in value:
            raise serializers.ValidationError(
                "username connot contain space"
            )
        return value


    def validate(self,attrs):
        if attrs["username"]==attrs["email"]:
            raise serializers.ValidationError(
                "username and email should not be equal"
            )
        return attrs


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Organization
        fields=[
            "id",
            "name",
            "slug",
            "is_active",
            "created_at",
            "updated_at"
        ]
        read_only_fields=[
            "id",
            "created_at",
            "updated_at"
        ]

    def validate_name(self,value):
        if not value.strip():
            raise serializers.ValidationError(
                "Organization name cannot be empty"
            )
        return value
