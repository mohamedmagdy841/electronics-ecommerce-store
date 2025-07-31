import random
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CustomUserCreateSerializer
from .models import PhoneOtp, User
from .utils import send_otp_via_sms

class CustomLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })
            
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
class CustomRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserCreateSerializer

class SendOtpView(APIView):
    def post(self, request):
        phone = request.data.get('phone_number')
        if not phone:
            return Response({'detail': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        otp = str(random.randint(100000, 999999))
        PhoneOtp.objects.update_or_create(phone_number=phone, defaults={'otp': otp, "is_verified": False})
        send_otp_via_sms(phone, otp)
        return Response({'detail': 'OTP sent successfully'}, status=status.HTTP_200_OK)
    
class VerifyOtpView(APIView):
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
