from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.user_register_view, name='register'),
    path('register/user/', views.user_register_view, name='register_user'),
    path('register/worker/', views.worker_register_view, name='register_worker'),
    path('register/admin/', views.admin_register_view, name='register_admin'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('request-pickup/', views.request_pickup_view, name='request_pickup'),
    path('pickup/<int:pk>/', views.pickup_detail_view, name='pickup_detail'),
    path('payment/<int:pk>/', views.payment_view, name='payment'),
    path('request-management/', views.request_management_view, name='request_management'),
    path('payment-management/', views.payment_management_view, name='payment_management'),
    path('cancel-request/<int:pk>/', views.cancel_request_view, name='cancel_request'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('feedback-management/', views.feedback_management_view, name='feedback_management'),
    path('resolve-feedback/<int:pk>/', views.resolve_feedback_view, name='resolve_feedback'),
    path('worker-dashboard/', views.worker_dashboard_view, name='worker_dashboard'),
    path('mark-picked/<int:pk>/', views.mark_picked_view, name='mark_picked'),
    path('mark-completed/<int:pk>/', views.mark_completed_view, name='mark_completed'),
    path('collect-cash/<int:pk>/', views.collect_cash_view, name='collect_cash'),
    path('print-receipt/<int:pk>/', views.print_receipt_view, name='print_receipt'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-users/', views.admin_users_view, name='admin_users'),
    path('admin-feedbacks/', views.admin_feedbacks_view, name='admin_feedbacks'),
    path('admin-wards/', views.admin_wards_view, name='admin_wards'),
    path('admin-rewards/', views.admin_rewards_view, name='admin_rewards'),
    path('admin-mark-picked/<int:pk>/', views.admin_mark_picked_view, name='admin_mark_picked'),
    path('admin-mark-completed/<int:pk>/', views.admin_mark_completed_view, name='admin_mark_completed'),
    path('admin-resolve-feedback/<int:pk>/', views.admin_resolve_feedback_view, name='admin_resolve_feedback'),
    path('admin-update-role/<int:pk>/', views.admin_update_role_view, name='admin_update_role'),
    path('admin-allocate-ward/<int:pk>/', views.admin_allocate_ward_view, name='admin_allocate_ward'),
    path('admin-respond-feedback/<int:pk>/', views.admin_respond_feedback_view, name='admin_respond_feedback'),
    path('admin-add-user/', views.admin_add_user_view, name='admin_add_user'),
    path('admin-add-worker/', views.admin_add_worker_view, name='admin_add_worker'),
    path('admin-delete-user/<int:pk>/', views.admin_delete_user_view, name='admin_delete_user'),
    path('admin-give-reward-least-waste/', views.admin_give_reward_to_least_waste_view, name='admin_give_reward_least_waste'),
    path('admin-panchayath/', views.admin_panchayath_view, name='admin_panchayath'),
    path('admin-panchayath/add/', views.admin_add_panchayath_view, name='admin_add_panchayath'),
    path('admin-panchayath/<int:pk>/edit/', views.admin_edit_panchayath_view, name='admin_edit_panchayath'),
    path('admin-panchayath/<int:pk>/delete/', views.admin_delete_panchayath_view, name='admin_delete_panchayath'),
    path('admin-wards-management/', views.admin_wards_management_view, name='admin_wards_management'),
    path('admin-wards/add/', views.admin_add_ward_view, name='admin_add_ward'),
    path('admin-wards/<int:pk>/edit/', views.admin_edit_ward_view, name='admin_edit_ward'),
    path('admin-wards/<int:pk>/delete/', views.admin_delete_ward_view, name='admin_delete_ward'),
    # Password reset (using Django built-in auth views with app templates)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='user_dashboard/password_reset_form.html',
        email_template_name='user_dashboard/password_reset_email.html',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='user_dashboard/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='user_dashboard/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='user_dashboard/password_reset_complete.html'
    ), name='password_reset_complete'),
]
