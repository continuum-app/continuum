from rest_framework import serializers
from .models import Habit, Category, Completion, SiteSettings, HabitCorrelation
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
            "archived",
        ]

    def get_today_value(self, obj):
        # Get the date from context (passed by the viewset)
        target_date = self.context.get("date", date.today())
        completion = obj.completions.filter(date=target_date).first()
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


# Lightweight serializer for habit info in correlations
class HabitBasicSerializer(serializers.ModelSerializer):
    """Minimal habit serializer for correlation insights."""

    category_name = serializers.CharField(
        source="category.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Habit
        fields = ["id", "name", "icon", "color", "habit_type", "category_name"]


class HabitCorrelationSerializer(serializers.ModelSerializer):
    """Serializer for habit correlation insights."""

    habit1 = HabitBasicSerializer(read_only=True)
    habit2 = HabitBasicSerializer(read_only=True)
    correlation = serializers.DecimalField(
        source="correlation_coefficient", max_digits=5, decimal_places=4, read_only=True
    )
    max_correlation = serializers.SerializerMethodField()
    strength = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = HabitCorrelation
        fields = [
            "habit1",
            "habit2",
            "correlation",
            "spearman_coefficient",
            "dtw_distance",
            "max_correlation",
            "sample_size",
            "start_date",
            "end_date",
            "strength",
            "description",
        ]
        read_only_fields = fields

    def get_max_correlation(self, obj):
        """Get the maximum correlation across all methods."""
        return obj.max_correlation

    def get_strength(self, obj):
        """Classify correlation strength based on maximum correlation across all methods."""
        max_corr = obj.max_correlation

        if max_corr >= 0.9:
            return "very_strong"
        elif max_corr >= 0.7:
            return "strong"
        elif max_corr >= 0.5:
            return "moderate"
        elif max_corr >= 0.3:
            return "weak"
        else:
            return "very_weak"

    def get_description(self, obj):
        """Generate human-readable description of the correlation."""
        habit1_name = obj.habit1.name
        habit2_name = obj.habit2.name
        coefficient = float(obj.correlation_coefficient)

        if coefficient > 0:
            if coefficient >= 0.9:
                return f"When you do {habit1_name}, you almost always do {habit2_name} too!"
            elif coefficient >= 0.7:
                return f"You tend to do {habit1_name} and {habit2_name} together."
            elif coefficient >= 0.5:
                return f"There's a moderate connection between {habit1_name} and {habit2_name}."
            else:
                return f"You sometimes do {habit1_name} and {habit2_name} together."
        else:
            abs_coef = abs(coefficient)
            if abs_coef >= 0.7:
                return f"You rarely do {habit1_name} and {habit2_name} on the same day."
            elif abs_coef >= 0.5:
                return f"When you do {habit1_name}, you tend to skip {habit2_name}."
            else:
                return f"There's a slight inverse relationship between {habit1_name} and {habit2_name}."
