from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile, PickupRequest, Ward, Panchayath, Reward, Feedback
from datetime import datetime

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    mobile_number = forms.CharField(max_length=15, required=False)
    location = forms.CharField(max_length=255)
    panchayath = forms.ModelChoiceField(queryset=Panchayath.objects.all(), label="Select Panchayath")
    ward = forms.ModelChoiceField(queryset=Ward.objects.all(), required=True, label="Select Ward")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")

        email = cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            self.add_error('email', "This email is already registered.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            ward = self.cleaned_data.get('ward')
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'mobile_number': self.cleaned_data.get('mobile_number'),
                    'location': self.cleaned_data.get('location'),
                    'ward': ward,
                    'role': 'user'
                }
            )
            Reward.objects.get_or_create(user=user, defaults={'points': 0})
        return user

class WorkerRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    mobile_number = forms.CharField(max_length=15, required=False)
    location = forms.CharField(max_length=255)
    panchayath = forms.ModelChoiceField(queryset=Panchayath.objects.all(), label="Select Panchayath")
    ward = forms.ModelChoiceField(queryset=Ward.objects.all(), required=True, label="Select Ward")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")

        email = cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            self.add_error('email', "This email is already registered.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            ward = self.cleaned_data.get('ward')
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'mobile_number': self.cleaned_data.get('mobile_number'),
                    'location': self.cleaned_data.get('location'),
                    'ward': ward,
                    'role': 'worker'
                }
            )
        return user

class AdminRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    mobile_number = forms.CharField(max_length=15, required=False)
    location = forms.CharField(max_length=255)
    panchayath = forms.ModelChoiceField(queryset=Panchayath.objects.all(), label="Select Panchayath")
    ward = forms.ModelChoiceField(queryset=Ward.objects.all(), required=True, label="Select Ward")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")

        email = cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            self.add_error('email', "This email is already registered.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            ward = self.cleaned_data.get('ward')
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'mobile_number': self.cleaned_data.get('mobile_number'),
                    'location': self.cleaned_data.get('location'),
                    'ward': ward,
                    'role': 'admin'
                }
            )
        return user

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class PickupRequestForm(forms.ModelForm):
    schedule_date_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        label="Schedule Date and Time"
    )

    class Meta:
        model = PickupRequest
        fields = ['waste_type', 'description', 'image', 'schedule_date_time']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_schedule_date_time(self):
        schedule_date_time = self.cleaned_data.get('schedule_date_time')
        if schedule_date_time:
            from django.utils import timezone
            now = timezone.now()
            if schedule_date_time.date() < now.date():
                raise ValidationError("Schedule date must be today or in the future.")
        return schedule_date_time

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent form classes for templates
        self.fields['waste_type'].widget.attrs.update({'class': 'form-select form-control'})
        self.fields['schedule_date_time'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        # File input
        if 'image' in self.fields:
            self.fields['image'].widget.attrs.update({'class': 'form-control'})

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['subject', 'message', 'is_complaint']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

class WasteWeightForm(forms.Form):
    waste_weight = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        help_text="Enter weight in kg",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'})
    )
class UserProfileEditForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False, label="First Name")
    last_name = forms.CharField(max_length=150, required=False, label="Last Name")

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['mobile_number', 'location', 'ward']
        widgets = {
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'ward': forms.Select(attrs={'class': 'form-select'}),
        }