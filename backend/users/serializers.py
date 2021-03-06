from rest_framework import serializers
from users.models import Passport, Address


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passport
        fields = ("username", "email")


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
