from django.shortcuts import render
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status, views, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.validators import ValidationError
from rest_framework.decorators import action
from django.utils.translation import gettext_lazy as _
from .serializer import *
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import Util, user_email, generate_six_digit_code, send_reset_code
from datetime import datetime, timedelta
import jwt
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


User = get_user_model()


@method_decorator(csrf_exempt, name="dispatch")
class UserRegistrationViewset(viewsets.ViewSet):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def register(self, request):
        try:
            print("Received registration data:", request.data)

            first_name = request.data.get("first_name")
            last_name = request.data.get("last_name")
            email = request.data.get("email", "").lower().strip()
            password = request.data.get("password", "").strip()
            confirm_password = request.data.get("confirm_password", "").strip()

            if not all([email, password, confirm_password, first_name, last_name]):
                return Response(
                    {"error": "All fields are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if User.objects.filter(email=email).exists():
                return Response(
                    {"error": "Email already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if password != confirm_password:
                return Response(
                    {"error": "Passwords do not match"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=False,
                is_verified=False,
            )
            user_email(request, user)
            return Response(
                {
                    "message": "Registration successful! Please check your email to verify your account.",
                    "email": user.email,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            print(f"Registration error: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def logout(self, request):
        logout(request)
        return Response(_("Logout Successful"), status=status.HTTP_200_OK)


class LoginViewset(viewsets.GenericViewSet):
    serializer_class = UserLoginSerializer

    @action(detail=False, methods=["post"])
    def login(self, request):
        try:
            data = request.data
            email = data.get("email", "").lower().strip()
            password = data.get("password", "")
            if not email or not password:
                return Response(
                    {"error": "Please provide both email and password"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                user = User.objects.get(email=email)
                from django.contrib.auth.hashers import check_password
                password_valid = check_password(password, user.password)
                auth_user1 = authenticate(request, username=email, password=password)
                auth_user2 = authenticate(request, email=email, password=password)
                if password_valid and not (auth_user1 or auth_user2):
                    login(request, user)
                    refresh = RefreshToken.for_user(user)
                    return Response(
                        {
                            "message": "Login successful",
                            "token": {
                                "access": str(refresh.access_token),
                                "refresh": str(refresh),
                            },
                        },
                        status=status.HTTP_200_OK,
                    )
            except User.DoesNotExist:
                print(f"No user found with email: {email}")
                return Response(
                    {"error": "Invalid email or password"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            user = authenticate(request, email=email, password=password)
            if not user:
                user = authenticate(request, username=email, password=password)
            if not user:
                return Response(
                    {"error": "Invalid email or password"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if not user.is_verified:
                return Response(
                    {"error": "Please verify your email before logging in"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if not user.is_active:
                return Response(
                    {"error": "Your account is not active"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            # Login successful
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Login successful",
                    "token": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    },
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(f"Login error: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def logout(self, request):
        logout(request)
        return Response({"Message": _("Logout Successful")}, status=status.HTTP_200_OK)
