from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class VendorLocationHelper(viewsets.ViewSet):
    """
    ViewSet for vendor location operations
    """
    
    @action(detail=False, methods=['get'])
    def get_vendors_within_radius(self, request):
        """
        Get vendors within a specified radius using latitude/longitude
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 50))  # Default 50km
        
        if not lat or not lng:
            return Response(
                {'error': 'Latitude and longitude parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vendors = VendorProfile.objects.filter(
                latitude__isnull=False,
                longitude__isnull=False,
                is_active=True,
                verification_status=VendorProfile.VerificationStatus.VERIFIED
            )
            
            nearby_vendors = []
            for vendor in vendors:
                distance = haversine_distance(
                    float(lat),
                    float(lng),
                    float(vendor.latitude),
                    float(vendor.longitude)
                )
                if distance <= radius:
                    vendor.distance = distance
                    nearby_vendors.append(vendor)
            
            sorted_vendors = sorted(nearby_vendors, key=lambda x: x.distance)
            serializer = VendorProfileSerializer(sorted_vendors, many=True)
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {'error': 'Invalid latitude, longitude or radius values'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def get_vendor_coordinates(self, request, pk=None):
        """
        Get coordinates for a specific vendor
        """
        try:
            vendor = VendorProfile.objects.get(id=pk)
            return Response({
                'latitude': vendor.latitude,
                'longitude': vendor.longitude
            })
        except VendorProfile.DoesNotExist:
            return Response(
                {'error': 'Vendor not found'},
                status=status.HTTP_404_NOT_FOUND
            )