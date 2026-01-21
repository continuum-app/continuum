from django.contrib import admin
from .models import Habit, Completion, Category, HabitCorrelation

admin.site.register(Habit)
admin.site.register(Completion)
admin.site.register(Category)
admin.site.register(HabitCorrelation)
