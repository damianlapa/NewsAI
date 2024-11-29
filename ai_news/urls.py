from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('articles.urls')),
    path('users/', include('users.urls')),
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_field_name='next'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='logout.html'
    ), name='logout'),
]
