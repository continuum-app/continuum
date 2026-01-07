from django.contrib import admin
from .models import Habit

# This makes the Habit model visible in the Admin
admin.site.register(Habit)
