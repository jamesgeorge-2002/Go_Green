from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile, PickupRequest, Ward
from datetime import datetime

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    mobile_number = forms.CharField(max_length=15, required=False)
    location = forms.CharField(max_length=255)
    panchayat_municipality = forms.ChoiceField(choices=Ward.panchayat_municipality_choices)
    ward_name = forms.CharField(max_length=100)
    ward_number = forms.IntegerField()

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
            # Create or get Ward
            panchayat_municipality = self.cleaned_data.get('panchayat_municipality')
            ward_name = self.cleaned_data.get('ward_name')
            ward_number = self.cleaned_data.get('ward_number')
            ward, created = Ward.objects.get_or_create(
                name=ward_name,
                panchayat_municipality=panchayat_municipality,
                ward_number=ward_number
            )
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
    panchayat_municipality = forms.ChoiceField(choices=Ward.panchayat_municipality_choices)
    ward_name = forms.CharField(max_length=100)
    ward_number = forms.IntegerField()

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
            # Create or get Ward
            panchayat_municipality = self.cleaned_data.get('panchayat_municipality')
            ward_name = self.cleaned_data.get('ward_name')
            ward_number = self.cleaned_data.get('ward_number')
            ward, created = Ward.objects.get_or_create(
                name=ward_name,
                panchayat_municipality=panchayat_municipality,
                ward_number=ward_number
            )
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'mobile_number': self.cleaned_data.get('mobile_number'),
                    'location': self.cleaned_data.get('location'),
                    'ward': ward,
                    'role': 'worker'
                }
            )
            Reward.objects.get_or_create(user=user, defaults={'points': 0})
        return user

class AdminRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    mobile_number = forms.CharField(max_length=15, required=False)
    location = forms.CharField(max_length=255)
    panchayat_municipality = forms.ChoiceField(choices=Ward.panchayat_municipality_choices)
    ward_name = forms.CharField(max_length=100)
    ward_number = forms.IntegerField()

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
            # Create or get Ward
            panchayat_municipality = self.cleaned_data.get('panchayat_municipality')
            ward_name = self.cleaned_data.get('ward_name')
            ward_number = self.cleaned_data.get('ward_number')
            ward, created = Ward.objects.get_or_create(
                name=ward_name,
                panchayat_municipality=panchayat_municipality,
                ward_number=ward_number
            )
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'mobile_number': self.cleaned_data.get('mobile_number'),
                    'location': self.cleaned_data.get('location'),
                    'ward': ward,
                    'role': 'admin'
                }
            )
            Reward.objects.get_or_create(user=user, defaults={'points': 0})
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
            if schedule_date_time < timezone.now():
                raise ValidationError("Schedule date and time must be in the future.")
        return schedule_date_time
