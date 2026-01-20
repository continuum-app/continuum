from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from .serializers import HabitSerializer, CategorySerializer, SiteSettingsSerializer
from datetime import date, datetime, timedelta
from .models import Habit, Completion, Category, SiteSettings
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

    def get_serializer_context(self):
        """Pass the requested date to the serializer"""
        context = super().get_serializer_context()
        # Get date from query params, default to today
        date_str = self.request.query_params.get("date")
        if date_str:
            try:
                context["date"] = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                context["date"] = date.today()
        else:
            context["date"] = date.today()
        return context

    def perform_create(self, serializer):
        # Automatically set the user when creating a habit
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        habit = self.get_object()
        val = request.data.get("value", 1)  # Default to 1 for booleans
        completion_date_str = request.data.get("date")  # Get date from request

        # Parse date or use today
        if completion_date_str:
            try:
                completion_date = datetime.strptime(
                    completion_date_str, "%Y-%m-%d"
                ).date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"}, status=400
                )
        else:
            completion_date = date.today()

        # Update or create completion for the specified date
        completion, created = Completion.objects.update_or_create(
            habit=habit,
            date=completion_date,
            defaults={"value": val},
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

    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        """
        Export habit completion data as CSV for a date range.
        Format: First column is habit name, subsequent columns are dates (one per day).
        Each row contains the values for that habit on each day.
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
        habits = self.get_queryset().order_by("name")

        # Generate list of all dates in range
        from datetime import timedelta

        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)

        # Build CSV content
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Write header row (Habit Name, Date1, Date2, ...)
        header = ["Habit Name"] + [d.strftime("%Y-%m-%d") for d in date_list]
        writer.writerow(header)

        # Write data rows
        for habit in habits:
            # Get all completions for this habit in the date range
            completions = Completion.objects.filter(
                habit=habit, date__gte=start_date, date__lte=end_date
            ).order_by("date")

            # Create a dictionary for quick lookup
            completion_dict = {c.date: float(c.value) for c in completions}

            # Build row: habit name followed by values for each date
            row = [habit.name]
            for date_item in date_list:
                value = completion_dict.get(date_item, "")
                row.append(value)

            writer.writerow(row)

        csv_content = output.getvalue()
        output.close()

        return Response({"csv_content": csv_content})

    @action(detail=False, methods=["get"])
    def date_range(self, request):
        """
        Get the minimum and maximum dates for all completions for the user's habits.
        Returns the date range of all available data.
        """
        # Get all habits for the user
        habits = self.get_queryset()

        # Get all completions for these habits
        completions = Completion.objects.filter(habit__in=habits).order_by("date")

        if not completions.exists():
            return Response(
                {"start_date": None, "end_date": None, "message": "No data available"}
            )

        min_date = completions.first().date
        max_date = completions.last().date

        return Response(
            {"start_date": min_date.isoformat(), "end_date": max_date.isoformat()}
        )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get summary statistics for habits over a date range (default: last 7 days).
        Returns metrics grouped by habit type.
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

        # Calculate number of days in range
        days_in_range = (end_date - start_date).days

        # Structure: { habit_type: [{ habit_name, color, metrics }] }
        result = {"boolean": [], "counter": [], "timer": [], "rating": []}

        for habit in habits:
            # Get completions for this habit in the date range
            completions = Completion.objects.filter(
                habit=habit, date__gte=start_date, date__lte=end_date
            )

            completion_count = completions.count()

            if completion_count == 0:
                continue

            # Calculate metrics based on habit type
            if habit.habit_type == "boolean":
                # For boolean: completion rate
                metrics = {
                    "total_completions": completion_count,
                    "completion_rate": round(
                        (completion_count / days_in_range) * 100, 1
                    ),
                    "days_in_range": days_in_range,
                    "streak": self._calculate_streak(habit, start_date, end_date),
                }
            elif habit.habit_type == "counter":
                # For counter: total, average, max
                values = [float(c.value) for c in completions]
                metrics = {
                    "total": sum(values),
                    "average": round(sum(values) / days_in_range, 1),
                    "max": max(values),
                    "days_tracked": completion_count,
                    "days_in_range": days_in_range,
                }
            elif habit.habit_type == "timer":
                # For timer: total hours, average, max session
                values = [float(c.value) for c in completions]
                metrics = {
                    "total_hours": round(sum(values), 1),
                    "average_hours": round(sum(values) / len(values), 1),
                    "max_session": round(max(values), 1),
                    "days_tracked": completion_count,
                    "days_in_range": days_in_range,
                }
            elif habit.habit_type == "rating":
                # For rating: average, distribution
                values = [float(c.value) for c in completions]
                metrics = {
                    "average": round(sum(values) / len(values), 1),
                    "max": int(max(values)),
                    "min": int(min(values)),
                    "days_tracked": completion_count,
                    "days_in_range": days_in_range,
                    "max_value": habit.max_value,
                }

            result[habit.habit_type].append(
                {
                    "habit_id": habit.id,
                    "habit_name": habit.name,
                    "category_name": habit.category.name if habit.category else None,
                    "color": habit.color,
                    "icon": habit.icon,
                    "metrics": metrics,
                }
            )

        return Response(result)

    def _calculate_streak(self, habit, start_date, end_date):
        """Calculate current streak for a habit ending on end_date"""
        current_date = start_date
        streak = 0
        max_streak = 0
        while True:
            completion = Completion.objects.filter(
                habit=habit, date=current_date
            ).first()

            if completion:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0

            current_date = current_date + timedelta(days=1)
            if current_date > end_date:
                break

        return max_streak


class UserInfoView(APIView):
    """
    Get current user information
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        )


class SiteSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for site-wide settings. Only admin users can modify settings.
    All authenticated users can view settings (to check if registration is allowed).
    """

    serializer_class = SiteSettingsSerializer
    queryset = SiteSettings.objects.all()

    def get_permissions(self):
        """
        Allow all authenticated users to view settings,
        but only admin users can modify them.
        check_registration is public (no auth required).
        """
        if self.action == "check_registration":
            # Public endpoint - no authentication required
            permission_classes = []
        elif self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Always return the singleton settings instance"""
        return SiteSettings.objects.all()

    def list(self, request):
        """
        Return the singleton settings instance for GET
        Handle updates for PATCH on list endpoint
        """
        if request.method == "PATCH":
            # Check if user is admin
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {"detail": "You do not have permission to perform this action."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            settings = SiteSettings.get_settings()
            serializer = self.get_serializer(settings, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # GET request
        settings = SiteSettings.get_settings()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Retrieve the singleton settings instance"""
        settings = SiteSettings.get_settings()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def update_settings(self, request):
        """Update the settings via custom action"""
        settings = SiteSettings.get_settings()
        serializer = self.get_serializer(settings, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=[])
    def check_registration(self, request):
        """Public endpoint to check if registration is allowed - no authentication required"""
        settings = SiteSettings.get_settings()
        return Response({"allow_registration": settings.allow_registration})
