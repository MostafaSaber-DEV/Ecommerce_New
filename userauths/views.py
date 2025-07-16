from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib.auth import login, authenticate , logout
from django.contrib import messages
from django.conf import settings
from .forms import LoginForm
from django.contrib.auth import get_user_model
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            messages.success(request, f'User {email} created successfully!')

            user = authenticate(username=email, password=raw_password)

            if user is not None:
                login(request, user)
                return redirect('core:index')
            else:
                messages.warning(request, "Authentication failed.")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'userauths/signup.html', {'form': form})



User = get_user_model()

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:index')

    form = LoginForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {email}!')
                return redirect('core:index')
            else:
                messages.error(request, 'Invalid email or password.')

    return render(request, 'userauths/signin.html', {'form': form, 'title': 'Login'})



def logout_view(request,pk):
    logout(request)
    messages.success(request, 'You have been logged out successfully.') 
    return redirect('core:index')
