from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, UserRegistrationSerializer, 
    CustomTokenObtainPairSerializer, AdminUserCreateSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from .models import PasswordResetToken
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['role', 'is_verified', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'email', 'role']
    
    def get_queryset(self):
        if self.request.user.is_admin():
            return User.objects.all().order_by('-date_joined')
        return User.objects.filter(id=self.request.user.id)

class UserDetailView(generics.RetrieveUpdateAPIView):
    """Admin can view and update any user"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_admin():
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetRequestSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Invalidate existing tokens
                PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
                
                # Create new token
                token = PasswordResetToken.objects.create(
                    user=user,
                    expires_at=timezone.now() + timedelta(hours=24)
                )
                
                # In a real app, send email here
                # send_password_reset_email(user, token.token)
                print(f"Password reset token for {user.email}: {token.token}")
                
            except User.DoesNotExist:
                # Silently fail to prevent email enumeration
                pass
                
            return Response({"detail": "Password reset email sent if account exists."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                reset_token = serializer.validated_data['reset_token']
                user = reset_token.user
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                reset_token.used = True
                reset_token.save()
                return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
            except KeyError:
                 # Should be caught by serializer valid check but safety net
                 return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminUserCreateView(generics.CreateAPIView):
    """
    Super Admin can create new users (including admins)
    """
    queryset = User.objects.all()
    serializer_class = AdminUserCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Only Super Admin can create users via this endpoint
        if not request.user.is_super_admin():
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().create(request, *args, **kwargs)
