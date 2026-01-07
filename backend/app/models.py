from django.db import models
from django.utils import timezone


class Habit(models.Model):
    TYPE_CHOICES = [
        ("boolean", "Yes/No"),
        ("counter", "Counter"),
        ("timer", "Time Duration"),
    ]

    name = models.CharField(max_length=100)
    habit_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default="boolean"
    )

    icon = models.CharField(max_length=50, default="calendar")
    color = models.CharField(max_length=20, default="#1F85DE")

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    habit = models.ForeignKey(
        Habit, related_name="subcategories", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.habit.name} - {self.name}"


class Completion(models.Model):
    habit = models.ForeignKey(
        Habit, related_name="completions", on_delete=models.CASCADE
    )
    subcategory = models.ForeignKey(
        Subcategory, null=True, blank=True, on_delete=models.SET_NULL
    )
    date = models.DateField(default=timezone.now)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.habit.name} - {self.subcategory}"
