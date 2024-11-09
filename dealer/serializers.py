# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from Accounts.models import *

# class DealerLoginSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)

#     def validate(self, attrs):
#         email = attrs.get('email')
#         password = attrs.get('password')

#         if email and password:
#             user = authenticate(request=self.context.get('request'), email=email, password=password)
#             if user is None or not user.is_dealer:
#                 raise serializers.ValidationError("Invalid email or password.")
#         else:
#             raise serializers.ValidationError("Email and password are required.")

#         attrs['user'] = user
#         return attrs



# Define the serializer for validating login
class DealerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if user is None or not user.is_dealer:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            raise serializers.ValidationError("Email and password are required.")

        attrs['user'] = user
        return attrs


# class ServiceProviderSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ServiceProvider
#         fields = '__all__'  # Or specify fields you want to include

from rest_framework import serializers
from Accounts.models import ServiceProvider, User  # Ensure you import User model

# class ServiceProviderSerializer(serializers.ModelSerializer):
#     full_name = serializers.SerializerMethodField()
#     email = serializers.EmailField(source='user.email', read_only=True)

#     class Meta:
#         model = ServiceProvider
#         fields = '__all__'  

#     def get_full_name(self, obj):
#         return obj.user.full_name if obj.user else None

class ServiceProviderSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    district = serializers.CharField(source='user.district.name', read_only=True)
    state = serializers.CharField(source='user.state.name', read_only=True)
    service_count = serializers.SerializerMethodField()
    active_services = serializers.SerializerMethodField()

    class Meta:
        model = ServiceProvider
        fields = [
            'id', 'custom_id', 'full_name', 'email', 'phone_number',
            'profile_image', 'district', 'state', 'status',
            'verification_by_dealer', 'created_date', 'service_count',
            'active_services', 'about'
        ]

    def get_full_name(self, obj):
        return obj.user.full_name if obj.user.full_name else ''

    def get_service_count(self, obj):
        return obj.services.count()

    def get_active_services(self, obj):
        return obj.services.filter(status='Active').count()
    
# normal_id
# class ServiceProviderPendingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ServiceProvider
#         fields = '__all__'  # or list specific fields

#     def update(self, instance, validated_data):
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         return instance

# custom_id
class ServiceProviderPendingSerializer(serializers.ModelSerializer):
    custom_id = serializers.CharField(read_only=False)

    class Meta:
        model = ServiceProvider
        fields = ['custom_id', 'verification_by_dealer']

    def update(self, instance, validated_data):
        instance.verification_by_dealer = validated_data.get('verification_by_dealer')
        instance.save()
        return instance

from rest_framework import serializers
from Accounts.models import ServiceProvider, ServiceRegister, CustomerReview

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRegister
        fields = '__all__'  # Or specify fields explicitly if needed


class PaymentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRequest
        fields = '__all__'
        read_only_fields = ['receiver', 'sernder']  # These are set in the view


class ServiceproviderSerializerSearch(serializers.ModelSerializer):
    # user = UserSerializer()

    name = serializers.CharField(source='user.full_name') 
    location=serializers.CharField(source='user.district')
    contact=serializers.IntegerField(source='user.phone_number')
    class Meta:
        model=ServiceProvider
        fields=['name','custom_id','verification_by_dealer','location','contact','status']


from Accounts.models import Franchisee, Franchise_Type

class FranchiseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Franchise_Type
        fields = ['name', 'details', 'amount', 'currency']  # Include the fields you want from Franchise_Type

class FranchiseSerializer(serializers.ModelSerializer):
    type = FranchiseTypeSerializer()  # Nest FranchiseTypeSerializer to get franchise type details

    class Meta:
        model = Franchisee
        fields = [
            'custom_id',
            'about',
            'profile_image',
            'revenue',
            'dealers',
            'service_providers',
            'type',  # Include the nested FranchiseTypeSerializer here
            'valid_from',
            'valid_up_to',
            'status',
            'verification_id',
            'verificationid_number',
            'community_name',
        ]



class DealerFranchiseeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Franchisee
        fields = [
            'custom_id', 'about', 'profile_image', 'revenue', 'dealers', 
            'service_providers', 'type', 'valid_from', 'valid_up_to', 
            'status', 'verification_id', 'verificationid_number', 
            'community_name', 'franchise_amount'
        ]


# Serializer for Ads model
class AdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ads
        fields = [
            'id', 'title', 'ad_type', 'amount', 
            'starting_date', 'ending_date', 'payment',
            'status', 'created'
        ]

# Enhanced ServiceSerializer to include basic stats
class ServiceSerializer(serializers.ModelSerializer):
    active_ads_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceRegister
        fields = [
            'id', 'description', 'gstcode', 'category',
            'subcategory', 'status', 'accepted_terms',
            'available_lead_balance', 'active_ads_count'
        ]

    def get_active_ads_count(self, obj):
        return obj.ads.filter(status='Active').count()
    

from rest_framework import serializers
from Accounts.models import *  # Adjust import based on your project structure


class DealerDashboardSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    address = serializers.CharField(source='user.address', read_only=True)
    custom_id = serializers.CharField(read_only=True)
    about = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    
    # Displaying franchisee data related to the dealer
    franchisee_name = serializers.CharField(source='franchisee.community_name', read_only=True)
    franchisee_location = serializers.CharField(source='franchisee.location', read_only=True)  # Add relevant fields
    franchisee_contact = serializers.CharField(source='franchisee.contact', read_only=True)  # Adjust to actual field names in franchisee model
    
    class Meta:
        model = Dealer
        fields = [
            'id',
            'custom_id',
            'full_name',
            'email',
            'phone_number',
            'address',
            'about',
            'status',
            'franchisee_name',
            'franchisee_location',  # Added field for franchisee location
            'franchisee_contact',    # Added field for franchisee contact
        ]


# class ServiceRegisterBasicSerializer(serializers.ModelSerializer):
#     service_name = serializers.CharField(source='service.name')  # Example of nested data access

#     class Meta:
#         model = ServiceRegister
#         fields = ['id', 'service_name', 'status', 'registered_on']  # Add fields as needed

# class AdsBasicSerializer(serializers.ModelSerializer):
#     service_provider_name = serializers.CharField(source='service_provider.user.full_name')

#     class Meta:
#         model = Ads
#         fields = ['id', 'title', 'service_provider_name', 'status', 'created']  # Add fields as needed


from rest_framework import serializers
from Accounts.models import ServiceProvider, ServiceRegister, Ads

class ServiceServiceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProvider
        fields = '__all__'

class ServiceServiceRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRegister
        fields = '__all__'

class ServiceAdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ads
        fields = '__all__'

from rest_framework import serializers
from .serializers import ServiceServiceRegisterSerializer, ServiceAdsSerializer
from Accounts.models import ServiceRegister, Ads

class RecentActivitySerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        if isinstance(instance, ServiceRegister):
            return ServiceServiceRegisterSerializer(instance).data
        elif isinstance(instance, Ads):
            return ServiceAdsSerializer(instance).data
        return super().to_representation(instance)

class DealerPaymentSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source='payment_date', format="%Y-%m-%d %H:%M")
    status = serializers.CharField(source='payment_status')
    description = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['transaction_id', 'date', 'description', 'amount_paid', 'status']

    def get_description(self, obj):
        # Check if invoice exists to avoid errors
        return f"Payment for Invoice #{obj.invoice.id}" if obj.invoice else "No associated invoice"


class DealerearningServiceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProvider
        fields = ['id', 'custom_id', 'about', 'profile_image', 'status']


class InvoiceSerializer(serializers.ModelSerializer):
    service_provider = serializers.StringRelatedField()
    commission = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'invoice_type', 'service_request',
            'sender', 'receiver', 'total_amount', 'payment_status',
            'commission', 'invoice_date'
        ]

    def get_commission(self, obj):
        return obj.total_amount * 0.04  # 4% commission