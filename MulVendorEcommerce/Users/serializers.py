from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Customer, Vendor, AdminProfile, VendorEmployee, Address
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'is_verified': self.user.is_verified
        }
        return data

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone_number', 'role', 'is_verified', 'password']
        read_only_fields = ['is_verified']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }

    def validate_email(self, value):
        if self.instance and User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_username(self, value):
        if self.instance and User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number'),
            role=validated_data.get('role', 'CUSTOMER')
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)

    class Meta:
        model = Customer
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save(role='CUSTOMER')
        customer = Customer.objects.create(user=user, **validated_data)
        return customer

class VendorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['is_approved', 'store_rating']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            if request.user.role != 'VENDOR':
                request.user.role = 'VENDOR'
                request.user.save()
            return super().create(validated_data)
        raise serializers.ValidationError("Authentication required")

class AdminProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='ADMIN'),
        required=False
    )

    class Meta:
        model = AdminProfile
        fields = '__all__'

    def validate_user(self, value):
        if value.role != 'ADMIN':
            raise serializers.ValidationError("User must have ADMIN role")
        return value

class VendorEmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        required=False
    )

    class Meta:
        model = VendorEmployee
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.role == 'VENDOR':
            validated_data['vendor'] = request.user.vendor
        return super().create(validated_data)

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['user']

    def validate(self, attrs):
        if attrs.get('is_default') and not (attrs.get('street') and attrs.get('city')):
            raise serializers.ValidationError("Default address must have street and city")
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            if validated_data.get('is_default'):
                Address.objects.filter(user=request.user).update(is_default=False)
            return super().create(validated_data)
        raise serializers.ValidationError("Authentication required")