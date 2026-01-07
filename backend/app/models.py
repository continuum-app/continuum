from django.db import models

class Habit(models.Model):
    name = models.CharField(max_length=100)
    streak = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
