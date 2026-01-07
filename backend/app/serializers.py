from rest_framework import serializers
from .models import Habit, Subcategory, Completion
from datetime import date


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ["id", "name"]

class HabitSerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)
    today_value = serializers.SerializerMethodField()

    class Meta:
        model = Habit
        fields = [
            "id",
            "name",
            "habit_type",
            "subcategories",
            "icon",
            "color",
            "today_value",
        ]

    def get_today_value(self, obj):
        completion = obj.completions.filter(date=date.today()).first()
        return completion.value if completion else 0
