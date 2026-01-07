from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Habit, Completion
from .serializers import HabitSerializer
from datetime import date


class HabitViewSet(viewsets.ModelViewSet):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        habit = self.get_object()
        # Create a completion for today if it doesn't exist
        Completion.objects.get_or_create(habit=habit, date=date.today())
        return Response({"status": "habit completed"})
