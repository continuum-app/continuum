from rest_framework import serializers
from .models import Habit, Category, Completion
from datetime import date


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class HabitSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    today_value = serializers.SerializerMethodField()

    class Meta:
        model = Habit
        fields = [
            "id",
            "name",
            "habit_type",
            "category",
            "icon",
            "color",
            "today_value",
        ]

    def get_today_value(self, obj):
        completion = obj.completions.filter(date=date.today()).first()
        return completion.value if completion else 0
