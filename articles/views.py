from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
from .models import Article, UserProfile


def home_view(request):
    articles = Article.objects.all().order_by('-publication_date')
    return render(request, 'articles/main.html', locals())


class UserArticleView(View):
    def get(self, request):
        selected_categories = UserProfile.objects.get(user=request.user).selected_categories.all()
        articles = Article.objects.filter(category__in=selected_categories)
        return render(request, 'articles/main.html', {'articles': articles})
