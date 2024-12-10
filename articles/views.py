from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
from .models import Article, UserProfile


def home_view(request):
    articles = Article.objects.all().order_by('-publication_date')
    print(f"Rendering {articles.count()} articles")  # Debug
    return render(request, 'articles/main.html', {'articles': articles})

@method_decorator(login_required, name='dispatch')
class UserArticleView(View):
    def get(self, request):
        user_profile = UserProfile.objects.filter(user=request.user).first()
        if not user_profile:
            return render(request, 'articles/main.html', {'articles': []})

        selected_categories = user_profile.selected_categories.all()
        articles = Article.objects.filter(category__in=selected_categories).order_by('-publication_date')
        return render(request, 'articles/main.html', {'articles': articles})

@login_required
def profile_view(request):
    return render(request, 'profile.html')
