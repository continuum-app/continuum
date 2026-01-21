"""
Management command to compute habit correlations for all users.
Run this nightly using Django's task scheduler or cron.

Usage:
    python manage.py compute_correlations
    python manage.py compute_correlations --days 7
    python manage.py compute_correlations --user-id 1
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import numpy as np
from collections import defaultdict
from ...models import Habit, Completion, HabitCorrelation


class Command(BaseCommand):
    help = "Compute habit correlations for all users based on recent completion data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days to analyze (default: 7)",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Compute correlations for specific user only",
        )
        parser.add_argument(
            "--min-sample-size",
            type=int,
            default=4,
            help="Minimum number of overlapping data points required (default: 4)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        user_id = options.get("user_id")
        min_sample_size = options["min_sample_size"]

        # Calculate date range
        end_date = timezone.now().date() - timedelta(days=1)  # Exclude today
        start_date = end_date - timedelta(days=days - 1)

        self.stdout.write(
            self.style.SUCCESS(f"Computing correlations for {start_date} to {end_date}")
        )

        # Get users to process
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            users = User.objects.all()

        total_correlations = 0

        for user in users:
            correlations_computed = self.compute_user_correlations(
                user, start_date, end_date, min_sample_size
            )
            total_correlations += correlations_computed

            self.stdout.write(
                f"  User {user.username}: {correlations_computed} correlations"
            )

        self.stdout.write(
            self.style.SUCCESS(f"✓ Computed {total_correlations} total correlations")
        )

    def compute_user_correlations(self, user, start_date, end_date, min_sample_size):
        """Compute correlations for a single user."""

        # Get all habits for this user
        habits = list(user.habits.all())

        if len(habits) < 2:
            return 0  # Need at least 2 habits to correlate

        # Fetch all completions for the date range
        completions = Completion.objects.filter(
            habit__user=user, date__gte=start_date, date__lte=end_date
        ).select_related("habit")

        # Build a data structure: {habit_id: {date: normalized_value}}
        habit_data = defaultdict(dict)
        habit_meta = {}  # Store habit metadata for normalization

        for completion in completions:
            habit_id = completion.habit_id
            date = completion.date
            value = float(completion.value)

            # Store raw value
            habit_data[habit_id][date] = value

            # Track min/max for normalization
            if habit_id not in habit_meta:
                habit_meta[habit_id] = {"habit": completion.habit, "values": []}
            habit_meta[habit_id]["values"].append(value)

        # Normalize all habit data to 0-1 scale
        normalized_data = {}
        for habit_id, dates_values in habit_data.items():
            values = habit_meta[habit_id]["values"]
            min_val = min(values)
            max_val = max(values)

            # Normalize to 0-1
            if max_val > min_val:
                normalized_data[habit_id] = {
                    date: (value - min_val) / (max_val - min_val)
                    for date, value in dates_values.items()
                }
            else:
                # All values are the same
                normalized_data[habit_id] = {
                    date: 1.0 if value > 0 else 0.0
                    for date, value in dates_values.items()
                }

        # Compute correlations between all pairs of habits
        correlations_computed = 0

        for i, habit1 in enumerate(habits):
            for habit2 in habits[i + 1 :]:  # Only compute upper triangle
                correlation = self.compute_correlation(
                    habit1,
                    habit2,
                    normalized_data,
                    start_date,
                    end_date,
                    min_sample_size,
                )

                if correlation is not None:
                    # Store or update correlation
                    HabitCorrelation.objects.update_or_create(
                        user=user,
                        habit1=habit1,
                        habit2=habit2,
                        defaults={
                            "correlation_coefficient": Decimal(
                                str(round(correlation["coefficient"], 4))
                            ),
                            "sample_size": correlation["sample_size"],
                            "start_date": start_date,
                            "end_date": end_date,
                        },
                    )
                    correlations_computed += 1

        return correlations_computed

    def compute_correlation(
        self, habit1, habit2, normalized_data, start_date, end_date, min_sample_size
    ):
        """Compute Pearson correlation coefficient between two habits."""

        habit1_data = normalized_data.get(habit1.id, {})
        habit2_data = normalized_data.get(habit2.id, {})

        # Find dates where both habits have data
        common_dates = set(habit1_data.keys()) & set(habit2_data.keys())

        if len(common_dates) < min_sample_size:
            return None  # Not enough overlapping data

        # Extract values for common dates
        values1 = [habit1_data[date] for date in sorted(common_dates)]
        values2 = [habit2_data[date] for date in sorted(common_dates)]

        # Compute Pearson correlation
        try:
            correlation_matrix = np.corrcoef(values1, values2)
            correlation_coefficient = correlation_matrix[0, 1]

            # Handle NaN (can occur if all values are identical)
            if np.isnan(correlation_coefficient):
                return None

            return {
                "coefficient": float(correlation_coefficient),
                "sample_size": len(common_dates),
            }
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"  Error computing correlation for {habit1.name} & {habit2.name}: {e}"
                )
            )
            return None
