from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import UserRegistrationForm, WorkerRegistrationForm, AdminRegistrationForm, LoginForm, PickupRequestForm
from .models import PickupRequest, Reward, Profile, Ward, Payment

def user_register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    return render(request, 'user_dashboard/register_user.html', {'form': form})

def worker_register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = WorkerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = WorkerRegistrationForm()
    return render(request, 'user_dashboard/register_worker.html', {'form': form})

def admin_register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AdminRegistrationForm()
    return render(request, 'user_dashboard/register_admin.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome, {user.username}!")
                return redirect('index')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = LoginForm()
    return render(request, 'user_dashboard/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def index(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    upcoming_pickups = PickupRequest.objects.filter(user=request.user, status='pending', schedule_date_time__gte=timezone.now()).order_by('schedule_date_time')
    previous_pickups = PickupRequest.objects.filter(user=request.user).exclude(status='pending').order_by('-schedule_date_time')
    reward, created = Reward.objects.get_or_create(user=request.user)

    context = {
        'user_profile': user_profile,
        'upcoming_pickups': upcoming_pickups,
        'previous_pickups': previous_pickups,
        'reward_points': reward.points,
    }
    return render(request, 'user_dashboard/index.html', context)

@login_required
def request_pickup_view(request):
    if request.method == 'POST':
        form = PickupRequestForm(request.POST, request.FILES)
        if form.is_valid():
            pickup_request = form.save(commit=False)
            pickup_request.user = request.user
            pickup_request.save()
            messages.success(request, f"Pickup request {pickup_request.request_id.hex[:8]} submitted successfully!")
            return redirect('pickup_detail', pk=pickup_request.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PickupRequestForm()
    return render(request, 'user_dashboard/request_pickup.html', {'form': form})

@login_required
def pickup_detail_view(request, pk):
    pickup = get_object_or_404(PickupRequest, pk=pk, user=request.user)
    payment = None
    if hasattr(pickup, 'payment'):
        payment = pickup.payment
    return render(request, 'user_dashboard/pickup_detail.html', {'pickup': pickup, 'payment': payment})

@login_required
def payment_view(request, pk):
    pickup = get_object_or_404(PickupRequest, pk=pk, user=request.user)
    if pickup.status != 'completed':
        messages.error(request, "Payment can only be made for completed pickups.")
        return redirect('pickup_detail', pk=pk)

    payment, created = Payment.objects.get_or_create(
        pickup_request=pickup,
        defaults={
            'user': request.user,
            'amount': 100.00  # Fixed amount for now, can be dynamic
        }
    )

    if payment.status == 'completed':
        messages.info(request, "Payment already completed.")
        return redirect('pickup_detail', pk=pk)

    if request.method == 'POST':
        # Handle payment success callback
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        # Verify payment (simplified, in production use Razorpay's verify method)
        if razorpay_payment_id and razorpay_order_id:
            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = 'completed'
            payment.save()
            messages.success(request, "Payment successful!")
            return redirect('pickup_detail', pk=pk)
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, "Payment failed.")
            return redirect('pickup_detail', pk=pk)

    # Create Razorpay order
    import razorpay
    from django.conf import settings
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order_data = {
        'amount': int(payment.amount * 100),  # Amount in paisa
        'currency': 'INR',
        'payment_capture': '1'
    }
    order = client.order.create(data=order_data)
    payment.razorpay_order_id = order['id']
    payment.save()

    context = {
        'pickup': pickup,
        'payment': payment,
        'order_id': order['id'],
        'amount': payment.amount,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'user_dashboard/payment.html', context)
