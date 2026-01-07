from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import HabitSerializer
from datetime import date
from .models import Habit, Completion, Subcategory


class HabitViewSet(viewsets.ModelViewSet):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        habit = self.get_object()
        sub_id = request.data.get("subcategory_id")
        val = request.data.get("value", 1)  # Default to 1 for booleans

        # Find the subcategory object if an ID was provided
        subcategory_obj = None
        if sub_id:
            try:
                subcategory_obj = Subcategory.objects.filter(id=sub_id).first()
            except Subcategory.DoesNotExist:
                return Response({"error": "Subcategory not found"}, status=404)

        completion, created = Completion.objects.update_or_create(
            habit=habit,
            subcategory=subcategory_obj,
            date=date.today(),
            defaults={'value': val}
        )

        return Response({
            'status': 'updated' if not created else 'created',
            'new_value': completion.value
        })
