from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import *
from . import views



urlpatterns = [

    path('login/', FranchiseeLoginView.as_view(), name='franchise-login'),

    path('franchise-dashboardcount/', views.FranchiseDashboardCountsView.as_view(), name='franchise-dashboardcount'),
    path('franchise-dashboardcount-service/', views.FranchiseeServiceRegisterCountsView.as_view(), name='franchise-dashboardcount-service'),
    path('franchise-dashboardcount-complaints/', views.FranchiseComplaintsCountView.as_view(), name='franchise-dashboardcount-complaints'),
    path('franchise-dashboardcount-ads/', views.FranchiseAdsCountView.as_view(), name='franchise-dashboardcount-ads'),
    # path('franchise-dashboardcount-earnings/', views.FranchiseCommissionViewSet.as_view(), name='franchise-dashboardcount-earnings'),
    path('franchise-dashboardcount-earnings/total_earnings/', views.FranchiseEarningsView.as_view(), name='franchise-dashboardcount-earnings'),

    path('franchise/details/', views.FranchiseDetailsView.as_view(), name='franchise-details'),
    path('franchise/recent-activities/', views.RecentActivitiesView.as_view(), name='franchise-recent-activities'),
    path('franchise/incomplete-bookings/', views.IncompleteBookingsView.as_view(), name='franchise-incomplete-bookings'),
    path('franchise/complaints/', views.ComplaintsView.as_view(), name='franchise-complaints'),
    path('franchisee/payments/', FranchiseePaymentView.as_view(), name='franchisee-payments'),

    path('service-providers/', FranchiseeServiceProviderListView.as_view(), name='franchise-service-providers'),
    # path('service-providers/<str:sort_option>/', FranchiseeServiceProviderListView.as_view(), name='franchise-service-providers'),
    path('service-provider-counts/', FranchiseeServiceProviderCountsView.as_view(), name='franchisee-service-provider-counts'),

    #post
    path('service-provider-details/', FranchiseeServiceProviderDetailView.as_view(), name='franchisee-service-provider-detail'),
    # path('service-provider-details/<int:service_provider_id>/', FranchiseeServiceProviderDetailView.as_view(), name='franchisee-service-provider-detail'),
    path('service-provider/payments/', FranchiseeServiceProviderPaymentView.as_view(), name='service-provider-payments'),
    # path('service-provider/<int:service_provider_id>/payments/', FranchiseeServiceProviderPaymentView.as_view()),


    path('franchise/franchisee-dealers/', FranchiseeDealerListView.as_view(), name='franchisee-dealer-list'),
    path('franchise/franchisee-dealers/<str:sort_option>/', FranchiseeDealerListView.as_view(), name='franchisee-dealer-list-sorted'),
    path('franchisee-dealers-details/', FranchiseeDealerDetailView.as_view(), name='franchisee-dealer-detail'),

    path('country-codes/', views.CountryCodeListView.as_view(), name='country-code-list'),
    path('states/', views.StateListView.as_view(), name='state-list'),
    path('districts/', views.DistrictListView.as_view(), name='district-list'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('subcategories/', views.SubcategoryListView.as_view(), name='subcategory-list'),

    # path('franchisee-dealers-details/<int:dealer_id>/', FranchiseeDealerDetailView.as_view(), name='franchisee-dealer-detail'),
    path('franchisee-dealer-count/', FranchiseeDealerCountView.as_view(), name='franchisee-dealer-count'),
    path('franchisee/service/add/', FranchiseeServiceAddView.as_view(), name='franchisee-service-add'),

    path('dealers/create/', DealerCreateView.as_view(), name='dealer-create'),
    path('service-providers/create/', ServiceProviderCreateView.as_view(), name='service-provider-create'),






    # path('franchise-service-providers/', FranchiseServiceProviderListView.as_view(), name='franchise-service-provider-list'),
    # path('create-sp/', ServiceProviderCreateView.as_view(), name='service-provider-create'),
    # path('add-service-provider/', AddServiceProviderView.as_view(), name='add_service_provider'),

    



]