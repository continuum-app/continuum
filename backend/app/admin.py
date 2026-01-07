from django.contrib import admin
from .models import Habit, Completion

# This makes the Habit model visible in the Admin
admin.site.register(Habit)
admin.site.register(Completion)
