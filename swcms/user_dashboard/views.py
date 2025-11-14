from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import UserRegistrationForm, WorkerRegistrationForm, AdminRegistrationForm, LoginForm, PickupRequestForm, FeedbackForm
from .models import PickupRequest, Reward, Profile, Ward, Payment, Feedback

@login_required
def worker_dashboard_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'worker':
        messages.error(request, "Access denied. Only workers can view this page.")
        return redirect('index')

    # Filter pickups by worker's ward
    pickups = PickupRequest.objects.filter(user__profile__ward=user_profile.ward).order_by('-created_at')

    pending_pickups = pickups.filter(status='pending')
    picked_pickups = pickups.filter(status='picked')
    completed_pickups = pickups.filter(status='completed')

    # Filter feedbacks by worker's ward
    feedbacks = Feedback.objects.filter(ward=user_profile.ward).order_by('-created_at')
    pending_feedbacks = feedbacks.filter(status='pending')
    resolved_feedbacks = feedbacks.filter(status='resolved')

    context = {
        'pending_pickups': pending_pickups,
        'picked_pickups': picked_pickups,
        'completed_pickups': completed_pickups,
        'pending_feedbacks': pending_feedbacks,
        'resolved_feedbacks': resolved_feedbacks,
    }
    return render(request, 'user_dashboard/worker_dashboard.html', context)

@login_required
def mark_picked_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'worker':
        messages.error(request, "Access denied.")
        return redirect('index')

    pickup = get_object_or_404(PickupRequest, pk=pk, user__profile__ward=user_profile.ward)
    if pickup.status == 'pending':
        pickup.status = 'picked'
        pickup.save()
        messages.success(request, "Pickup marked as picked.")
    else:
        messages.error(request, "Cannot mark this pickup as picked.")
    return redirect('worker_dashboard')

@login_required
def mark_completed_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'worker':
        messages.error(request, "Access denied.")
        return redirect('index')

    pickup = get_object_or_404(PickupRequest, pk=pk, user__profile__ward=user_profile.ward)
    if pickup.status == 'picked':
        pickup.status = 'completed'
        pickup.save()
        messages.success(request, "Pickup marked as completed.")
    else:
        messages.error(request, "Cannot mark this pickup as completed.")
    return redirect('worker_dashboard')
