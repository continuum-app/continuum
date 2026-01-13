from rest_framework import serializers
from .models import Habit, Category, Completion
from datetime import date


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]
        # user field is set automatically in the view, so we don't include it here


class HabitSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)  # Single category, not many
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    today_value = serializers.SerializerMethodField()
    max_value = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Habit
        fields = [
            "id",
            "name",
            "habit_type",
            "category",
            "category_id",
            "icon",
            "color",
            "max_value",
            "today_value",
        ]
        # user field is set automatically in the view, so we don't include it here

    def get_today_value(self, obj):
        completion = obj.completions.filter(date=date.today()).first()
        return float(completion.value) if completion else 0

    def validate_category_id(self, value):
        # Ensure the category belongs to the current user
        if value and value.user != self.context["request"].user:
            raise serializers.ValidationError("You can only use your own categories")
        return value
