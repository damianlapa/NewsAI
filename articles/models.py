from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)


class Article(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    summary = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    publication_date = models.DateField()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    selected_categories = models.ManyToManyField(Category)

