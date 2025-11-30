from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, WorkerRegistrationForm, AdminRegistrationForm, LoginForm, PickupRequestForm, FeedbackForm
from .models import PickupRequest, Reward, Profile, Ward, Payment, Feedback

@login_required
def index(request):
    user = request.user
    reward_points = Reward.objects.get(user=user).points if Reward.objects.filter(user=user).exists() else 0
    upcoming_pickups = PickupRequest.objects.filter(user=user, schedule_date_time__gte=timezone.now(), status__in=['pending', 'picked']).order_by('schedule_date_time')
    previous_pickups = PickupRequest.objects.filter(user=user, schedule_date_time__lt=timezone.now()).order_by('-schedule_date_time')[:5]
    total_pickups = PickupRequest.objects.filter(user=user, status='completed').count()

    context = {
        'reward_points': reward_points,
        'upcoming_pickups': upcoming_pickups,
        'previous_pickups': previous_pickups,
        'total_pickups': total_pickups,
    }
    return render(request, 'user_dashboard/index.html', context)

def user_register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role='user')
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'user_dashboard/register.html', {'form': form})

def worker_register_view(request):
    if request.method == 'POST':
        form = WorkerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            ward = form.cleaned_data.get('ward')
            if ward:
                Profile.objects.create(user=user, role='worker', ward=ward)
                messages.success(request, 'Registration successful. Please log in.')
                return redirect('login')
            else:
                form.add_error('ward', 'This field is required.')
    else:
        form = WorkerRegistrationForm()
    return render(request, 'user_dashboard/register.html', {'form': form})

def admin_register_view(request):
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role='admin')
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = AdminRegistrationForm()
    return render(request, 'user_dashboard/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect based on role
                try:
                    profile = Profile.objects.get(user=user)
                    if profile.role == 'admin':
                        return redirect('admin_dashboard')
                    elif profile.role == 'worker':
                        return redirect('worker_dashboard')
                    else:
                        return redirect('index')
                except Profile.DoesNotExist:
                    return redirect('index')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()
    return render(request, 'user_dashboard/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def request_pickup_view(request):
    if request.method == 'POST':
        form = PickupRequestForm(request.POST, request.FILES)
        if form.is_valid():
            pickup = form.save(commit=False)
            pickup.user = request.user
            pickup.save()
            messages.success(request, 'Pickup request submitted successfully.')
            return redirect('index')
    else:
        form = PickupRequestForm()
    return render(request, 'user_dashboard/request_pickup.html', {'form': form})

@login_required
def pickup_detail_view(request, pk):
    pickup = get_object_or_404(PickupRequest, pk=pk, user=request.user)
    return render(request, 'user_dashboard/pickup_detail.html', {'pickup': pickup})

@login_required
def payment_view(request, pk):
    pickup = get_object_or_404(PickupRequest, pk=pk, user=request.user)
    # Assuming payment logic here, for now just render
    return render(request, 'user_dashboard/payment.html', {'pickup': pickup})

@login_required
def request_management_view(request):
    pickups = PickupRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'user_dashboard/request_management.html', {'pickups': pickups})

@login_required
def cancel_request_view(request, pk):
    pickup = get_object_or_404(PickupRequest, pk=pk, user=request.user)
    if pickup.status == 'pending':
        pickup.status = 'cancelled'
        pickup.save()
        messages.success(request, 'Request cancelled.')
    else:
        messages.error(request, 'Cannot cancel this request.')
    return redirect('request_management')

@login_required
def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, 'Feedback submitted.')
            return redirect('index')
    else:
        form = FeedbackForm()
    return render(request, 'user_dashboard/feedback.html', {'form': form})

@login_required
def feedback_management_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role not in ['admin', 'worker']:
        messages.error(request, "Access denied.")
        return redirect('index')

    feedbacks = Feedback.objects.filter(ward=user_profile.ward).order_by('-created_at') if user_profile.role == 'worker' else Feedback.objects.all().order_by('-created_at')
    return render(request, 'user_dashboard/feedback_management.html', {'feedbacks': feedbacks})

@login_required
def resolve_feedback_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role not in ['admin', 'worker']:
        messages.error(request, "Access denied.")
        return redirect('index')

    feedback = get_object_or_404(Feedback, pk=pk, ward=user_profile.ward) if user_profile.role == 'worker' else get_object_or_404(Feedback, pk=pk)
    if feedback.status == 'pending':
        feedback.status = 'resolved'
        feedback.save()
        messages.success(request, "Feedback resolved.")
    else:
        messages.error(request, "Cannot resolve this feedback.")
    return redirect('feedback_management')

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

@login_required
def admin_dashboard_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    users = User.objects.filter(profile__isnull=False)
    pickups = PickupRequest.objects.all().order_by('-created_at')
    feedbacks = Feedback.objects.all().order_by('-created_at')
    payments = Payment.objects.all().order_by('-created_at')
    wards = Ward.objects.all()
    rewards = Reward.objects.all()

    total_users = users.count()
    total_pickups = pickups.count()
    pending_pickups = pickups.filter(status='pending').count()
    completed_pickups = pickups.filter(status='completed').count()
    total_feedbacks = feedbacks.count()
    pending_feedbacks = feedbacks.filter(status='pending').count()
    total_payments = payments.count()

    context = {
        'users': users,
        'pickups': pickups,
        'feedbacks': feedbacks,
        'payments': payments,
        'wards': wards,
        'rewards': rewards,
        'total_users': total_users,
        'total_pickups': total_pickups,
        'pending_pickups': pending_pickups,
        'completed_pickups': completed_pickups,
        'total_feedbacks': total_feedbacks,
        'pending_feedbacks': pending_feedbacks,
        'total_payments': total_payments,
    }
    return render(request, 'user_dashboard/admin_dashboard.html', context)

@login_required
def admin_mark_picked_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    pickup = get_object_or_404(PickupRequest, pk=pk)
    if pickup.status == 'pending':
        pickup.status = 'picked'
        pickup.save()
        messages.success(request, "Pickup marked as picked.")
    else:
        messages.error(request, "Cannot mark this pickup as picked.")
    return redirect('admin_dashboard')

@login_required
def admin_mark_completed_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    pickup = get_object_or_404(PickupRequest, pk=pk)
    if pickup.status == 'picked':
        pickup.status = 'completed'
        pickup.save()
        messages.success(request, "Pickup marked as completed.")
    else:
        messages.error(request, "Cannot mark this pickup as completed.")
    return redirect('admin_dashboard')

@login_required
def admin_resolve_feedback_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    feedback = get_object_or_404(Feedback, pk=pk)
    if feedback.status == 'pending':
        feedback.status = 'resolved'
        feedback.save()
        messages.success(request, "Feedback marked as resolved.")
    else:
        messages.error(request, "Cannot resolve this feedback.")
    return redirect('admin_dashboard')

@login_required
def admin_update_role_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ['user', 'worker', 'admin']:
            profile = get_object_or_404(Profile, pk=pk)
            profile.role = new_role
            profile.save()
            messages.success(request, f"Role updated to {new_role}.")
        else:
            messages.error(request, "Invalid role.")
    return redirect('admin_dashboard')

@login_required
def admin_allocate_ward_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    if request.method == 'POST':
        ward_id = request.POST.get('ward')
        if ward_id:
            ward = get_object_or_404(Ward, pk=ward_id)
            profile = get_object_or_404(Profile, pk=pk)
            profile.ward = ward
            profile.save()
            messages.success(request, f"Ward allocated to {profile.user.username}.")
        else:
            messages.error(request, "Invalid ward.")
    return redirect('admin_dashboard')

@login_required
def admin_respond_feedback_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    feedback = get_object_or_404(Feedback, pk=pk)
    if request.method == 'POST':
        response = request.POST.get('response')
        if response:
            feedback.response = response
            feedback.status = 'resolved'
            feedback.save()
            messages.success(request, "Feedback responded and resolved.")
        else:
            messages.error(request, "Response cannot be empty.")
    return redirect('admin_dashboard')

@login_required
def admin_add_user_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role='user')
            messages.success(request, 'User added successfully.')
            return redirect('admin_dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'user_dashboard/admin_add_user.html', {'form': form})

@login_required
def admin_add_worker_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    if request.method == 'POST':
        form = WorkerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            ward = form.cleaned_data.get('ward')
            if ward:
                Profile.objects.create(user=user, role='worker', ward=ward)
                messages.success(request, 'Worker added successfully.')
                return redirect('admin_dashboard')
            else:
                form.add_error('ward', 'This field is required.')
    else:
        form = WorkerRegistrationForm()
    return render(request, 'user_dashboard/admin_add_worker.html', {'form': form})
