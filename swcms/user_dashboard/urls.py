from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/user/', views.user_register_view, name='register_user'),
    path('register/worker/', views.worker_register_view, name='register_worker'),
    path('register/admin/', views.admin_register_view, name='register_admin'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('request-pickup/', views.request_pickup_view, name='request_pickup'),
    path('pickup/<int:pk>/', views.pickup_detail_view, name='pickup_detail'),
    path('payment/<int:pk>/', views.payment_view, name='payment'),
]
