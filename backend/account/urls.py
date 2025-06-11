from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"", UserRegistrationViewset, basename="register")
router.register(r"", LoginViewset, basename="login")
# router.register(r"verify", VerifyEmailViewSet, basename="verify")

urlpatterns = [
    path("", include(router.urls)),
    path('verify-email',VerifyEmailViewSet.as_view({'get':'verify'}),name='verify-email'),
    path('request-password-reset/',RequestPasswordResetEmail.as_view(),name='request-password-reset'),
    path('password-reset/',VerifyPasswordReset.as_view(),name='password-reset')
]
