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

class VerifyEmailViewSet(viewsets.GenericViewSet):
    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'token',
                openapi.IN_QUERY,
                description="JWT token for email verification",
                type=openapi.TYPE_STRING
            )
        ]
    )
    @action(methods=['get'], detail=False)
    def verify(self, request):
        token = request.GET.get('token')

        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            email_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=email_token['user_id'])

            if not user.is_verified:
                user.is_verified = True
                user.save()

            return Response({'email': 'User is successfully activated'}, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            return Response({'error': 'Email activation link has expired'}, status=status.HTTP_400_BAD_REQUEST)

        except jwt.DecodeError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def generate_token(user):
        expiration = datetime.utcnow() + timedelta(hours=24)
        payload = {
            'user_id': user.id,
            'exp': expiration,
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return token

class RequestPasswordResetEmail(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Invalid input'}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get('email')

        # Always respond the same way to prevent email enumeration
        try:
            user = User.objects.get(email=email)
            code = generate_six_digit_code()
            ResetPassword.objects.create(user=user, code=code)
            send_reset_code(user, code)
        except User.DoesNotExist:
            pass

        return Response({'message': 'If your email is registered, a reset code has been sent.'}, status=status.HTTP_200_OK)


class VerifyPasswordReset(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email or code.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reset_code = ResetPassword.objects.get(user=user, code=code)
        except ResetPassword.DoesNotExist:
            return Response({'error': 'Invalid email or code.'}, status=status.HTTP_400_BAD_REQUEST)

        if not reset_code.is_valid():
            return Response({'error': 'Reset code has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        reset_code.delete()

        return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)