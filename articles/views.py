from django.shortcuts import render
from .models import Article


def home_view(request):
    articles = Article.objects.all().order_by('-publication_date')
    return render(request, 'articles/main.html', locals())
