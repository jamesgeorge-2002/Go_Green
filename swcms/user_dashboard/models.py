from django.db import models
from django.contrib.auth.models import User
import uuid

class Ward(models.Model):
    name = models.CharField(max_length=100)
    panchayat_municipality_choices = [
        ('meenichil', 'Meenichil'),
        ('kanjirapally', 'Kanjirapally'),
        ('kollam', 'Kollam'),
    ]
    panchayat_municipality = models.CharField(max_length=50, choices=panchayat_municipality_choices)
    ward_number = models.IntegerField()

    def __str__(self):
        return f"{self.name} ({self.panchayat_municipality}, Ward {self.ward_number})"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=50, choices=[
        ('user', 'User'),
        ('worker', 'Worker'),
        ('admin', 'Admin'),
    ], default='user')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class PickupRequest(models.Model):
    WASTE_TYPE_CHOICES = [
        ('wet', 'Wet Waste'),
        ('dry', 'Dry Waste'),
        ('plastic', 'Plastic Waste'),
        ('e-waste', 'E-waste'),
        ('recyclable', 'Recyclable Waste'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('picked', 'Picked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    request_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    waste_type = models.CharField(max_length=50, choices=WASTE_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='pickup_images/', blank=True, null=True)
    schedule_date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request {self.request_id} by {self.user.username} - {self.status}"

class Reward(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.points} points"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pickup_request = models.OneToOneField(PickupRequest, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.pickup_request} - {self.amount}"

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_complaint = models.BooleanField(default=False)
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
    ], default='pending')

    def __str__(self):
        return f"{self.subject} by {self.user.username} - {self.status}"
