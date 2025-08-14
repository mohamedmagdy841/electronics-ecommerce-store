import random
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers

from cart.utils import merge_guest_cart
from .serializers import CustomUserCreateSerializer
from .models import PhoneOtp, User
from .utils import send_otp_via_sms

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiResponse,
)

COOKIE_NAME = "guest_id" 
COOKIE_SAMESITE = "Lax"

@extend_schema(
    tags=["Accounts"],
    summary="Login (username & password)",
    description=(
        "Authenticate a user and return a JWT access/refresh token pair. "
        "Also merges a guest cart into the user's cart and clears the guest cookie."
    ),
    auth=[],  # public endpoint
    request=inline_serializer(
        name="LoginRequest",
        fields={
            "username": serializers.CharField(),
            "password": serializers.CharField(write_only=True),
        },
    ),
    responses={
        200: inline_serializer(
            name="TokenPair",
            fields={
                "access": serializers.CharField(),
                "refresh": serializers.CharField(),
            },
        ),
        401: OpenApiResponse(description="Invalid credentials"),
    },
)


class CustomLoginView(APIView):
    throttle_scope = 'login'
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # merge guest cart into user cart
        merge_guest_cart(request, user, cookie_name=COOKIE_NAME)

        refresh = RefreshToken.for_user(user)
        resp = Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)

        # delete the guest cookie
        resp.delete_cookie(
            COOKIE_NAME,
            samesite=COOKIE_SAMESITE,
            path="/",
        )
        return resp
    
    
@extend_schema_view(
    post=extend_schema(
        tags=["Accounts"],
        summary="Register a new user",
        description="Create an account and return the created user.",
        auth=[],  # public endpoint
        responses={201: CustomUserCreateSerializer},
    )
)
class CustomRegisterView(generics.CreateAPIView):
    throttle_scope = 'register'
    queryset = User.objects.all()
    serializer_class = CustomUserCreateSerializer


@extend_schema(
    tags=["Accounts"],
    summary="Send OTP to phone",
    description="Generate and send a 6-digit OTP to the given phone number.",
    auth=[],  # public endpoint
    request=inline_serializer(
        name="SendOtpRequest",
        fields={
            "phone_number": serializers.CharField(),
        },
    ),
    responses={
        200: inline_serializer(
            name="SendOtpResponse",
            fields={"detail": serializers.CharField()},
        ),
        400: OpenApiResponse(description="Phone number missing or invalid"),
    },
)
class SendOtpView(APIView):
    throttle_scope = 'send_otp'
    def post(self, request):
        phone = request.data.get('phone_number')
        if not phone:
            return Response({'detail': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        otp = str(random.randint(100000, 999999))
        PhoneOtp.objects.update_or_create(phone_number=phone, defaults={'otp': otp, "is_verified": False})
        send_otp_via_sms(phone, otp)
        return Response({'detail': 'OTP sent successfully'}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Accounts"],
    summary="Verify OTP",
    description="Verify the previously sent OTP for a phone number.",
    auth=[],  # public endpoint
    request=inline_serializer(
        name="VerifyOtpRequest",
        fields={
            "phone_number": serializers.CharField(),
            "otp": serializers.CharField(),
        },
    ),
    responses={
        200: inline_serializer(
            name="VerifyOtpResponse",
            fields={"detail": serializers.CharField()},
        ),
        400: OpenApiResponse(description="OTP expired or invalid"),
        404: OpenApiResponse(description="Phone number not found"),
    },
)   
class VerifyOtpView(APIView):
    throttle_scope = 'verify_otp'
    def post(self, request):
        phone = request.data.get('phone_number')
        otp = request.data.get('otp')
        
        try:
            phone_otp = PhoneOtp.objects.get(phone_number=phone)
        except PhoneOtp.DoesNotExist:
            return Response({'detail': 'Invalid phone number'}, status=status.HTTP_404_NOT_FOUND)
        
        if phone_otp.is_expired():
            return Response({'detail': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        if phone_otp.otp != otp:
            return Response({'detail': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        phone_otp.is_verified = True
        phone_otp.save()
        return Response({'detail': 'OTP verified successfully'}, status=status.HTTP_200_OK)
