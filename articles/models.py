from django.db import models
from django.contrib.auth.models import User
from pydantic import ValidationError


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f'{self.name}'


class Article(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    summary = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    publication_date = models.DateField()

    def __str__(self):
        return f'{self.title}'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    selected_categories = models.ManyToManyField(Category)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def clean(self):
        # Sprawdź czy użytkownik już ma profil przed zapisem
        if not self.pk:  # Tylko dla nowych obiektów
            existing_profile = UserProfile.objects.filter(user=self.user).first()
            if existing_profile and existing_profile.pk != self.pk:
                raise ValidationError('User already has a profile')
        super().clean()

    def __str__(self):
        return f'{self.user} - user profile'

