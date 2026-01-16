from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import HabitSerializer, CategorySerializer
from datetime import date, datetime
from .models import Habit, Completion, Category
from django.db.models import Q


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by("order", "name")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"])
    def update_layout(self, request):
        """Update the order of categories"""
        layout_data = request.data.get("layout", [])

        for item in layout_data:
            try:
                category = Category.objects.get(id=item["id"], user=request.user)
                category.order = item.get("order", 0)
                category.save()
            except Category.DoesNotExist:
                pass

        return Response({"status": "layout updated"})


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]
    # Add queryset attribute for the router
    queryset = Habit.objects.all()

    def get_queryset(self):
        # Only return habits for the authenticated user
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically set the user when creating a habit
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        habit = self.get_object()
        category_id = request.data.get("category_id")
        val = request.data.get("value", 1)  # Default to 1 for booleans

        # Find the category object if an ID was provided
        category_obj = None
        if category_id:
            try:
                # Ensure the category belongs to the authenticated user
                category_obj = Category.objects.get(id=category_id, user=request.user)
            except Category.DoesNotExist:
                return Response({"error": "category not found"}, status=404)

        # Update or create completion for today
        completion, created = Completion.objects.update_or_create(
            habit=habit,
            date=date.today(),
            defaults={"value": val, "category": category_obj},
        )

        return Response(
            {
                "status": "updated" if not created else "created",
                "new_value": float(completion.value),
            }
        )

    @action(detail=False, methods=["get"])
    def graph_data(self, request):
        """
        Get habit completion data for graphing within a date range.
        Returns data grouped by habit type.
        """
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        if not start_date_str or not end_date_str:
            return Response(
                {"error": "start_date and end_date are required"}, status=400
            )

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, status=400
            )

        # Get all habits for the user
        habits = self.get_queryset()

        # Structure: { habit_type: [{ habit_name, habit_id, color, data: [{ date, value }] }] }
        result = {"boolean": [], "counter": [], "timer": [], "rating": []}

        for habit in habits:
            # Get completions for this habit in the date range
            completions = Completion.objects.filter(
                habit=habit, date__gte=start_date, date__lte=end_date
            ).order_by("date")

            # Build data points
            data_points = []
            for completion in completions:
                data_points.append(
                    {
                        "date": completion.date.isoformat(),
                        "value": float(completion.value),
                    }
                )

            # Only include habits that have data
            if data_points:
                habit_data = {
                    "habit_id": habit.id,
                    "habit_name": habit.name,
                    "color": habit.color,
                    "data": data_points,
                }

                result[habit.habit_type].append(habit_data)

        return Response(result)
