from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from .models import VendorProfile
from .serializers import VendorProfileSerializer, VendorVerificationSerializer
from .permissions import IsVendorOwner, IsAdmin

class VendorProfileCreateView(generics.CreateAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        self.request.user.role = 'vendor'
        self.request.user.save()

class VendorProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = VendorProfile.objects.all()
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendorOwner]

class VendorListView(generics.ListAPIView):
    queryset = VendorProfile.objects.filter(status='approved')
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['status']
    search_fields = ['business_name', 'business_description']

class VendorPublicDetailView(generics.RetrieveAPIView):
    """Public vendor storefront - anyone can view approved vendors"""
    queryset = VendorProfile.objects.filter(status='approved')
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.AllowAny]

class VendorManagementView(generics.ListAPIView):
    queryset = VendorProfile.objects.all()
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['status']

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdmin])
def verify_vendor(request, pk):
    try:
        vendor = VendorProfile.objects.get(pk=pk)
        serializer = VendorVerificationSerializer(vendor, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save(verified_by=request.user, verified_at=timezone.now())
            
            if serializer.validated_data.get('status') == 'approved':
                vendor.user.is_verified = True
                vendor.user.save()
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)
