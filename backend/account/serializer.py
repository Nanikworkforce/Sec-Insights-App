from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from .models import ResetPassword

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password", "confirm_password"]

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(_("Passwords do not match"))
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        validated_data["username"] = validated_data["email"].split('@')[0]

        try:
            user = User.objects.create_user(**validated_data)
            return user
        except Exception as e:
            print("Error creating user:", str(e))
            raise



class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            email=data.get("email", ""), password=data.get("password", "")
        )
        if not user:
            raise serializers.ValidationError(_("Invalid email or password"))
        if not user.is_active:
            raise serializers.ValidationError(_("User account is disabled"))
        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_verified",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "is_verified"]

class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=1000)

    class Meta:
        model = User
        fields = ['token']

class RequestPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=10)

    class Meta:
        fields = ['email']

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=10)
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True,validators=[validate_password],required=True)

    class Meta:
        model = ResetPassword
        fields = ['email','code']