from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.db import transaction
from decimal import Decimal
from collections import defaultdict
from .forms import UserRegistrationForm, WorkerRegistrationForm, AdminRegistrationForm, LoginForm, PickupRequestForm, FeedbackForm, WasteWeightForm
from .models import PickupRequest, Reward, Profile, Ward, Payment, Feedback

# Decorator for role-based access
def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            try:
                profile = Profile.objects.get(user=request.user)
                if profile.role not in allowed_roles:
                    messages.error(request, "Access denied. You don't have permission to access this page.")
                    return redirect('index')
            except Profile.DoesNotExist:
                messages.error(request, "Profile not found. Please contact administrator.")
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

@login_required
def index(request):
    try:
        user = request.user
        profile = Profile.objects.get(user=user)
        
        # Only users should access this page
        if profile.role != 'user':
            if profile.role == 'admin':
                return redirect('admin_dashboard')
            elif profile.role == 'worker':
                return redirect('worker_dashboard')
        
        reward, created = Reward.objects.get_or_create(user=user)
        reward_points = reward.points
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
    except Profile.DoesNotExist:
        messages.error(request, "Profile not found. Please contact administrator.")
        return redirect('login')

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
            # Profile and ward are created inside the form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = WorkerRegistrationForm()
    return render(request, 'user_dashboard/register.html', {'form': form})

def admin_register_view(request):
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile and ward are created inside the form.save()
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

def _recalculate_user_rewards():
    """
    Recalculate reward points automatically based on total waste generated
    and its environmental impact. Users with less and less-harmful waste
    receive higher scores. Only users with role='user' are ranked.
    """
    # Weight multipliers per waste type (higher = more harmful)
    weight_factors = {
        'wet': Decimal('1.0'),
        'dry': Decimal('1.0'),
        'recyclable': Decimal('0.5'),
        'plastic': Decimal('2.0'),
        'e-waste': Decimal('3.0'),
    }

    impact_map = defaultdict(lambda: {'total_kg': Decimal('0'), 'impact': Decimal('0')})

    completed = (
        PickupRequest.objects
        .filter(status='completed')
        .select_related('user')
        .only('user_id', 'waste_type', 'waste_weight')
    )

    for p in completed:
        if p.waste_weight is None:
            continue
        if not hasattr(p, 'user') or p.user is None:
            continue
        weight = Decimal(str(p.waste_weight))
        factor = weight_factors.get(p.waste_type, Decimal('1.0'))
        impact_map[p.user]['total_kg'] += weight
        impact_map[p.user]['impact'] += weight * factor

    # Ensure all users with role 'user' exist in the map (even if zero waste)
    for profile in Profile.objects.select_related('user').filter(role='user'):
        _ = impact_map[profile.user]  # initialize default if missing

    users_impacts = list(impact_map.items())
    if not users_impacts:
        return

    # Sort by impact ascending (less impact = better)
    users_impacts.sort(key=lambda item: (item[1]['impact'], item[0].id))
    n = len(users_impacts)
    max_points = Decimal('100')
    min_points = Decimal('10')

    for idx, (user, data) in enumerate(users_impacts):
        # Linear scale: best user gets max_points, worst gets min_points
        if n == 1:
            points = max_points
        else:
            # rank 0 => best
            ratio = Decimal(n - 1 - idx) / Decimal(n - 1)  # 1.0 .. 0.0
            points = min_points + (max_points - min_points) * ratio
        reward, _ = Reward.objects.get_or_create(
            user=user,
            defaults={'points': 0, 'total_waste_collected': Decimal('0')},
        )
        reward.total_waste_collected = data['total_kg']
        reward.points = int(points)
        reward.save()

@login_required
@role_required(['worker'])
def mark_completed_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'worker':
        messages.error(request, "Access denied.")
        return redirect('index')

    pickup = get_object_or_404(PickupRequest, pk=pk, user__profile__ward=user_profile.ward)

    if request.method == 'POST':
        form = WasteWeightForm(request.POST)
        if form.is_valid():
            waste_weight = form.cleaned_data['waste_weight']
            if pickup.status == 'picked':
                pickup.status = 'completed'
                pickup.waste_weight = waste_weight
                pickup.save()

                # Automatically recalculate rewards for all users
                _recalculate_user_rewards()
                messages.success(
                    request,
                    "Pickup marked as completed. Reward points have been recalculated based on total waste and its impact."
                )
            else:
                messages.error(request, "Cannot mark this pickup as completed.")
            return redirect('worker_dashboard')
    else:
        form = WasteWeightForm()

    return render(request, 'user_dashboard/enter_weight.html', {'pickup': pickup, 'form': form})

@login_required
def admin_dashboard_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    users = User.objects.filter(profile__isnull=False)
    pickups = PickupRequest.objects.all()
    feedbacks = Feedback.objects.all()
    payments = Payment.objects.all()

    total_users = users.count()
    total_pickups = pickups.count()
    pending_pickups = pickups.filter(status='pending').count()
    completed_pickups = pickups.filter(status='completed').count()
    total_feedbacks = feedbacks.count()
    pending_feedbacks = feedbacks.filter(status='pending').count()
    total_payments = payments.count()

    context = {
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
@role_required(['admin'])
def admin_users_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    users = User.objects.filter(profile__isnull=False)
    wards = Ward.objects.all()

    context = {
        'users': users,
        'wards': wards,
    }
    return render(request, 'user_dashboard/admin_users.html', context)

@login_required
@role_required(['admin'])
def admin_feedbacks_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    feedbacks = Feedback.objects.all().order_by('-created_at')

    context = {
        'feedbacks': feedbacks,
    }
    return render(request, 'user_dashboard/admin_feedbacks.html', context)

@login_required
@role_required(['admin'])
def admin_wards_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    wards = Ward.objects.all()

    context = {
        'wards': wards,
    }
    return render(request, 'user_dashboard/admin_wards.html', context)

@login_required
@role_required(['admin'])
def admin_rewards_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied. Only admins can view this page.")
        return redirect('index')

    rewards = Reward.objects.filter(user__profile__role='user').order_by('-points')
    user_with_least_waste = rewards.order_by('total_waste_collected').first()

    context = {
        'rewards': rewards,
        'user_with_least_waste': user_with_least_waste,
    }
    return render(request, 'user_dashboard/admin_rewards.html', context)

@login_required
@role_required(['admin'])
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
    return redirect('admin_users')

@login_required
@role_required(['admin'])
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
    return redirect('admin_users')

@login_required
@role_required(['admin'])
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
    return redirect('admin_feedbacks')

@login_required
@role_required(['admin'])
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
    return redirect('admin_users')

@login_required
@role_required(['admin'])
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
    return redirect('admin_users')

@login_required
@role_required(['admin'])
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
    return redirect('admin_feedbacks')

@login_required
@role_required(['admin'])
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
            return redirect('admin_users')
    else:
        form = UserRegistrationForm()
    return render(request, 'user_dashboard/admin_add_user.html', {'form': form})

@login_required
@role_required(['admin'])
def admin_add_worker_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')

    if request.method == 'POST':
        form = WorkerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile and ward are created inside the form.save()
            messages.success(request, 'Worker added successfully.')
            return redirect('admin_users')
    else:
        form = WorkerRegistrationForm()
    return render(request, 'user_dashboard/admin_add_worker.html', {'form': form})

@login_required
@role_required(['admin'])
def admin_delete_user_view(request, pk):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')
    
    user_to_delete = get_object_or_404(User, pk=pk)
    
    # Prevent admin from deleting themselves
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('admin_users')
    
    if request.method == 'POST':
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f"User {username} has been deleted successfully.")
        return redirect('admin_users')
    
    return render(request, 'user_dashboard/confirm_delete_user.html', {'user_to_delete': user_to_delete})

@login_required
@role_required(['admin'])
def admin_give_reward_to_least_waste_view(request):
    user_profile = Profile.objects.get(user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('index')
    
    # Find user with least waste collected
    user_reward = Reward.objects.filter(user__profile__role='user').order_by('total_waste_collected').first()
    
    if user_reward:
        # Give bonus points (e.g., 50 points)
        bonus_points = 50
        user_reward.points += bonus_points
        user_reward.save()
        messages.success(request, f"Bonus reward of {bonus_points} points given to {user_reward.user.username} (least waste collected: {user_reward.total_waste_collected} kg).")
    else:
        messages.error(request, "No users found to give reward.")
    
    return redirect('admin_rewards')
