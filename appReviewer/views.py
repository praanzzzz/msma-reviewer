from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .utils import send_verification_email
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import CustomUser
from django.core.signing import BadSignature, SignatureExpired
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.core.signing import Signer
signer = Signer()


#                fadgMSMA@2025

# Create your views here.
def landing_page(request):
    return render(request, "appReviewer/landing_page.html", {})

@login_required
def dashboard(request):
    return render(request, "appReviewer/dashboard.html", {})

def my_register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_verified = False
            user.is_active = False
            user.save()
            send_verification_email(user)
            messages.info(request, "Please check and verify email.")
            return redirect("my_register")
    
    else:
        form = RegisterForm()
    return render(request, "auth_pages/my_register.html", {"form": form})


def verify_email(request, token):
    try:
        user_id = signer.unsign(token)  # Decode user ID from token
        user = CustomUser.objects.get(pk=user_id)  # Get the user

        # Mark as verified and active
        user.is_verified = True
        user.is_active = True
        user.save()
        messages.success(request, "Email verified Succesfully")
        return redirect("my_login")
    except SignatureExpired:
        messages.error(request, "Verification link expired. Please register again.")
    except (BadSignature, CustomUser.DoesNotExist):
        print("Email verification failed. Invalid or expired verification link.")
        messages.error(request, "Invalid verification link")



def my_login(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(request, email=email, password=password) # it only checks is_active = True
            if user is None:
                messages.error(request, "Invalid credentials or Account deactivated.")
            elif not user.is_verified:
                messages.info(request, "Please check and verify your email.")
            elif not user.is_active:
                messages.info(request, "Account is deactived")
            else:
                login(request, user)
                return redirect("dashboard")
    context = {"form": form}
    return render(request, "auth_pages/my_login.html", context)



def my_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect("my_login")



@login_required
def reviewer(request):
    return render(request, "appReviewer/reviewer.html")


@login_required
def profile(request):
    return render(request, "appReviewer/profile.html")


