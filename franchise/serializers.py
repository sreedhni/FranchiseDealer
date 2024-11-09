
# serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate
from Accounts.models import *

class FranchiseeLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if user is None or not user.is_franchisee:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            raise serializers.ValidationError("Email and password are required.")

        attrs['user'] = user
        return attrs

from rest_framework import serializers
from Accounts.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['transaction_id', 'amount_paid', 'payment_method', 'payment_date', 'payment_status']


from rest_framework import serializers
from Accounts.models import ServiceProvider

class ServiceProviderSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = ServiceProvider
        fields = '__all__'  # Specify fields explicitly if needed

    def get_full_name(self, obj):
        return obj.user.full_name if obj.user else None

from rest_framework import serializers
from Accounts.models import ServiceProvider, ServiceRegister, CustomerReview

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRegister
        fields = '__all__'  # Or specify fields explicitly if needed

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerReview
        fields = '__all__'  # Or specify fields explicitly if needed


from rest_framework import serializers
from Accounts.models import Dealer

class DealerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dealer
        fields = '__all__'  # Or specify individual fields if needed


#without file upload

# class ServiceRegisterSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ServiceRegister
#         fields = ['service_provider', 'description', 'gstcode', 'category', 'subcategory', 'accepted_terms']

#     def create(self, validated_data):
#         # You can perform any additional validation or processing here
#         return super().create(validated_data)

# with file upload
class ServiceRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRegister
        fields = ['service_provider', 'description', 'gstcode', 'category', 'subcategory', 'license', 'image', 'accepted_terms']

    def create(self, validated_data):
        # Set the status to 'Active' by default
        validated_data['status'] = 'Active'
        return super().create(validated_data)

# class ServiceProviderSerializer(serializers.ModelSerializer):
#     # Custom fields to get information from related models
#     full_name = serializers.SerializerMethodField()
#     email = serializers.EmailField(source='user.email', read_only=True)

#     total_service_providers = serializers.SerializerMethodField()
#     approved_count = serializers.SerializerMethodField()
#     pending_count = serializers.SerializerMethodField()

#     class Meta:
#         model = ServiceProvider
#         fields = '__all__'  # Or specify fields explicitly if needed

#     def get_full_name(self, obj):
#         return obj.user.full_name if obj.user else None

#     def get_total_service_providers(self, obj):
#         dealer = self.context.get('dealer')  # Access dealer from context
#         return ServiceProvider.objects.filter(dealer=dealer).count()

#     def get_approved_count(self, obj):
#         dealer = self.context.get('dealer')  # Access dealer from context
#         return ServiceProvider.objects.filter(dealer=dealer, verification_by_dealer='APPROVED').count()

#     def get_pending_count(self, obj):
#         dealer = self.context.get('dealer')  # Access dealer from context
#         return ServiceProvider.objects.filter(dealer=dealer, verification_by_dealer='PENDING').count()







# # without file
# class AddDealerSerializer(serializers.ModelSerializer):
#     # Fields for User model
#     email = serializers.EmailField(required=False)
#     phone_number = serializers.CharField(required=True)
#     full_name = serializers.CharField(required=True)
#     address = serializers.CharField(required=True)
#     pin_code = serializers.CharField(required=True)
#     district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all())
#     state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all())
    
#     # Fields for Dealer model
#     about = serializers.CharField(required=True)
#     profile_image = serializers.ImageField(required=False)
#     service_providers = serializers.IntegerField(required=False)
#     franchisee = serializers.PrimaryKeyRelatedField(queryset=Franchisee.objects.all())
#     verification_id = serializers.CharField(required=False)
#     verificationid_number = serializers.CharField(required=False)
#     id_copy = serializers.FileField(required=False)

#     class Meta:
#         model = Dealer
#         fields = ['email', 'phone_number', 'full_name', 'address', 'pin_code', 
#                  'district', 'state', 'about', 'profile_image', 'service_providers',
#                  'franchisee', 'verification_id', 'verificationid_number', 'id_copy']
        
# with file

class AddDealerSerializer(serializers.ModelSerializer):
    # Fields for User model
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=True)
    full_name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    landmark = serializers.CharField(required=True)
    pin_code = serializers.CharField(required=True)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all())
    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all())
    watsapp = serializers.CharField(required=True)
    country_code = serializers.PrimaryKeyRelatedField(queryset=Country_Codes.objects.all())

    # Fields for Dealer model
    about = serializers.CharField(required=True)
    profile_image = serializers.ImageField(required=False)
    service_providers = serializers.IntegerField(required=False)
    franchisee = serializers.PrimaryKeyRelatedField(queryset=Franchisee.objects.all())
    verification_id = serializers.CharField(required=False)
    verificationid_number = serializers.CharField(required=False)
    id_copy = serializers.FileField(required=False)

    class Meta:
        model = Dealer
        fields = [
            'email', 'phone_number', 'full_name', 'address', 'landmark', 'pin_code',
            'district', 'state', 'watsapp', 'country_code', 'about', 'profile_image',
            'service_providers', 'franchisee', 'verification_id', 'verificationid_number',
            'id_copy'
        ]

# #without file
# class AddServiceProviderSerializer(serializers.ModelSerializer):
#     # Fields for User model
#     email = serializers.EmailField(required=False)
#     phone_number = serializers.CharField(required=True)
#     full_name = serializers.CharField(required=True)
#     address = serializers.CharField(required=True)
#     pin_code = serializers.CharField(required=True)
#     district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all())
#     state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all())
    
#     # Fields for ServiceProvider model
#     about = serializers.CharField(required=False)
#     profile_image = serializers.ImageField(required=False)
#     date_of_birth = serializers.DateField(required=True)
#     gender = serializers.ChoiceField(choices=GENDER_CHOICES)
#     dealer = serializers.PrimaryKeyRelatedField(queryset=Dealer.objects.all())
#     franchisee = serializers.PrimaryKeyRelatedField(queryset=Franchisee.objects.all())
#     address_proof_document = serializers.CharField(required=False)
#     id_number = serializers.CharField(required=False)
#     address_proof_file = serializers.FileField(required=False)
#     payout_required = serializers.ChoiceField(choices=ServiceProvider.PAYOUT_FREQUENCY_CHOICES)

#     class Meta:
#         model = ServiceProvider
#         fields = ['email', 'phone_number', 'full_name', 'address', 'pin_code', 
#                  'district', 'state', 'about', 'profile_image', 'date_of_birth',
#                  'gender', 'dealer', 'franchisee', 'address_proof_document',
#                  'id_number', 'address_proof_file', 'payout_required']

class AddServiceProviderSerializer(serializers.ModelSerializer):
    # Fields for User model
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=True)
    full_name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    landmark = serializers.CharField(required=True)
    pin_code = serializers.CharField(required=True)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all())
    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all())
    watsapp = serializers.CharField(required=True)
    country_code = serializers.PrimaryKeyRelatedField(queryset=Country_Codes.objects.all())

    # Fields for ServiceProvider model
    about = serializers.CharField(required=False)
    profile_image = serializers.ImageField(required=False)
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.ChoiceField(choices=GENDER_CHOICES)
    dealer = serializers.PrimaryKeyRelatedField(queryset=Dealer.objects.all())
    franchisee = serializers.PrimaryKeyRelatedField(queryset=Franchisee.objects.all())
    address_proof_document = serializers.CharField(required=False)
    id_number = serializers.CharField(required=False)
    address_proof_file = serializers.FileField(required=False)
    payout_required = serializers.ChoiceField(choices=ServiceProvider.PAYOUT_FREQUENCY_CHOICES)
    accepted_terms = serializers.BooleanField(required=True)

    class Meta:
        model = ServiceProvider
        fields = ['email', 'phone_number', 'full_name', 'address', 'landmark', 'pin_code',
                 'district', 'state', 'watsapp', 'country_code', 'about', 'profile_image',
                 'date_of_birth', 'gender', 'dealer', 'franchisee', 'address_proof_document',
                 'id_number', 'address_proof_file', 'payout_required', 'accepted_terms']


# counts of complaints
from rest_framework import serializers

class FranchiseComplaintsCountSerializer(serializers.Serializer):
    total_complaints = serializers.IntegerField()
    percentage_change = serializers.FloatField()
    trend = serializers.CharField()

from rest_framework import serializers

class FranchiseAdsCountSerializer(serializers.Serializer):
    total_ads = serializers.IntegerField()
    percentage_change = serializers.FloatField()
    trend = serializers.CharField()
    active_ads = serializers.IntegerField()
    service_provider_count = serializers.IntegerField()


from rest_framework import serializers
from Accounts.models import ServiceProvider, Invoice, Franchisee

class FranchiseearningServiceProviderSerializer(serializers.ModelSerializer):
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
    

from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from Accounts.models import Dealer, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'address', 'landmark', 
                 'pin_code', 'watsapp', 'country_code', 'district', 'state']


class DealerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Dealer
        fields = [
            'id', 'custom_id', 'user', 'about', 'profile_image', 
            'service_providers', 'franchisee', 'status', 
            'verification_id', 'verificationid_number', 
            'id_copy', 'craeted_date'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Convert image URLs to absolute URLs if they exist
        request = self.context.get('request')
        if request and instance.profile_image:
            data['profile_image'] = request.build_absolute_uri(instance.profile_image.url)
        if request and instance.id_copy:
            data['id_copy'] = request.build_absolute_uri(instance.id_copy.url)
        return data


class CustomIDRequestSerializer(serializers.Serializer):
    custom_id = serializers.CharField(required=True)


from rest_framework import serializers
from Accounts.models import Country_Codes, State, District

class CountryCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country_Codes
        fields = ['id', 'country_name', 'calling_code']

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name']

class DistrictSerializer(serializers.ModelSerializer):
    state = StateSerializer()

    class Meta:
        model = District
        fields = ['id', 'name', 'state']


from rest_framework import serializers
from Accounts.models import Category, Subcategory

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'description', 'status']

class SubcategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    service_type = serializers.StringRelatedField()
    collar = serializers.StringRelatedField()

    class Meta:
        model = Subcategory
        fields = ['id', 'title', 'image', 'description', 'service_type', 'collar', 'status', 'category']