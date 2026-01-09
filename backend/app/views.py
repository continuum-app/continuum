from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import HabitSerializer, CategorySerializer
from datetime import date
from .models import Habit, Completion, Category


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class HabitViewSet(viewsets.ModelViewSet):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        habit = self.get_object()
        category_id = request.data.get("category_id")
        val = request.data.get("value", 1)  # Default to 1 for booleans

        # Find the category object if an ID was provided
        category_obj = None
        if category_id:
            try:
                category_obj = Category.objects.get(id=category_id)
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
