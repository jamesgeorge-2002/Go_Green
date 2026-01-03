from django.contrib import admin
from .models import (
    Panchayath, Ward, Profile, PickupRequest, 
    Reward, Payment, Feedback
)

@admin.register(Panchayath)
class PanchayathAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at')
    fields = ('name', 'code', 'description', 'created_at', 'updated_at')

@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('name', 'panchayath', 'ward_number')
    list_filter = ('panchayath',)
    search_fields = ('name', 'panchayath__name')
    fields = ('name', 'panchayath', 'ward_number')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'ward', 'mobile_number')
    list_filter = ('role', 'ward')
    search_fields = ('user__username', 'mobile_number')

@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'user', 'waste_type', 'status', 'created_at')
    list_filter = ('status', 'waste_type', 'created_at')
    search_fields = ('request_id', 'user__username')
    readonly_fields = ('request_id', 'created_at', 'updated_at')

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'total_waste_collected')
    search_fields = ('user__username',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'pickup_request', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'razorpay_order_id')
    readonly_fields = ('created_at',)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'ward', 'status', 'is_complaint', 'created_at')
    list_filter = ('status', 'is_complaint', 'ward', 'created_at')
    search_fields = ('subject', 'user__username')
    readonly_fields = ('created_at',)
