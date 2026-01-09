from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.name}"


class Habit(models.Model):
    TYPE_CHOICES = [
        ("boolean", "Yes/No"),  # Yes or no type of habits, a card toggle
        (
            "counter",
            "Counter",
        ),  # A counter habit, there is a - and + on the card to adjust the value
        (
            "timer",
            "Time Duration",
        ),  # A timer habit, the user can enter a decimal value to indicate time mostly, but can be used for other type of data
        (
            "rating",
            "Rating",
        ),  # A star-rating habit card, the max amount of star is determined by the habit's max_value field.
    ]
    name = models.CharField(max_length=100)
    habit_type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default="boolean"
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="habits",
    )

    icon = models.CharField(max_length=50, default="calendar")
    color = models.CharField(max_length=20, default="#1F85DE")
    max_value = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self):
        return self.name


class Completion(models.Model):
    habit = models.ForeignKey(
        Habit, related_name="completions", on_delete=models.CASCADE
    )
    date = models.DateField(default=timezone.now)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        # Ensure only one completion per habit per date
        unique_together = ["habit", "date"]

    def __str__(self):
        return f"{self.habit.name} - {self.date}"
