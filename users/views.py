from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .forms import UserProfileForm
from articles.models import UserProfile, Category


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = request.POST["password1"]
            messages.success(request, f'Konto utworzone dla {username}! Możesz się teraz zalogować.')
            login(request, user=authenticate(request, username=username, password=password))
            return redirect('profile')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', locals())



@login_required
def profile(request):
    user_profile = UserProfile.objects.get(user=request.user)
    all_categories = Category.objects.all()
    categories = user_profile.selected_categories.all()
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'users/profile.html', locals())

