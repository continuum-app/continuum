from rest_framework import serializers
from .models import Habit, Category, Completion, SiteSettings
from datetime import date


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "order"]


class HabitSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
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

    def get_today_value(self, obj):
        completion = obj.completions.filter(date=date.today()).first()
        return float(completion.value) if completion else 0

    def validate_category_id(self, value):
        if value and value.user != self.context["request"].user:
            raise serializers.ValidationError("You can only use your own categories")
        return value


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = ["id", "allow_registration", "updated_at", "updated_by"]
        read_only_fields = ["id", "updated_at", "updated_by"]
