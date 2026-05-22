from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('blood-directory/', views.blood_directory_view, name='blood_directory'),
    path('approve/<int:pk>/', views.approve_rover, name='approve_rover'),
    path('reject/<int:pk>/', views.reject_rover, name='reject_rover'),
    path('notices/', views.notice_list, name='notice_list'),
    path('notices/create/', views.notice_create, name='notice_create'),
    path('notices/<int:pk>/edit/', views.notice_edit, name='notice_edit'),
    path('notices/<int:pk>/delete/', views.notice_delete, name='notice_delete'),
    path('funds/', views.fundtransaction_list, name='fundtransaction_list'),
    # Fee management URLs
    path('fee-structure/', views.fee_structure_edit, name='fee_structure_edit'),
    path('rover-fees/', views.rover_fees_list, name='rover_fees_list'),
    path('rover-list/', views.rover_list_all, name='rover_list_all'),
    path('rover-fee/<int:fee_id>/mark-paid/', views.rover_fee_mark_paid, name='rover_fee_mark_paid'),
    path('my-fees/', views.my_fees, name='my_fees'),
    path('funds/add-fee/', views.add_rover_fee_view, name='add_rover_fee'),
    path('', views.home_view, name='home'),
]
