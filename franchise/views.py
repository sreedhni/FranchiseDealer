from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .serializers import FranchiseeLoginSerializer

class FranchiseeLoginView(generics.GenericAPIView):
    serializer_class = FranchiseeLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Login successful',
            'refresh': str(refresh),
            'access': str(refresh.access_token),  # Include both tokens in the response
            'user_id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'is_franchisee': user.is_franchisee,
        }, status=status.HTTP_200_OK)



# franchisee homepage

from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404

class FranchiseDashboardCountsView(APIView):
    authentication_classes = [JWTAuthentication]  # Use JWT for access and refresh tokens
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        franchisee = get_object_or_404(Franchisee, user=user)

        # Get current date and calculate the start and end of the previous and current months
        today = timezone.now().date()
        first_day_of_current_month = today.replace(day=1)
        first_day_of_previous_month = (first_day_of_current_month - timedelta(days=1)).replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)

        # Service Provider counts for the current and previous months
        approved_count_current_month = ServiceProvider.objects.filter(
            franchisee=franchisee,
            verification_by_dealer='APPROVED',
            created_date__gte=first_day_of_current_month,
            created_date__lte=today
        ).count()

        approved_count_previous_month = ServiceProvider.objects.filter(
            franchisee=franchisee,
            verification_by_dealer='APPROVED',
            created_date__gte=first_day_of_previous_month,
            created_date__lte=last_day_of_previous_month
        ).count()

        # Calculate percentage change
        if approved_count_previous_month == 0:
            percentage_change = 0  # Avoid division by zero
        else:
            percentage_change = ((approved_count_current_month - approved_count_previous_month) / approved_count_previous_month) * 100

        # Total approved service providers for the franchisee
        total_approved_count = ServiceProvider.objects.filter(
            franchisee=franchisee, 
            verification_by_dealer='APPROVED'
        ).count()

        # Total dealers under the franchisee
        total_dealers_count = Dealer.objects.filter(franchisee=franchisee).count()

        # Calculate the percentage change for dealers
        dealer_count_previous_month = Dealer.objects.filter(
            franchisee=franchisee,
            craeted_date__gte=first_day_of_previous_month,
            craeted_date__lte=last_day_of_previous_month
        ).count()

        if dealer_count_previous_month == 0:
            dealer_percentage_change = 0  # Avoid division by zero
        else:
            dealer_percentage_change = ((total_dealers_count - dealer_count_previous_month) / dealer_count_previous_month) * 100

        data = {
            "percentage_change_service_provider": round(percentage_change, 2),
            "total_approved_service_providers": total_approved_count,
            # "approved_count_current_month_service_provider": approved_count_current_month,
            "percentage_change_dealers": round(dealer_percentage_change, 2),
            "total_dealers_count": total_dealers_count
        }

        return Response(data)

class FranchiseeServiceRegisterCountsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_service_register_data(self, franchisee):
        # Define the start and end dates for current and previous month
        now = timezone.now()
        start_of_current_month = now.replace(day=1)
        start_of_previous_month = (start_of_current_month - timedelta(days=1)).replace(day=1)
        end_of_previous_month = start_of_current_month - timedelta(days=1)

        # Filter ServiceRegister entries under the franchisee's service providers
        service_registers = ServiceRegister.objects.filter(service_provider__franchisee=franchisee)

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

        # Total count of all-time service registrations under the franchisee
        total_count = service_registers.count()

        return {
            "total_count": total_count,
            "percentage_change": round(percentage_change, 2)
        }

    def get(self, request):
        user = request.user
        franchisee = get_object_or_404(Franchisee, user=user)  # Get the franchisee associated with the logged-in user

        # Fetch total count and percentage change data
        service_register_data = self.get_service_register_data(franchisee)

        return Response(service_register_data)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

class FranchiseComplaintsCountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get total complaints count and month-over-month trend
        """
        if not request.user.is_franchisee:
            return Response(
                {'error': 'User is not a franchisee'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Get the franchise
            franchise = Franchisee.objects.get(user=request.user)
            
            # Get time periods for trend calculation
            today = timezone.now()
            current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_end = current_month_start - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)

            # Get service provider IDs under this franchise
            sp_user_ids = ServiceProvider.objects.filter(
                franchisee=franchise
            ).values_list('user_id', flat=True)

            # Get all complaints ever
            total_complaints = Complaint.objects.filter(
                Q(sender_id__in=sp_user_ids) | Q(receiver_id__in=sp_user_ids)
            ).count()

            # Get complaints for current and previous month (for trend)
            current_month_count = Complaint.objects.filter(
                Q(sender_id__in=sp_user_ids) | Q(receiver_id__in=sp_user_ids),
                submitted_at__gte=current_month_start,
                submitted_at__lte=today
            ).count()

            previous_month_count = Complaint.objects.filter(
                Q(sender_id__in=sp_user_ids) | Q(receiver_id__in=sp_user_ids),
                submitted_at__gte=last_month_start,
                submitted_at__lte=last_month_end
            ).count()

            # Calculate percentage change
            if previous_month_count > 0:
                percentage_change = ((current_month_count - previous_month_count) / previous_month_count) * 100
            else:
                percentage_change = 100 if current_month_count > 0 else 0

            # Prepare response data
            response_data = {
                'total_complaints': total_complaints,
                'percentage_change': round(percentage_change, 2),
                'trend': 'increase' if percentage_change > 0 else 'decrease' if percentage_change < 0 else 'same'
            }

            serializer = FranchiseComplaintsCountSerializer(response_data)
            return Response(serializer.data)

        except Franchisee.DoesNotExist:
            return Response(
                {'error': 'Franchise not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

class FranchiseAdsCountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get total ads count and month-over-month trend for a franchise's service providers
        """
        if not request.user.is_franchisee:
            return Response(
                {'error': 'User is not a franchisee'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Get the franchise
            franchise = Franchisee.objects.get(user=request.user)
            
            # Get all service providers under this franchise
            service_providers = ServiceProvider.objects.filter(franchisee=franchise)
            service_provider_ids = service_providers.values_list('id', flat=True)

            # Time periods for trend calculation
            today = timezone.now()
            current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_end = current_month_start - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)

            # Get all ads ever for these service providers
            all_ads = Ads.objects.filter(
                service_provider_id__in=service_provider_ids
            )
            total_ads = all_ads.count()

            # Get currently active ads
            active_ads = all_ads.filter(
                starting_date__lte=today,
                ending_date__gte=today,
                status='active'  # Adjust status value according to your model
            ).count()

            # Get ads created in current month
            current_month_ads = all_ads.filter(
                created__gte=current_month_start,
                created__lte=today
            ).count()

            # Get ads created in previous month
            previous_month_ads = all_ads.filter(
                created__gte=last_month_start,
                created__lte=last_month_end
            ).count()

            # Calculate percentage change
            if previous_month_ads > 0:
                percentage_change = ((current_month_ads - previous_month_ads) / previous_month_ads) * 100
            else:
                percentage_change = 100 if current_month_ads > 0 else 0

            # Get breakdown by service provider
            ads_by_provider = all_ads.values(
                'service_provider__custom_id',
                'service_provider__user__full_name'
            ).annotate(
                ads_count=Count('id'),
                active_ads=Count('id', filter=Q(
                    ending_date__gte=today,
                    status='active'
                ))
            )

            # Prepare response data
            response_data = {
                'total_ads': total_ads,
                'active_ads': active_ads,
                'percentage_change': round(percentage_change, 2),
                'trend': 'increase' if percentage_change > 0 else 'decrease' if percentage_change < 0 else 'same',
                'service_provider_count': service_providers.count(),
                'detailed_breakdown': {
                    'current_month_ads': current_month_ads,
                    'previous_month_ads': previous_month_ads,
                    'providers': list(ads_by_provider)
                }
            }

            serializer = FranchiseAdsCountSerializer(response_data)
            return Response(serializer.data)

        except Franchisee.DoesNotExist:
            return Response(
                {'error': 'Franchise not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, F, Q
from datetime import timedelta
from Accounts.models import ServiceProvider, Invoice
from .serializers import FranchiseearningServiceProviderSerializer, InvoiceSerializer

from django.db.models import Sum, F, DecimalField

class FranchiseEarningsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Check if the user has a related franchisee and retrieve it
        franchisee = request.user.franchisee.first()  # Assuming 'franchisee' is a related name for a one-to-many relationship
        if franchisee:
            service_providers = ServiceProvider.objects.filter(franchisee_id=franchisee.id)
        else:
            service_providers = ServiceProvider.objects.none()
        
        service_providers_data = FranchiseearningServiceProviderSerializer(service_providers, many=True).data
        now = timezone.now()

        # Retrieve all related invoices for the franchise's service providers
        invoices = Invoice.objects.filter(
            service_request__in=[sp.id for sp in service_providers],
            payment_status='paid'
        )
        invoices_data = InvoiceSerializer(invoices, many=True).data

        # Calculate commission earnings (4% of each transaction)
        total_commission = invoices.aggregate(
            total_earnings=Sum(F('total_amount') * 0.04, output_field=DecimalField())
        )['total_earnings'] or 0

        # Compare current and previous month's commission earnings
        current_month_start = now.replace(day=1)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        current_month_earnings = invoices.filter(
            invoice_date__gte=current_month_start
        ).aggregate(total=Sum(F('total_amount') * 0.04, output_field=DecimalField()))['total'] or 0

        previous_month_earnings = invoices.filter(
            invoice_date__gte=previous_month_start,
            invoice_date__lt=current_month_start
        ).aggregate(total=Sum(F('total_amount') * 0.04, output_field=DecimalField()))['total'] or 0

        # Calculate percentage increase or decrease
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


from rest_framework import views, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class BaseFranchiseView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def get_franchise(self):
        if not hasattr(self.request.user, 'franchisee'):
            raise PermissionError("User is not associated with any franchise")
        return get_object_or_404(Franchisee, user=self.request.user)

class FranchiseDetailsView(BaseFranchiseView):
    def get(self, request):
        franchise = self.get_franchise()
        
        data = {
            'franchise_id': franchise.custom_id,
            'owner_name': franchise.user.full_name,
            'community_name': franchise.community_name,
            'type': franchise.type.name,
            'dealers_count': franchise.dealers,
            'service_providers_count': franchise.service_providers,
            'revenue': str(franchise.revenue),  # Convert Decimal to string for JSON
            'valid_from': franchise.valid_from,
            'valid_up_to': franchise.valid_up_to,
            'status': franchise.status,
        }
        
        return Response(data)

class RecentActivitiesView(BaseFranchiseView):
    pagination_class = CustomPagination

    def get(self, request):
        franchise = self.get_franchise()
        
        # Get service providers under this franchise
        service_providers = ServiceProvider.objects.filter(
            franchisee=franchise
        ).select_related('user')
        service_provider_users = service_providers.values_list('user_id', flat=True)

        # Get last 30 days of activities
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Get recent ads
        recent_ads = Ads.objects.filter(
            service_provider__user_id__in=service_provider_users,
            created__gte=thirty_days_ago
        ).select_related('service_provider', 'service')

        # Get recent service registrations
        recent_services = ServiceRegister.objects.filter(
            service_provider__user_id__in=service_provider_users
        ).select_related('service_provider', 'category', 'subcategory')

        # Combine activities
        activities = []
        for ad in recent_ads:
            activities.append({
                'type': 'advertisement',
                'date': ad.created,
                'title': ad.title,
                'service_provider': ad.service_provider.user.full_name,
                'details': {
                    'ad_type': ad.ad_type,
                    'amount': str(ad.amount),
                    'status': ad.status
                }
            })

        for service in recent_services:
            activities.append({
                'type': 'service_registration',
                'date': service.service_provider.created_date,
                'title': service.subcategory.title,
                'service_provider': service.service_provider.user.full_name,
                'details': {
                    'category': service.category.title,
                    'status': service.status,
                    'lead_balance': service.available_lead_balance
                }
            })

        # Sort activities by date
        activities.sort(key=lambda x: x['date'], reverse=True)

        # Paginate
        paginator = self.pagination_class()
        paginated_activities = paginator.paginate_queryset(activities, request)
        
        return paginator.get_paginated_response(paginated_activities)

class IncompleteBookingsView(BaseFranchiseView):
    pagination_class = CustomPagination

    def get(self, request):
        franchise = self.get_franchise()
        
        # Get service providers under this franchise
        service_provider_users = ServiceProvider.objects.filter(
            franchisee=franchise
        ).values_list('user_id', flat=True)

        # Get incomplete bookings
        incomplete_requests = ServiceRequest.objects.filter(
            service_provider__in=service_provider_users,
            work_status__in=['pending', 'in_progress']
        ).select_related(
            'customer',
            'service_provider',
            'service'
        ).order_by('-request_date')

        # Format booking data
        bookings_data = []
        for booking in incomplete_requests:
            bookings_data.append({
                'booking_id': str(booking.booking_id),
                'title': booking.title,
                'customer_name': booking.customer.full_name,
                'service_provider': booking.service_provider.full_name,
                'service': booking.service.subcategory.title,
                'work_status': booking.work_status,
                'acceptance_status': booking.acceptance_status,
                'request_date': booking.request_date,
                'availability': {
                    'from': booking.availability_from,
                    'to': booking.availability_to
                }
            })

        # Paginate
        paginator = self.pagination_class()
        paginated_bookings = paginator.paginate_queryset(bookings_data, request)
        
        return paginator.get_paginated_response(paginated_bookings)

class ComplaintsView(BaseFranchiseView):
    def get(self, request):
        franchise = self.get_franchise()
        
        # Get service providers under this franchise
        service_provider_users = ServiceProvider.objects.filter(
            franchisee=franchise
        ).values_list('user_id', flat=True)

        # Get complaints
        complaints = Complaint.objects.filter(
            Q(receiver__in=service_provider_users) |
            Q(sender__in=service_provider_users)
        ).select_related(
            'sender',
            'receiver',
            'service_request'
        ).order_by('-submitted_at')

        # Format complaint data
        complaints_data = []
        for complaint in complaints:
            complaints_data.append({
                'subject': complaint.subject,
                'description': complaint.description,
                'sender': complaint.sender.full_name,
                'receiver': complaint.receiver.full_name,
                'status': complaint.status,
                'submitted_at': complaint.submitted_at,
                'resolved_at': complaint.resolved_at,
                'resolution_notes': complaint.resolution_notes,
                'service_request': str(complaint.service_request.booking_id) if complaint.service_request else None
            })

        return Response(complaints_data)


from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from Accounts.models import Payment, Franchisee
from .serializers import PaymentSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class FranchiseePaymentPagination(PageNumberPagination):
    page_size = 10  # You can set a custom page size here
    page_size_query_param = 'page_size'
    max_page_size = 100

class FranchiseePaymentView(APIView):
    """View to retrieve payment data for the logged-in franchisee."""
    permission_classes = [IsAuthenticated]
    pagination_class = FranchiseePaymentPagination

    def get(self, request, *args, **kwargs):
        # Ensure the user is a franchisee
        if not request.user.is_franchisee:
            return Response({'error': 'User is not a franchisee'}, status=status.HTTP_403_FORBIDDEN)

        # Retrieve the franchisee instance
        franchisee = get_object_or_404(Franchisee, user=request.user)

        # Retrieve payments associated with the franchisee as receiver
        payments = Payment.objects.filter(receiver=request.user)

        # Paginate the queryset
        paginator = FranchiseePaymentPagination()
        paginated_payments = paginator.paginate_queryset(payments, request)
        
        # Serialize the paginated payment data
        serializer = PaymentSerializer(paginated_payments, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response({
            'franchisee_id': franchisee.custom_id,
            'community_name': franchisee.community_name,
            'payments': serializer.data
        })





# service provider list page

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from Accounts.models import *
from .serializers import ServiceProviderSerializer
from rest_framework import filters  # Import filters here

# class FranchiseeServiceProviderListView(generics.ListAPIView):
#     authentication_classes = [JWTAuthentication]  # Use JWT authentication
#     permission_classes = [IsAuthenticated]
#     serializer_class = ServiceProviderSerializer
#     filter_backends = [filters.SearchFilter]  # Use the filters module for SearchFilter
#     search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']

#     def get_queryset(self):
#         user = self.request.user
#         # Get the Franchisee associated with the logged-in user
#         franchisee = get_object_or_404(Franchisee, user=user)
#         # Return the service providers associated with the franchisee
#         return ServiceProvider.objects.filter(franchisee=franchisee)

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         user = self.request.user
#         franchisee = get_object_or_404(Franchisee, user=user)
#         context['franchisee'] = franchisee  # Pass franchisee to the context
#         return context


class FranchiseeServiceProviderListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]  # Use JWT authentication
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceProviderSerializer
    filter_backends = [filters.SearchFilter]  # Use the filters module for SearchFilter
    search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']

    def get_queryset(self):
        user = self.request.user
        # Get the Franchisee associated with the logged-in user
        franchisee = get_object_or_404(Franchisee, user=user)

        # Retrieve service providers associated with the franchisee
        queryset = ServiceProvider.objects.filter(franchisee=franchisee)

        # Handle sorting based on query parameters
        sort_option = self.request.query_params.get('sort', 'newest')  # Default to newest
        if sort_option == 'oldest':
            queryset = queryset.order_by('created_date')  # Sort by created_date ascending
        else:  # Default to 'newest'
            queryset = queryset.order_by('-created_date')  # Sort by created_date descending

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        franchisee = get_object_or_404(Franchisee, user=user)
        context['franchisee'] = franchisee  # Pass franchisee to the context
        return context

from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class FranchiseeServiceProviderListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceProviderSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        # Get the Franchisee associated with the logged-in user
        franchisee = get_object_or_404(Franchisee, user=user)

        # Retrieve service providers associated with the franchisee
        queryset = ServiceProvider.objects.filter(franchisee=franchisee)

        # Handle sorting based on query parameters
        sort_option = self.request.query_params.get('sort', 'newest')  # Default to newest
        if sort_option == 'oldest':
            queryset = queryset.order_by('created_date')  # Sort by created_date ascending
        else:  # Default to 'newest'
            queryset = queryset.order_by('-created_date')  # Sort by created_date descending

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        franchisee = get_object_or_404(Franchisee, user=user)
        context['franchisee'] = franchisee  # Pass franchisee to the context
        return context


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

class FranchiseeServiceProviderCountsView(APIView):
    authentication_classes = [JWTAuthentication]  # Use JWT for access and refresh tokens
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Get the Franchisee associated with the logged-in user
        franchisee = get_object_or_404(Franchisee, user=user)
        
        # Count service providers associated with the franchisee
        total_service_providers = ServiceProvider.objects.filter(franchisee=franchisee).count()
        approved_count = ServiceProvider.objects.filter(franchisee=franchisee, verification_by_dealer='APPROVED').count()
        pending_count = ServiceProvider.objects.filter(franchisee=franchisee, verification_by_dealer='PENDING').count()

        data = {
            "total_service_providers": total_service_providers,
            "approved_count": approved_count,
            "pending_count": pending_count,
        }
        return Response(data)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from Accounts.models import ServiceProvider, Franchisee, ServiceRegister, CustomerReview,ServiceRequest,Ads
from .serializers import *


# service provider detailview normal_id

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from django.shortcuts import get_object_or_404
# from django.http import Http404
# from django.db.models import Avg


# class FranchiseeServiceProviderDetailView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, service_provider_id):
#         # Verify the franchisee making the request
#         user = request.user
#         franchisee = get_object_or_404(Franchisee, user=user)

#         # Get the service provider and verify they belong to this franchisee
#         service_provider = get_object_or_404(
#             ServiceProvider, 
#             id=service_provider_id, 
#             franchisee=franchisee
#         )

#         # Get the service provider's user object for related data
#         provider_user = service_provider.user

#         # Get all related data
#         services = ServiceRegister.objects.filter(service_provider=service_provider)
#         customer_reviews = CustomerReview.objects.filter(service_provider=provider_user)
#         service_requests = ServiceRequest.objects.filter(service_provider=provider_user)
#         ads = Ads.objects.filter(service_provider=service_provider)

#         # Serialize all the data
#         response_data = {
#             'service_provider': {
#                 'personal_info': {
#                     'id': service_provider.id,
#                     'custom_id': service_provider.custom_id,
#                     'full_name': provider_user.full_name,
#                     'email': provider_user.email,
#                     'phone_number': provider_user.phone_number,
#                     'profile_image': request.build_absolute_uri(service_provider.profile_image.url) if service_provider.profile_image else None,
#                     'date_of_birth': service_provider.date_of_birth,
#                     'gender': service_provider.gender,
#                     'about': service_provider.about,
#                 },
#                 'business_info': {
#                     'dealer': service_provider.dealer.custom_id,
#                     'franchisee': service_provider.franchisee.custom_id,
#                     'address_proof_document': service_provider.address_proof_document,
#                     'id_number': service_provider.id_number,
#                     'payout_required': service_provider.payout_required,
#                     'status': service_provider.status,
#                     'verification_by_dealer': service_provider.verification_by_dealer,
#                     'created_date': service_provider.created_date,
#                 }
#             },
#             'services': [{
#                 'id': service.id,
#                 'description': service.description,
#                 'gstcode': service.gstcode,
#                 'category': service.category.title,
#                 'subcategory': service.subcategory.title,
#                 'status': service.status,
#                 'available_lead_balance': service.available_lead_balance,
#                 'image': request.build_absolute_uri(service.image.url) if service.image else None,
#                 'license': request.build_absolute_uri(service.license.url) if service.license else None,
#             } for service in services],
#             'customer_reviews': [{
#                 'id': review.id,
#                 'customer_name': review.customer.full_name,
#                 'rating': review.rating,
#                 'comment': review.comment,
#                 'created_at': review.created_at,
#                 'image': request.build_absolute_uri(review.image.url) if review.image else None,
#             } for review in customer_reviews],
#             'service_requests': [{
#                 'booking_id': str(request.booking_id),
#                 'title': request.title,
#                 'customer_name': request.customer.full_name,
#                 'service_title': request.service.subcategory.title,
#                 'work_status': request.work_status,
#                 'acceptance_status': request.acceptance_status,
#                 'request_date': request.request_date,
#                 'availability_from': request.availability_from,
#                 'availability_to': request.availability_to,
#                 'additional_notes': request.additional_notes,
#                 'image': request.build_absolute_uri(request.image.url) if request.image else None,
#             } for request in service_requests],
#             'ads': [{
#                 'id': ad.id,
#                 'title': ad.title,
#                 'ad_type': ad.ad_type,
#                 'service_title': ad.service.subcategory.title,
#                 'amount': str(ad.amount),
#                 'starting_date': ad.starting_date,
#                 'ending_date': ad.ending_date,
#                 'payment': ad.payment,
#                 'status': ad.status,
#                 'created': ad.created,
#             } for ad in ads],
#         }

#         # Add summary statistics
#         response_data['summary'] = {
#             'total_services': services.count(),
#             'total_reviews': customer_reviews.count(),
#             'average_rating': customer_reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
#             'total_service_requests': service_requests.count(),
#             'pending_requests': service_requests.filter(work_status='pending').count(),
#             'active_ads': ads.filter(status='active').count(),
#         }

#         return Response(response_data, status=status.HTTP_200_OK)

#     def handle_exception(self, exc):
#         if isinstance(exc, Http404):
#             return Response(
#                 {'error': 'Service provider not found or not associated with this franchisee'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         return super().handle_exception(exc)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Avg

# service provider detailview custom_id

class FranchiseeServiceProviderDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get custom_id from request body
        custom_id = request.data.get('custom_id')
        if not custom_id:
            return Response(
                {'error': 'Service provider custom ID is required in request body'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the franchisee making the request
        user = request.user
        franchisee = get_object_or_404(Franchisee, user=user)

        # Get the service provider and verify they belong to this franchisee
        try:
            service_provider = ServiceProvider.objects.get(
                custom_id=custom_id,
                franchisee=franchisee
            )
        except ServiceProvider.DoesNotExist:
            return Response(
                {'error': 'Service provider not found or not associated with this franchisee'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get the service provider's user object for related data
        provider_user = service_provider.user

        # Get all related data
        services = ServiceRegister.objects.filter(service_provider=service_provider)
        customer_reviews = CustomerReview.objects.filter(service_provider=provider_user)
        service_requests = ServiceRequest.objects.filter(service_provider=provider_user)
        ads = Ads.objects.filter(service_provider=service_provider)

        # Serialize all the data
        response_data = {
            'service_provider': {
                'personal_info': {
                    'id': service_provider.id,
                    'custom_id': service_provider.custom_id,
                    'full_name': provider_user.full_name,
                    'email': provider_user.email,
                    'phone_number': provider_user.phone_number,
                    'profile_image': request.build_absolute_uri(service_provider.profile_image.url) if service_provider.profile_image else None,
                    'date_of_birth': service_provider.date_of_birth,
                    'gender': service_provider.gender,
                    'about': service_provider.about,
                },
                'business_info': {
                    'dealer': service_provider.dealer.custom_id,
                    'franchisee': service_provider.franchisee.custom_id,
                    'address_proof_document': service_provider.address_proof_document,
                    'id_number': service_provider.id_number,
                    'payout_required': service_provider.payout_required,
                    'status': service_provider.status,
                    'verification_by_dealer': service_provider.verification_by_dealer,
                    'created_date': service_provider.created_date,
                }
            },
            'services': [{
                'id': service.id,
                'description': service.description,
                'gstcode': service.gstcode,
                'category': service.category.title,
                'subcategory': service.subcategory.title,
                'status': service.status,
                'available_lead_balance': service.available_lead_balance,
                'image': request.build_absolute_uri(service.image.url) if service.image else None,
                'license': request.build_absolute_uri(service.license.url) if service.license else None,
            } for service in services],
            'customer_reviews': [{
                'id': review.id,
                'customer_name': review.customer.full_name,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at,
                'image': request.build_absolute_uri(review.image.url) if review.image else None,
            } for review in customer_reviews],
            'service_requests': [{
                'booking_id': str(request.booking_id),
                'title': request.title,
                'customer_name': request.customer.full_name,
                'service_title': request.service.subcategory.title,
                'work_status': request.work_status,
                'acceptance_status': request.acceptance_status,
                'request_date': request.request_date,
                'availability_from': request.availability_from,
                'availability_to': request.availability_to,
                'additional_notes': request.additional_notes,
                'image': request.build_absolute_uri(request.image.url) if request.image else None,
            } for request in service_requests],
            'ads': [{
                'id': ad.id,
                'title': ad.title,
                'ad_type': ad.ad_type,
                'service_title': ad.service.subcategory.title,
                'amount': str(ad.amount),
                'starting_date': ad.starting_date,
                'ending_date': ad.ending_date,
                'payment': ad.payment,
                'status': ad.status,
                'created': ad.created,
            } for ad in ads],
        }

        # Add summary statistics
        response_data['summary'] = {
            'total_services': services.count(),
            'total_reviews': customer_reviews.count(),
            'average_rating': customer_reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
            'total_service_requests': service_requests.count(),
            'pending_requests': service_requests.filter(work_status='pending').count(),
            'active_ads': ads.filter(status='active').count(),
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            return Response(
                {'error': 'Service provider not found or not associated with this franchisee'},
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exception(exc)

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import Http404

class ServicePaymentCustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# custom_id
class FranchiseeServiceProviderPaymentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = ServicePaymentCustomPagination

    def post(self, request):
        try:
            # Validate request data
            serializer = CustomIDRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Get custom_id from validated data
            custom_id = serializer.validated_data['custom_id']

            # Verify the franchisee making the request
            user = request.user
            franchisee = get_object_or_404(Franchisee, user=user)

            # Get the service provider and verify they belong to this franchisee
            try:
                service_provider = ServiceProvider.objects.get(
                    custom_id=custom_id,
                    franchisee=franchisee
                )
            except ServiceProvider.DoesNotExist:
                return Response(
                    {'error': 'Service provider not found or not associated with this franchisee'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get filter parameters from query params
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            payment_status = request.GET.get('status')

            # Base queryset
            payments_queryset = Payment.objects.filter(
                receiver=service_provider.user
            )

            # Apply filters if provided
            if start_date and end_date:
                payments_queryset = payments_queryset.filter(
                    payment_date__range=[start_date, end_date]
                )
            if payment_status:
                payments_queryset = payments_queryset.filter(
                    payment_status=payment_status
                )

            # Order by payment date (most recent first)
            payments_queryset = payments_queryset.order_by('-payment_date')

            # Get the paginator instance
            paginator = self.pagination_class()
            
            # Paginate the payments queryset
            paginated_payments = paginator.paginate_queryset(payments_queryset, request)

            # Calculate summary statistics
            total_payments = payments_queryset.count()
            total_amount = payments_queryset.aggregate(
                total=models.Sum('amount_paid')
            )['total'] or 0

            # Prepare the simplified payment data
            payments_data = [{
                'transaction_id': payment.transaction_id,
                'sender_name': payment.sender.full_name,
                'date': payment.payment_date.strftime('%Y-%m-%d %H:%M'),
                'amount': str(payment.amount_paid),
                'status': payment.payment_status,
                'payment_mode': payment.payment_mode if hasattr(payment, 'payment_mode') else None,
                'description': payment.description if hasattr(payment, 'description') else None
            } for payment in paginated_payments]

            # Response with pagination details and summary
            response_data = {
                'service_provider': {
                    'custom_id': service_provider.custom_id,
                    'name': service_provider.user.full_name,
                    'email': service_provider.user.email,
                    'phone': service_provider.user.phone_number
                },
                'summary': {
                    'total_payments': total_payments,
                    'total_amount': str(total_amount),
                    'successful_payments': payments_queryset.filter(payment_status='success').count(),
                    'pending_payments': payments_queryset.filter(payment_status='pending').count()
                },
                'results': payments_data,
                'pagination': {
                    'total_records': paginator.page.paginator.count,
                    'total_pages': paginator.page.paginator.num_pages,
                    'current_page': paginator.page.number,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link()
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            return Response(
                {'error': 'Service provider not found or not associated with this franchisee'},
                status=status.HTTP_404_NOT_FOUND
            )
        return super().handle_exception(exc)

# normal_id

# class FranchiseeServiceProviderPaymentView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     pagination_class = ServicePaymentCustomPagination

#     def get(self, request, service_provider_id):
#         try:
#             # Verify the franchisee making the request
#             user = request.user
#             franchisee = get_object_or_404(Franchisee, user=user)

#             # Get the service provider and verify they belong to this franchisee
#             service_provider = get_object_or_404(
#                 ServiceProvider, 
#                 id=service_provider_id, 
#                 franchisee=franchisee
#             )

#             # Get all payments related to this service provider
#             all_payments = Payment.objects.filter(
#                 receiver=service_provider.user
#             ).order_by('-payment_date')

#             # Get the paginator instance
#             paginator = self.pagination_class()
            
#             # Paginate the payments queryset
#             paginated_payments = paginator.paginate_queryset(all_payments, request)

#             # Prepare the simplified payment data
#             payments_data = [{
#                 'transaction_id': payment.transaction_id,
#                 'sender_name': payment.sender.full_name,
#                 'date': payment.payment_date.strftime('%Y-%m-%d %H:%M'),
#                 'amount': str(payment.amount_paid),
#                 'status': payment.payment_status
#             } for payment in paginated_payments]

#             # Response with pagination details
#             response_data = {
#                 'results': payments_data,
#                 'pagination': {
#                     'total_records': paginator.page.paginator.count,
#                     'total_pages': paginator.page.paginator.num_pages,
#                     'current_page': paginator.page.number,
#                     'next': paginator.get_next_link(),
#                     'previous': paginator.get_previous_link()
#                 }
#             }

#             return Response(response_data, status=status.HTTP_200_OK)

#         except Http404:
#             return Response(
#                 {'error': 'Service provider not found or not associated with this franchisee'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     def handle_exception(self, exc):
#         if isinstance(exc, Http404):
#             return Response(
#                 {'error': 'Service provider not found or not associated with this franchisee'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         return super().handle_exception(exc)

# class FranchiseeServiceProviderDetailView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, service_provider_id):
#         user = request.user
#         franchisee = get_object_or_404(Franchisee, user=user)

#         # Retrieve the service provider associated with the franchisee
#         service_provider = get_object_or_404(ServiceProvider, id=service_provider_id, franchisee=franchisee)

#         # Serialize service provider data
#         service_provider_data = ServiceProviderSerializer(service_provider)

#         # Get services registered by the service provider
#         services = service_provider.services.all()
#         services_data = ServiceSerializer(services, many=True).data

#         # Get recent service requests
#         service_requests = ServiceRequest.objects.filter(service_provider=service_provider).order_by('-request_date')[:5]
#         service_requests_data = ServiceRequestSerializer(service_requests, many=True).data

#         # Get ads associated with the service provider
#         ads = Ads.objects.filter(service_provider=service_provider).order_by('-created')[:5]
#         ads_data = AdsSerializer(ads, many=True).data

#         # Compile the response data
#         response_data = {
#             'service_provider': service_provider_data.data,
#             'services': services_data,
#             'recent_service_requests': service_requests_data,
#             'ads': ads_data,
#         }

#         return Response(response_data, status=status.HTTP_200_OK)


# from rest_framework import generics, filters
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from django.shortcuts import get_object_or_404
# from Accounts.models import Franchisee, Dealer
# from .serializers import DealerSerializer  # Create this serializer if it doesn't already exist

# class FranchiseeDealerListView(generics.ListAPIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = DealerSerializer
#     filter_backends = [filters.SearchFilter]
#     search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']

#     def get_queryset(self):
#         # Get the logged-in user
#         user = self.request.user
#         # Retrieve the Franchisee associated with the logged-in user
#         franchisee = get_object_or_404(Franchisee, user=user)
        
#         # Retrieve sorting option from URL path; default to 'newest' if not specified
#         sort_option = self.kwargs.get('sort_option', 'newest')

#         # Apply sorting order based on the path parameter
#         queryset = Dealer.objects.filter(franchisee=franchisee)
        
#         # Check sort option and apply ordering accordingly
#         if sort_option == 'oldest':
#             queryset = queryset.order_by('craeted_date')
#         else:  # Default to 'newest'
#             queryset = queryset.order_by('-craeted_date')

#         return queryset

#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context['franchisee'] = get_object_or_404(Franchisee, user=self.request.user)
#         return context


# dealer listview

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from Accounts.models import Franchisee, Dealer
from .serializers import DealerSerializer

class FranchiseeDealerListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DealerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__full_name', 'user__phone_number', 'user__district__name']
    pagination_class = CustomPagination

    def get_queryset(self):
        # Get the logged-in user
        user = self.request.user
        # Retrieve the Franchisee associated with the logged-in user
        franchisee = get_object_or_404(Franchisee, user=user)
        
        # Retrieve sorting option from URL path; default to 'newest' if not specified
        sort_option = self.kwargs.get('sort_option', 'newest')

        # Apply sorting order based on the path parameter
        queryset = Dealer.objects.filter(franchisee=franchisee)
        
        # Check sort option and apply ordering accordingly
        if sort_option == 'oldest':
            queryset = queryset.order_by('craeted_date')
        else:  # Default to 'newest'
            queryset = queryset.order_by('-craeted_date')

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['franchisee'] = get_object_or_404(Franchisee, user=self.request.user)
        return context

# dealer detailview normal_id

# class FranchiseeDealerDetailView(APIView):
#     authentication_classes = [JWTAuthentication]  # Use JWT authentication
#     permission_classes = [IsAuthenticated]

#     def get(self, request, dealer_id):
#         # Get the logged-in user
#         user = request.user
#         # Retrieve the Franchisee associated with the logged-in user
#         franchisee = get_object_or_404(Franchisee, user=user)

#         # Retrieve the specific dealer based on the dealer ID and the associated franchisee
#         dealer = get_object_or_404(Dealer, id=dealer_id, franchisee=franchisee)

#         # Serialize dealer data
#         dealer_data = DealerSerializer(dealer)

#         return Response(dealer_data.data, status=status.HTTP_200_OK)

# dealer detailview custom_id

class FranchiseeDealerDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Validate request data
        serializer = CustomIDRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get the logged-in user
            user = request.user
            # Retrieve the Franchisee associated with the logged-in user
            franchisee = get_object_or_404(Franchisee, user=user)

            # Retrieve the specific dealer based on the custom ID and the associated franchisee
            dealer = get_object_or_404(
                Dealer, 
                custom_id=serializer.validated_data['custom_id'],
                franchisee=franchisee
            )

            # Serialize dealer data with request context for absolute URLs
            dealer_data = DealerSerializer(dealer, context={'request': request})

            return Response(dealer_data.data, status=status.HTTP_200_OK)

        except Dealer.DoesNotExist:
            return Response(
                {'error': 'Dealer not found or not associated with this franchisee'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class FranchiseeDealerCountView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        franchisee = get_object_or_404(Franchisee, user=user)

        # Count dealers associated with this franchisee
        total_dealers = Dealer.objects.filter(franchisee=franchisee).count()
        active_dealers = Dealer.objects.filter(franchisee=franchisee, status='Active').count()
        inactive_dealers = Dealer.objects.filter(franchisee=franchisee, status='Inactive').count()

        response_data = {
            'total_dealers': total_dealers,
            'active_dealers': active_dealers,
            'inactive_dealers': inactive_dealers,
        }

        return Response(response_data, status=status.HTTP_200_OK)

# add service

from .serializers import *
from rest_framework import generics, permissions

class FranchiseeServiceAddView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceRegisterSerializer

    def get_queryset(self):
        # Return all service registers or filter them as needed
        return ServiceRegister.objects.filter(service_provider__user=self.request.user)

    def get(self, request, *args, **kwargs):
        service_providers = ServiceProvider.objects.filter(user=request.user)
        serializer = self.serializer_class(service_providers, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        try:
            service_provider = ServiceProvider.objects.get(user=self.request.user)
            serializer.save(service_provider=service_provider)
        except ServiceProvider.DoesNotExist:
            return Response({'error': 'ServiceProvider does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# dealer create

from rest_framework import generics, status
from rest_framework.response import Response
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
# without file

# class DealerCreateView(generics.CreateAPIView):
#     serializer_class = AddDealerSerializer
#     permission_classes = [IsAuthenticated]

#     @transaction.atomic
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         # Create User first
#         user = User.objects.create(
#             email=serializer.validated_data.get('email'),
#             phone_number=serializer.validated_data['phone_number'],
#             full_name=serializer.validated_data['full_name'],
#             address=serializer.validated_data['address'],
#             pin_code=serializer.validated_data['pin_code'],
#             district=serializer.validated_data['district'],
#             state=serializer.validated_data['state'],
#             is_dealer=True  # Set the role flag
#         )
        
#         # Create Dealer
#         dealer = Dealer.objects.create(
#             user=user,
#             about=serializer.validated_data['about'],
#             profile_image=serializer.validated_data.get('profile_image'),
#             service_providers=serializer.validated_data.get('service_providers'),
#             franchisee=serializer.validated_data['franchisee'],
#             verification_id=serializer.validated_data.get('verification_id'),
#             verificationid_number=serializer.validated_data.get('verificationid_number'),
#             id_copy=serializer.validated_data.get('id_copy'),
#             status='Active'
#         )
        
#         return Response({
#             'message': 'Dealer created successfully',
#             'dealer_id': dealer.custom_id,
#             'user_id': user.id
#         }, status=status.HTTP_201_CREATED)

# with file
from django.db.utils import IntegrityError

class DealerCreateView(generics.CreateAPIView):
    serializer_class = AddDealerSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Create User first
            user = User.objects.create(
                email=serializer.validated_data.get('email'),
                phone_number=serializer.validated_data['phone_number'],
                full_name=serializer.validated_data['full_name'],
                address=serializer.validated_data['address'],
                landmark=serializer.validated_data['landmark'],
                pin_code=serializer.validated_data['pin_code'],
                district=serializer.validated_data['district'],
                state=serializer.validated_data['state'],
                watsapp=serializer.validated_data['watsapp'],
                country_code=serializer.validated_data['country_code'],
                is_dealer=True  # Set the role flag
            )

            # Create Dealer
            dealer = Dealer.objects.create(
                user=user,
                about=serializer.validated_data['about'],
                profile_image=serializer.validated_data.get('profile_image'),
                service_providers=serializer.validated_data.get('service_providers'),
                franchisee=serializer.validated_data['franchisee'],
                verification_id=serializer.validated_data.get('verification_id'),
                verificationid_number=serializer.validated_data.get('verificationid_number'),
                id_copy=serializer.validated_data.get('id_copy'),
                status='Active'
            )

            return Response({
                'message': 'Dealer created successfully',
                'dealer_id': dealer.custom_id,
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            if 'unique' in str(e):
                if 'email' in str(e):
                    return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
                elif 'phone_number' in str(e):
                    return Response({'error': 'Phone number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'An error occurred while creating the dealer.'}, status=status.HTTP_400_BAD_REQUEST)

# service provider create without file

# class ServiceProviderCreateView(generics.CreateAPIView):
#     serializer_class = AddServiceProviderSerializer
#     permission_classes = [IsAuthenticated]

#     @transaction.atomic
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         # Create User first
#         user = User.objects.create(
#             email=serializer.validated_data.get('email'),
#             phone_number=serializer.validated_data['phone_number'],
#             full_name=serializer.validated_data['full_name'],
#             address=serializer.validated_data['address'],
#             pin_code=serializer.validated_data['pin_code'],
#             district=serializer.validated_data['district'],
#             state=serializer.validated_data['state'],
#             is_service_provider=True  # Set the role flag
#         )
        
#         # Create ServiceProvider
#         service_provider = ServiceProvider.objects.create(
#             user=user,
#             about=serializer.validated_data.get('about'),
#             profile_image=serializer.validated_data.get('profile_image'),
#             date_of_birth=serializer.validated_data['date_of_birth'],
#             gender=serializer.validated_data['gender'],
#             dealer=serializer.validated_data['dealer'],
#             franchisee=serializer.validated_data['franchisee'],
#             address_proof_document=serializer.validated_data.get('address_proof_document'),
#             id_number=serializer.validated_data.get('id_number'),
#             address_proof_file=serializer.validated_data.get('address_proof_file'),
#             payout_required=serializer.validated_data['payout_required'],
#             status='Active',
#             verification_by_dealer='PENDING'
#         )
        
#         return Response({
#             'message': 'Service Provider created successfully',
#             'service_provider_id': service_provider.custom_id,
#             'user_id': user.id
#         }, status=status.HTTP_201_CREATED)


from django.db.utils import IntegrityError

class ServiceProviderCreateView(generics.CreateAPIView):
    serializer_class = AddServiceProviderSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Create User first
            user = User.objects.create(
                email=serializer.validated_data.get('email'),
                phone_number=serializer.validated_data['phone_number'],
                full_name=serializer.validated_data['full_name'],
                address=serializer.validated_data['address'],
                landmark=serializer.validated_data['landmark'],
                pin_code=serializer.validated_data['pin_code'],
                district=serializer.validated_data['district'],
                state=serializer.validated_data['state'],
                watsapp=serializer.validated_data['watsapp'],
                country_code=serializer.validated_data['country_code'],
                is_service_provider=True  # Set the role flag
            )

            # Create ServiceProvider
            service_provider = ServiceProvider.objects.create(
                user=user,
                about=serializer.validated_data.get('about'),
                profile_image=serializer.validated_data.get('profile_image'),
                date_of_birth=serializer.validated_data['date_of_birth'],
                gender=serializer.validated_data['gender'],
                dealer=serializer.validated_data['dealer'],
                franchisee=serializer.validated_data['franchisee'],
                address_proof_document=serializer.validated_data.get('address_proof_document'),
                id_number=serializer.validated_data.get('id_number'),
                address_proof_file=serializer.validated_data.get('address_proof_file'),
                payout_required=serializer.validated_data['payout_required'],
                status='Active',
                verification_by_dealer='PENDING',
                accepted_terms=serializer.validated_data['accepted_terms']
            )

            return Response({
                'message': 'Service Provider created successfully',
                'service_provider_id': service_provider.custom_id,
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            if 'unique' in str(e):
                if 'email' in str(e):
                    return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
                elif 'phone_number' in str(e):
                    return Response({'error': 'Phone number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'An error occurred while creating the service provider.'}, status=status.HTTP_400_BAD_REQUEST)



from rest_framework import generics
from Accounts.models import Country_Codes, State, District
from .serializers import CountryCodeSerializer, StateSerializer, DistrictSerializer

class CountryCodeListView(generics.ListAPIView):
    queryset = Country_Codes.objects.all()
    serializer_class = CountryCodeSerializer

class StateListView(generics.ListAPIView):
    queryset = State.objects.all()
    serializer_class = StateSerializer

class DistrictListView(generics.ListAPIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer


from rest_framework import generics
from Accounts.models import Category, Subcategory
from .serializers import CategorySerializer, SubcategorySerializer

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class SubcategoryListView(generics.ListAPIView):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer