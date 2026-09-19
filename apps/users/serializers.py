from rest_framework import serializers
from .models import *

class UserSeralizers(serializers.Serializer):
    first_name=serializers.CharField()
    last_name=serializers.CharField()
