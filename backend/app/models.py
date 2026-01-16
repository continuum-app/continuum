from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name}"


class Habit(models.Model):
    TYPE_CHOICES = [
        ("boolean", "Yes/No"),
        ("counter", "Counter"),
        ("timer", "Time Duration"),
        ("rating", "Rating"),
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="habits")

    icon = models.CharField(max_length=50, default="calendar")
    color = models.CharField(max_length=20, default="#1F85DE")
    max_value = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

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
        unique_together = ["habit", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.habit.name} - {self.date}"


class SiteSettings(models.Model):
    """
    Site-wide settings that can only be modified by admin users.
    This uses a singleton pattern - only one instance should exist.
    """

    # Registration settings
    allow_registration = models.BooleanField(
        default=True, help_text="Allow new users to register on the site"
    )

    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="settings_updates",
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Settings"

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion of settings
        pass
