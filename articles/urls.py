from django.urls import path

from . import views
from .views import home_view, UserArticleView


urlpatterns = [
    path('', home_view, name="home"),
    path('user-articles/', views.UserArticleView.as_view(), name='user-articles'),
    path('profile/', views.profile_view, name='profile'),
]
