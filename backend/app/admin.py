from django.contrib import admin
from .models import Habit, Completion, Subcategory

admin.site.register(Habit)
admin.site.register(Completion)
admin.site.register(Subcategory)
