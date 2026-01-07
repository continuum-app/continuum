from rest_framework import serializers
from .models import Habit, Completion
from datetime import date

class HabitSerializer(serializers.ModelSerializer):
    is_completed_today = serializers.SerializerMethodField()

    class Meta:
        model = Habit
        fields = ['id', 'name', 'icon', 'color', 'is_completed_today']

    def get_is_completed_today(self, obj):
        return obj.completions.filter(date=date.today()).exists()