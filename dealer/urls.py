from django.urls import include, path
from service_provider.views import ResetPasswordView
from rest_framework.routers import DefaultRouter
from .views import *
from . import views



urlpatterns = [

    path('login/', DealerLoginView.as_view(), name='dealer_login'),

#dealer home
    path('dealer/dashboard/', DealerDashboardView.as_view(), name='dealer-dashboard'),
    path('dealer-dashboard-count/', DealerDashboardServiceProviderCountsView.as_view(), name='dealer-dashboard'),
    path('dealer-serviceregister-count/', DealerServiceRegisterCountsView.as_view(), name='dealer-serviceregister-count/'),
    path('dealer/earnings/', DealerEarningsView.as_view(), name='dealer-earnings'),
    # path('recent-activities/', views.DealerRecentActivitiesView.as_view(), name='recent-activities'),
    path('recent-activities/', RecentActivitiesView.as_view(), name='recent-activities'),


    # path('dealer/recent-activities/', DealerRecentActivitiesView.as_view(), name='dealer-recent-activities'),
    path('dealer-payments/', DealerPaymentViewSet.as_view({'get': 'list'}), name='dealer-payment-list'),
    path('franchise-details/', FranchiseDetailsViewSet.as_view({'get': 'retrieve'}), name='franchise-details'),
    # path('dealer-payments/', DealerPaymentViewSet.as_view(), name='dealerpayment-list'), 

    path('service-providers/', DealerServiceProviderListView.as_view(), name='dealer-service-providers'),
    # path('search/', SearchAPIView.as_view(), name='search'),
    path('service-provider-counts/', DealerServiceProviderCountsView.as_view(), name='service-provider-counts'),
    path('pending-service-providers/', DealerServiceProviderPendingListView.as_view(), name='dealer-service-provider-list'),
    path('serviceproviders/approve/', UpdateServiceProviderStatusView.as_view(), name='approve-serviceprovider'),
    # path('serviceproviders/<int:id>/approve/', UpdateServiceProviderStatusView.as_view(), name='approve-serviceprovider'),
    path('service-provider-details/', DealerServiceProviderDetailView.as_view(), name='dealer-service-provider-detail'),
    # path('service-provider-details/<int:service_provider_id>/', DealerServiceProviderDetailView.as_view(), name='dealer-service-provider-detail'),

    path('payment-request/create/', PaymentRequestCreateView.as_view(), name='payment-request-create'),

]