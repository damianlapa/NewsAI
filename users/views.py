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
    try:
        print("Profile view accessed")

        # Pobierz lub utwórz profil
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        print(f"User profile: {user_profile.id}, created: {created}")

        # Pobierz kategorie
        categories = Category.objects.all()
        print(f"Found {categories.count()} categories")

        if request.method == 'POST':
            selected_categories = request.POST.getlist('selected_categories')
            print(f"Selected categories: {selected_categories}")

            user_profile.selected_categories.clear()
            for category_id in selected_categories:
                try:
                    category = Category.objects.get(id=category_id)
                    user_profile.selected_categories.add(category)
                except Category.DoesNotExist:
                    continue

            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')

        context = {
            'all_categories': categories,
            'selected_categories': user_profile.selected_categories.all(),
        }
        return render(request, 'users/profile.html', context)

    except Exception as e:
        print(f"Error in profile view: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, "An error occurred.")
        return render(request, 'users/profile.html', {
            'all_categories': Category.objects.all(),
            'selected_categories': [],
        })
