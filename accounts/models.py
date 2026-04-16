from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser





class User(AbstractUser):
    ROLE_CHOICES = (
        ('dean', 'Декан'),
        ('senior', 'Старший'),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='senior'
    )
