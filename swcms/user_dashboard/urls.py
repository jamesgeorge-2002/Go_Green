from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.user_register_view, name='register'),
    path('register/user/', views.user_register_view, name='register_user'),
    path('register/worker/', views.worker_register_view, name='register_worker'),
    path('register/admin/', views.admin_register_view, name='register_admin'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('request-pickup/', views.request_pickup_view, name='request_pickup'),
    path('pickup/<int:pk>/', views.pickup_detail_view, name='pickup_detail'),
    path('payment/<int:pk>/', views.payment_view, name='payment'),
    path('request-management/', views.request_management_view, name='request_management'),
    path('cancel-request/<int:pk>/', views.cancel_request_view, name='cancel_request'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('feedback-management/', views.feedback_management_view, name='feedback_management'),
    path('resolve-feedback/<int:pk>/', views.resolve_feedback_view, name='resolve_feedback'),
    path('worker-dashboard/', views.worker_dashboard_view, name='worker_dashboard'),
    path('mark-picked/<int:pk>/', views.mark_picked_view, name='mark_picked'),
    path('mark-completed/<int:pk>/', views.mark_completed_view, name='mark_completed'),
]
