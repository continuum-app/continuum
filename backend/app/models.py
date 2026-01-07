from django.db import models
from django.utils import timezone

class Habit(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    icon = models.CharField(max_length=50, default='Activity')
    color = models.CharField(max_length=20, default='#6366f1')

    def __str__(self):
        return self.name
    
class Completion(models.Model):
    habit = models.ForeignKey(Habit, related_name='completions', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ('habit', 'date') # Prevents double-clicking the same day
