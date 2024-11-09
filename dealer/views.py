from django.shortcuts import render
from Accounts.models import *  # Ensure you import your models
from rest_framework_simplejwt.authentication import JWTAuthentication


# Create your views here.

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import DealerLoginSerializer

# class DealerLoginView(generics.GenericAPIView):
#     serializer_class = DealerLoginSerializer

#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']

#         # Generate a token for the authenticated user
#         token, created = Token.objects.get_or_create(user=user)

#         return Response({
#             'message': 'Login successful',
#             'token': token.key,  # Include the token in the response
#             'user_id': user.id,
#             'email': user.email,
#             'full_name': user.full_name,
#             'is_dealer': user.is_dealer,
#         }, status=status.HTTP_200_OK)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import update_last_login


# Define the login view for dealers
class DealerLoginView(APIView):
    def post(self, request):
        serializer = DealerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if user.is_dealer:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            update_last_login(None, user)  # Update last login timestamp

            return Response({
                'refresh': str(refresh),              # Refresh token
                'access': str(refresh.access_token),  # Access token
                'user_id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'is_dealer': user.is_dealer,
            }, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'User is not a dealer.'}, status=status.HTTP_403_FORBIDDEN)

# from django.shortcuts import get_object_or_404
# from rest_framework import generics
# from rest_framework.authentication import TokenAuthentication
# from rest_framework.permissions import IsAuthenticated
# from .serializers import ServiceProviderSerializer

# from django.shortcuts import get_object_or_404

# class DealerServiceProviderListView(generics.ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = ServiceProviderSerializer

#     def get_queryset(self):
#         user = self.request.user  # This is a User instance
#         print(f"User: {user}, Type: {type(user)}, Is Dealer: {user.is_dealer}")  # Added Is Dealer check
#         dealer = get_object_or_404(Dealer, user=user)
#         print(f"Dealer: {dealer}, Type: {type(dealer)}")  # Print dealer details

#         return ServiceProvider.objects.filter(dealer=dealer)


#dealer homapage

from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# views.py
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

# class DealerDashboardView(APIView):
#     """View to get dealer's basic information and counts"""
    
#     def get(self, request):
#         try:
#             dealer = Dealer.objects.get(user=request.user)
#             dealer_data = DealerDashboardSerializer(dealer).data
            
#             # Add recent service providers summary
#             recent_providers_count = ServiceProvider.objects.filter(
#                 dealer=dealer,
#                 created_date__gte=timezone.now() - timedelta(days=30)
#             ).count()
            
#             # Add recent services summary
#             recent_services_count = ServiceRegister.objects.filter(
#                 service_provider__dealer=dealer,
#                 id__gte=timezone.now() - timedelta(days=30)
#             ).count()
            
#             # Add recent ads summary
#             recent_ads_count = Ads.objects.filter(
#                 service_provider__dealer=dealer,
#                 created__gte=timezone.now() - timedelta(days=30)
#             ).count()
            
#             response_data = {
#                 'dealer': dealer_data,
#                 'recent_summary': {
#                     'new_service_providers': recent_providers_count,
#                     'new_services': recent_services_count,
#                     'new_ads': recent_ads_count
#                 }
#             }
            
#             return Response(response_data, status=status.HTTP_200_OK)
            
#         except Dealer.DoesNotExist:
#             return Response(
#                 {'error': 'Dealer not found'}, 
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             return Response(
#                 {'error': str(e)}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404

class DealerDashboardServiceProviderCountsView(APIView):
    authentication_classes = [JWTAuthentication]  # Use JWT for access and refresh tokens
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        dealer = get_object_or_404(Dealer, user=user)

        # Get current date and calculate the start and end of the previous and current months
        today = timezone.now().date()
        first_day_of_current_month = today.replace(day=1)
        first_day_of_previous_month = (first_day_of_current_month - timedelta(days=1)).replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)

        # Approved counts for the current and previous months
        approved_count_current_month = ServiceProvider.objects.filter(
            dealer=dealer,
            verification_by_dealer='APPROVED',
            created_date__gte=first_day_of_current_month,
            created_date__lte=today
        ).count()

        approved_count_previous_month = ServiceProvider.objects.filter(
            dealer=dealer,
            verification_by_dealer='APPROVED',
            created_date__gte=first_day_of_previous_month,
            created_date__lte=last_day_of_previous_month
        ).count()

        # Calculate percentage change
        if approved_count_previous_month == 0:
            percentage_change = 0  # Avoid division by zero
        else:
            percentage_change = ((approved_count_current_month - approved_count_previous_month) / approved_count_previous_month) * 100

        # All-time approved count
        total_approved_count = ServiceProvider.objects.filter(dealer=dealer, verification_by_dealer='APPROVED').count()

        # Current pending requests
        pending_count = ServiceProvider.objects.filter(dealer=dealer, verification_by_dealer='PENDING').count()

        data = {
            "approved_count_current_month": approved_count_current_month,
            "percentage_change": percentage_change,
            "total_approved_count": total_approved_count,
            "pending_count": pending_count
        }

        return Response(data)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

class DealerServiceRegisterCountsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_service_register_data(self, dealer):
        # Define the start and end dates for current and previous month
        now = timezone.now()
        start_of_current_month = now.replace(day=1)
        start_of_previous_month = (start_of_current_month - timedelta(days=1)).replace(day=1)
        end_of_previous_month = start_of_current_month - timedelta(days=1)

        # Filter ServiceRegister entries under the dealer's service providers
        service_registers = ServiceRegister.objects.filter(service_provider__dealer=dealer)

        # Calculate current month and previous month counts
        current_month_count = service_registers.filter(
            service_provider__created_date__gte=start_of_current_month
        ).count()
        
        previous_month_count = service_registers.filter(
            service_provider__created_date__range=(start_of_previous_month, end_of_previous_month)
        ).count()

        # Calculate percentage change
        if previous_month_count > 0:
            percentage_change = ((current_month_count - previous_month_count) / previous_month_count) * 100
        else:
            percentage_change = 100 if current_month_count > 0 else 0

        # Total count of all-time service registrations under the dealer
        total_count = service_registers.count()

        return {
            "total_count": total_count,
            "percentage_change": round(percentage_change, 2)
        }

    def get(self, request):
        user = request.user
        dealer = get_object_or_404(Dealer, user=user)  # Get the dealer associated with the logged-in user

        # Fetch total count and percentage change data
        service_register_data = self.get_service_register_data(dealer)

        return Response(service_register_data)

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, F
from django.utils import timezone
from django.db.models import DecimalField
from datetime import timedelta
from Accounts.models import ServiceProvider, Invoice  # Adjust based on your actual model import
from .serializers import DealerearningServiceProviderSerializer, InvoiceSerializer  # Adjust serializer import

class DealerEarningsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure 'request.user' is the logged-in user
        dealer = Dealer.objects.get(user=request.user)  # Fetch the Dealer instance

        # Retrieve service providers related to the dealer
        service_providers = ServiceProvider.objects.filter(dealer=dealer)

        # Proceed with the rest of the logic as before
        service_providers_data = DealerearningServiceProviderSerializer(service_providers, many=True).data
        now = timezone.now()

        # Retrieve related invoices for the dealer's service providers
        invoices = Invoice.objects.filter(
            service_request__in=[sp.id for sp in service_providers],
            payment_status='paid'
        )
        invoices_data = InvoiceSerializer(invoices, many=True).data

        # Calculate commission earnings (4% of each transaction)
        total_commission = invoices.aggregate(
            total_earnings=Sum(F('total_amount') * 0.04, output_field=DecimalField())
        )['total_earnings'] or 0

        # Monthly earnings comparison logic
        current_month_start = now.replace(day=1)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        current_month_earnings = invoices.filter(
            invoice_date__gte=current_month_start
        ).aggregate(total=Sum(F('total_amount') * 0.04, output_field=DecimalField()))['total'] or 0

        previous_month_earnings = invoices.filter(
            invoice_date__gte=previous_month_start,
            invoice_date__lt=current_month_start
        ).aggregate(total=Sum(F('total_amount') * 0.04, output_field=DecimalField()))['total'] or 0

        # Calculate percentage change
        if previous_month_earnings > 0:
            earnings_change_percentage = ((current_month_earnings - previous_month_earnings) / previous_month_earnings) * 100
        else:
            earnings_change_percentage = None  # No previous month earnings to compare

        # Calculate all-time commission earnings
        all_time_commission = total_commission

        return Response({
            # "service_providers": service_providers_data,
            "invoices": invoices_data,
            "current_month_earnings": current_month_earnings,
            "previous_month_earnings": previous_month_earnings,
            "earnings_change_percentage": earnings_change_percentage,
            "all_time_commission": all_time_commission
        })


from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import DealerDashboardSerializer

class DealerDashboardView(APIView):
    """View to get dealer's basic information and franchisee details"""

    def get(self, request):
        try:
            # Get dealer instance with related user and franchisee
            dealer = Dealer.objects.select_related('user', 'franchisee').get(
                user=request.user,
                user__is_dealer=True  # Additional check to ensure user is a dealer
            )
            
            # Serialize dealer data, including franchisee details
            dealer_data = DealerDashboardSerializer(dealer).data
            
            response_data = {
                'dealer': dealer_data,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Dealer.DoesNotExist:
            return Response(
                {'error': 'Dealer not found for this user'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Error in DealerDashboardView: {str(e)}")  # Debugging
            return Response(
                {'error': 'An unexpected error occurred'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from rest_framework import viewsets  # Make sure this line is present
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

class FranchiseDetailsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request):
        user = request.user

        if not user.is_dealer:
            return Response({'detail': 'User is not a dealer.'}, status=status.HTTP_403_FORBIDDEN)

        dealer = user.dealer.first()
        if not dealer:
            return Response({'detail': 'Dealer not found.'}, status=status.HTTP_404_NOT_FOUND)

        franchisee = dealer.franchisee
        remaining_days = (franchisee.valid_up_to - timezone.now()).days

        franchise_details = {
            'franchise_name': franchisee.community_name,
            'location': user.address,  # Assuming location is the user's address
            'valid_up_to': franchisee.valid_up_to,
            'remaining_days': max(remaining_days, 0),
            'phone_number': franchisee.user.phone_number,
            'email': franchisee.user.email,
        }

        return Response(franchise_details, status=status.HTTP_200_OK)
    
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from Accounts.models import ServiceProvider, ServiceRegister, Ads
from .serializers import RecentActivitySerializer

class RecentActivitiesPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'
    max_page_size = 100

class RecentActivitiesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = RecentActivitiesPagination
    serializer_class = RecentActivitySerializer

    def get_queryset(self):
        dealer = self.request.user.dealer.first()
        service_providers = ServiceProvider.objects.filter(dealer=dealer)

        service_registers = ServiceRegister.objects.filter(service_provider__in=service_providers)
        ads = Ads.objects.filter(service_provider__in=service_providers)

        combined_queryset = sorted(
            list(service_registers) + list(ads),
            key=lambda x: x.created,
            reverse=True
        )
        return combined_queryset


# class DealerRecentActivitiesView(ListAPIView):
#     """View to list recent activities (services and ads) with pagination"""
#     pagination_class = StandardResultsSetPagination
    
#     def get_queryset(self):
#         dealer = Dealer.objects.get(user=self.request.user)
        
#         # Get recent services
#         recent_services = ServiceRegister.objects.filter(
#             service_provider__dealer=dealer
#         ).order_by('-id')
        
#         # Get recent ads
#         recent_ads = Ads.objects.filter(
#             service_provider__dealer=dealer
#         ).order_by('-created')
        
#         return recent_services, recent_ads
    
#     def list(self, request, *args, **kwargs):
#         try:
#             dealer = Dealer.objects.get(user=request.user)
            
#             # Get both querysets
#             recent_services, recent_ads = self.get_queryset()
            
#             # Create activities list
#             activities = []
            
#             # Add services to activities
#             for service in recent_services:
#                 activities.append({
#                     'type': 'service_registration',
#                     'data': ServiceRegisterBasicSerializer(service).data,
#                     'timestamp': service.id.timestamp(),
#                     'date': service.id
#                 })
            
#             # Add ads to activities
#             for ad in recent_ads:
#                 activities.append({
#                     'type': 'advertisement',
#                     'data': AdsBasicSerializer(ad).data,
#                     'timestamp': ad.created.timestamp(),
#                     'date': ad.created
#                 })
            
#             # Sort activities by timestamp
#             activities.sort(key=lambda x: x['timestamp'], reverse=True)
            
#             # Apply pagination
#             page = self.paginate_queryset(activities)
#             if page is not None:
#                 return self.get_paginated_response(page)
            
#             return Response(activities)
            
#         except Dealer.DoesNotExist:
#             return Response(
#                 {'error': 'Dealer not found'}, 
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             return Response(
#                 {'error': str(e)}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination

# Custom pagination class that only returns the results
class DealerPaymentPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response(data)

from .serializers import DealerPaymentSerializer
# ViewSet for dealer payments


class DealerPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DealerPaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DealerPaymentPagination

    def get_queryset(self):
        user = self.request.user
        if not user.is_dealer:
            return Payment.objects.none()
            
        return Payment.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('invoice').order_by('-payment_date')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(payment_status=status_filter)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(payment_date__range=[start_date, end_date])

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# dealer dashboard serviceprovider list page

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter  # Add SearchFilter import
from Accounts.models import ServiceProvider, Dealer  # Ensure you import Dealer model
from .serializers import ServiceProviderSerializer

# class DealerServiceProviderListView(generics.ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = ServiceProviderSerializer
#     filter_backends = [SearchFilter]  # Enable search functionality
#     search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']  # Define search fields

#     def get_queryset(self):
#         user = self.request.user  # Get the logged-in user
#         dealer = get_object_or_404(Dealer, user=user)  # Ensure the user is a dealer
#         return ServiceProvider.objects.filter(dealer=dealer)  # Filter by dealer

# class DealerServiceProviderListView(generics.ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = ServiceProviderSerializer
#     filter_backends = [SearchFilter]
#     search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']

#     def get_queryset(self):
#         user = self.request.user
#         dealer = get_object_or_404(Dealer, user=user)
#         return ServiceProvider.objects.filter(dealer=dealer)

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         user = self.request.user
#         dealer = get_object_or_404(Dealer, user=user)
#         context['dealer'] = dealer  # Pass dealer to the context
#         return context



# class DealerServiceProviderListView(generics.ListAPIView):
#     authentication_classes = [JWTAuthentication]  # Use JWT authentication here
#     permission_classes = [IsAuthenticated]
#     serializer_class = ServiceProviderSerializer
#     filter_backends = [SearchFilter]
#     search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']

#     def get_queryset(self):
#         user = self.request.user
#         dealer = get_object_or_404(Dealer, user=user)
#         return ServiceProvider.objects.filter(dealer=dealer)

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         user = self.request.user
#         dealer = get_object_or_404(Dealer, user=user)
#         context['dealer'] = dealer  # Pass dealer to the context
#         return context
    

from rest_framework.pagination import PageNumberPagination
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404

# Custom pagination class
class ServiceProviderPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'  # Allow client to override page size
    max_page_size = 100  # Maximum limit
    page_query_param = 'page'  # Query parameter for page number

class DealerServiceProviderListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceProviderSerializer
    filter_backends = [SearchFilter]
    search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']
    pagination_class = ServiceProviderPagination  # Add pagination class

    def get_queryset(self):
        user = self.request.user
        dealer = get_object_or_404(Dealer, user=user)
        return ServiceProvider.objects.filter(dealer=dealer).order_by('-created_date')  # Add ordering

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        dealer = get_object_or_404(Dealer, user=user)
        context['dealer'] = dealer
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            
            # Add extra information to the response
            response.data['total_service_providers'] = queryset.count()
            response.data['active_service_providers'] = queryset.filter(status='Active').count()
            
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

from rest_framework.views import APIView


# class DealerServiceProviderCountsView(APIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         dealer = get_object_or_404(Dealer, user=user)
        
#         total_service_providers = ServiceProvider.objects.filter(dealer=dealer).count()
#         approved_count = ServiceProvider.objects.filter(dealer=dealer, verification_by_dealer='APPROVED').count()
#         pending_count = ServiceProvider.objects.filter(dealer=dealer, verification_by_dealer='PENDING').count()

#         data = {
#             "total_service_providers": total_service_providers,
#             "approved_count": approved_count,
#             "pending_count": pending_count,
#         }
#         return Response(data)


class DealerServiceProviderCountsView(APIView):
    authentication_classes = [JWTAuthentication]  # Use JWT for access and refresh tokens
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        dealer = get_object_or_404(Dealer, user=user)
        
        total_service_providers = ServiceProvider.objects.filter(dealer=dealer).count()
        approved_count = ServiceProvider.objects.filter(dealer=dealer, verification_by_dealer='APPROVED').count()
        pending_count = ServiceProvider.objects.filter(dealer=dealer, verification_by_dealer='PENDING').count()

        data = {
            "total_service_providers": total_service_providers,
            "approved_count": approved_count,
            "pending_count": pending_count,
        }
        return Response(data)


# class DealerServiceProviderPendingListView(generics.ListAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = ServiceProviderSerializer
#     filter_backends = [SearchFilter]
#     search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']

#     def get_queryset(self):
#         user = self.request.user  # Ensure this is within the correct method
#         dealer = get_object_or_404(Dealer, user=user)
#         return ServiceProvider.objects.filter(dealer=dealer, verification_by_dealer='PENDING')

from .serializers import *

class DealerServiceProviderPendingListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]  # Use JWT for access and refresh tokens
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceProviderPendingSerializer
    filter_backends = [SearchFilter]
    search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']

    def get_queryset(self):
        user = self.request.user
        dealer = get_object_or_404(Dealer, user=user)
        return ServiceProvider.objects.filter(dealer=dealer, verification_by_dealer='PENDING')


from .serializers import ServiceProviderPendingSerializer

# class UpdateServiceProviderStatusView(generics.UpdateAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = ServiceProviderPendingSerializer

#     def get_object(self):
#         # Retrieve the service provider by ID from the URL
#         service_provider_id = self.kwargs.get('id')  # Assuming the URL includes an ID
#         user = self.request.user  # Get the logged-in user
#         dealer = get_object_or_404(Dealer, user=user)  # Ensure the user is a dealer
        
#         # Get the service provider and ensure it belongs to the logged-in dealer
#         service_provider = get_object_or_404(ServiceProvider, id=service_provider_id, dealer=dealer)
#         return service_provider

#     def perform_update(self, serializer):
#         # Change the status to 'APPROVED'
#         serializer.instance.verification_by_dealer = 'APPROVED'
#         serializer.save()


# service provider verification page normal id
# class UpdateServiceProviderStatusView(generics.UpdateAPIView):
#     authentication_classes = [JWTAuthentication]  # Use JWT for access and refresh tokens
#     permission_classes = [IsAuthenticated]
#     serializer_class = ServiceProviderPendingSerializer

#     def get_object(self):
#         # Retrieve the service provider by ID from the URL
#         service_provider_id = self.kwargs.get('id')  # Assuming the URL includes an ID
#         user = self.request.user  # Get the logged-in user
#         dealer = get_object_or_404(Dealer, user=user)  # Ensure the user is a dealer
        
#         # Get the service provider and ensure it belongs to the logged-in dealer
#         service_provider = get_object_or_404(ServiceProvider, id=service_provider_id, dealer=dealer)
#         return service_provider

#     def perform_update(self, serializer):
#         # Change the status to 'APPROVED'
#         serializer.instance.verification_by_dealer = 'APPROVED'
#         serializer.save()

#custom id
class UpdateServiceProviderStatusView(generics.UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceProviderPendingSerializer

    def get_object(self):
        custom_id = self.request.data.get('custom_id')
        user = self.request.user
        dealer = get_object_or_404(Dealer, user=user)
        service_provider = get_object_or_404(ServiceProvider, custom_id=custom_id, dealer=dealer)
        return service_provider

    def perform_update(self, serializer):
        serializer.save()

# from .serializers import FranchiseSerializer

# class DealerFranchiseeDetailView(generics.GenericAPIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         # Ensure the user is a dealer
#         if not request.user.is_dealer:
#             return Response({
#                 'message': 'Access denied. User is not a dealer.'
#             }, status=status.HTTP_403_FORBIDDEN)

#         try:
#             # Retrieve the dealer object for the logged-in user
#             dealer = Dealer.objects.get(user=request.user)

#             # Retrieve the franchisee data associated with this dealer
#             franchisee = dealer.franchisee
#             franchisee_data = FranchiseSerializer(franchisee).data

#             return Response({
#                 'message': 'Franchisee data retrieved successfully',
#                 'franchisee_data': franchisee_data
#             }, status=status.HTTP_200_OK)

#         except Dealer.DoesNotExist:
#             return Response({
#                 'message': 'Dealer profile not found for this user.'
#             }, status=status.HTTP_404_NOT_FOUND)

#         except Exception as e:
#             return Response({
#                 'message': f'An error occurred: {str(e)}'
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# from rest_framework import generics
# from rest_framework.filters import SearchFilter  # Correct import for SearchFilter
# from .serializers import ServiceproviderSerializerSearch
# from .serializers import *

# class SearchAPIView(generics.ListCreateAPIView):
#     search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']  # Correct fields
#     filter_backends = (SearchFilter,)  # Use SearchFilter directly
#     queryset = ServiceProvider.objects.all()
#     serializer_class = ServiceproviderSerializerSearch




# # views.py
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from Accounts.models import Dealer
# from .serializers import DealerFranchiseeSerializer

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def franchise_details_view(request):
#     try:
#         # Check if the user is a dealer and retrieve the dealer object
#         dealer = Dealer.objects.get(user=request.user)
        
#         # Retrieve the franchise associated with the dealer
#         franchise = dealer.franchisee

#         # Serialize the franchise data
#         serializer = DealerFranchiseeSerializer(franchise)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     except Dealer.DoesNotExist:
#         return Response(
#             {"error": "Dealer profile not found."}, 
#             status=status.HTTP_404_NOT_FOUND
#         )
#     except AttributeError:
#         return Response(
#             {"error": "No franchise associated with this dealer."},
#             status=status.HTTP_400_BAD_REQUEST
#         )




# class DealerServiceProviderDetailView(APIView):
#     authentication_classes = [JWTAuthentication]  # Use JWT for access and refresh tokens
#     permission_classes = [IsAuthenticated]

#     def get(self, request, service_provider_id):
#         user = request.user
#         dealer = get_object_or_404(Dealer, user=user)

#         service_provider = get_object_or_404(ServiceProvider, id=service_provider_id, dealer=dealer)

#         service_provider_data = ServiceProviderSerializer(service_provider)

#         services = service_provider.services.all()  # Get all services registered by the service provider

#         services_data = ServiceSerializer(services, many=True).data

#         response_data = {
#             'service_provider': service_provider_data.data,
#             'services': services_data,
#         }
#         return Response(response_data, status=status.HTTP_200_OK)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from rest_framework import status

class DealerServiceProviderDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get custom_id from request body
            custom_id = request.data.get('custom_id')
            if not custom_id:
                return Response(
                    {'error': 'custom_id is required in request body'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the dealer based on authenticated user
            user = request.user
            dealer = get_object_or_404(Dealer, user=user)

            # Get the service provider using custom_id and verify they belong to this dealer
            service_provider = get_object_or_404(
                ServiceProvider, 
                custom_id=custom_id, 
                dealer=dealer
            )

            # Get service provider details
            service_provider_data = ServiceProviderSerializer(service_provider).data

            # Get all services registered by the service provider
            services = service_provider.services.all()
            services_data = []
            
            for service in services:
                service_data = ServiceSerializer(service).data
                
                # Get ads related to this service
                ads = Ads.objects.filter(
                    service=service,
                    service_provider=service_provider
                )
                ads_data = AdsSerializer(ads, many=True).data
                
                # Combine service and its ads data
                service_data['ads'] = ads_data
                services_data.append(service_data)

            # Get all ads for this service provider
            all_ads = Ads.objects.filter(service_provider=service_provider)
            all_ads_data = AdsSerializer(all_ads, many=True).data

            response_data = {
                'service_provider': service_provider_data,
                'services': services_data,
                'all_ads': all_ads_data,  # All ads regardless of service
                'total_services': len(services_data),
                'total_ads': len(all_ads_data),
                'status': 'success'
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except ServiceProvider.DoesNotExist:
            return Response(
                {'error': 'Service provider not found or not associated with this dealer'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from django.shortcuts import get_object_or_404
# from rest_framework import status

# class DealerServiceProviderDetailView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, service_provider_id):
#         try:
#             # Get the dealer based on authenticated user
#             user = request.user
#             dealer = get_object_or_404(Dealer, user=user)

#             # Get the service provider and verify they belong to this dealer
#             service_provider = get_object_or_404(
#                 ServiceProvider, 
#                 id=service_provider_id, 
#                 dealer=dealer
#             )

#             # Get service provider details
#             service_provider_data = ServiceProviderSerializer(service_provider).data

#             # Get all services registered by the service provider
#             services = service_provider.services.all()
#             services_data = []
            
#             for service in services:
#                 service_data = ServiceSerializer(service).data
                
#                 # Get ads related to this service
#                 ads = Ads.objects.filter(
#                     service=service,
#                     service_provider=service_provider
#                 )
#                 ads_data = AdsSerializer(ads, many=True).data
                
#                 # Combine service and its ads data
#                 service_data['ads'] = ads_data
#                 services_data.append(service_data)

#             # Get all ads for this service provider
#             all_ads = Ads.objects.filter(service_provider=service_provider)
#             all_ads_data = AdsSerializer(all_ads, many=True).data

#             response_data = {
#                 'service_provider': service_provider_data,
#                 'services': services_data,
#                 'all_ads': all_ads_data,  # All ads regardless of service
#                 'total_services': len(services_data),
#                 'total_ads': len(all_ads_data),
#                 'status': 'success'
#             }

#             return Response(response_data, status=status.HTTP_200_OK)

#         except ServiceProvider.DoesNotExist:
#             return Response(
#                 {'error': 'Service provider not found or not associated with this dealer'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


from Accounts.models import Dealer, PaymentRequest

    
class PaymentRequestCreateView(APIView):
    def post(self, request, *args, **kwargs):
        dealer = Dealer.objects.filter(user=request.user).first()  # Adjust to fetch the dealer instance based on the logged-in user

        if dealer is None:
            return Response({"error": "No dealer instance found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch the receiver, assuming you want a superuser or any user
        receiver = User.objects.filter(is_superuser=True).first()  # Change as necessary
        # Alternatively, if you want any user:
        # receiver = User.objects.first()

        if receiver is None:
            return Response({"error": "No superuser found to set as receiver."}, status=status.HTTP_404_NOT_FOUND)

        # Extract data from request
        data = request.data
        # Ensure all required fields are present
        required_fields = [
            "amount", "description", "phone", "payment_method",
            "account_holder_name", "bank_name", "bank_branch",
            "account_number", "ifsc_code", "email"
        ]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return Response(
                {field: "This field is required." for field in missing_fields},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the payment request
        try:
            payment_request = PaymentRequest.objects.create(
                sernder=dealer,  # Valid dealer instance
                receiver=receiver,
                amount=data["amount"],
                description=data["description"],
                email=data["email"],
                country_code=data.get("country_code"),  # Adjust if necessary
                phone=data["phone"],
                payment_method=data["payment_method"],
                account_holder_name=data["account_holder_name"],
                bank_name=data["bank_name"],
                bank_branch=data["bank_branch"],
                account_number=data["account_number"],
                ifsc_code=data["ifsc_code"],
            )
            serializer = PaymentRequestSerializer(payment_request)  # Assuming you have a serializer
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)