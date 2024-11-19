from django.urls import path
from .views import home_view, UserArticleView


urlpatterns = [
    path('', home_view, name="home"),
    path('user-articles/', UserArticleView.as_view(), name='user-articles')
]
