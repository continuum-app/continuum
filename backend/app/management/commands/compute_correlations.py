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
from scipy.stats import spearmanr
from collections import defaultdict
from ...models import Habit, Completion, HabitCorrelation

try:
    from dtaidistance import dtw

    HAS_DTW = True
except ImportError:
    HAS_DTW = False


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
        """Compute correlations for a single user using matrix operations."""

        # Get all non-archived habits for this user
        habits = list(user.habits.filter(archived=False))

        if len(habits) < 2:
            return 0  # Need at least 2 habits to correlate

        # Fetch all completions for the date range
        completions = Completion.objects.filter(
            habit__user=user, date__gte=start_date, date__lte=end_date
        ).select_related("habit")

        # Build a data structure: {habit_id: {date: value}}
        habit_data = defaultdict(dict)

        for completion in completions:
            habit_id = completion.habit_id
            date = completion.date
            value = float(completion.value)
            habit_data[habit_id][date] = value

        # Create ordered list of habit IDs that have data
        habit_ids = [h.id for h in habits if h.id in habit_data]
        habit_map = {h.id: h for h in habits}

        if len(habit_ids) < 2:
            return 0

        # Find all dates where any habit has data
        all_dates = set()
        for dates_values in habit_data.values():
            all_dates.update(dates_values.keys())

        if len(all_dates) < min_sample_size:
            return 0

        sorted_dates = sorted(all_dates)
        num_habits = len(habit_ids)
        num_dates = len(sorted_dates)

        # Build raw data matrix (habits x dates)
        raw_matrix = np.zeros((num_habits, num_dates), dtype=np.float64)
        for i, habit_id in enumerate(habit_ids):
            for j, date in enumerate(sorted_dates):
                raw_matrix[i, j] = habit_data[habit_id].get(date, 0.0)

        # Build normalized data matrix (0-1 scale per habit)
        normalized_matrix = np.zeros((num_habits, num_dates), dtype=np.float64)
        for i, habit_id in enumerate(habit_ids):
            row = raw_matrix[i]
            min_val = row.min()
            max_val = row.max()

            if max_val > min_val:
                normalized_matrix[i] = (row - min_val) / (max_val - min_val)
            else:
                # All values are the same
                normalized_matrix[i] = np.where(row > 0, 1.0, 0.0)

        # Compute all correlation matrices at once
        pearson_matrix = self.compute_pearson_matrix(normalized_matrix)
        spearman_matrix = self.compute_spearman_matrix(raw_matrix)
        dtw_matrix = self.compute_dtw_matrix(normalized_matrix)

        # Fetch existing correlations for this user to determine create vs update
        existing_correlations = HabitCorrelation.objects.filter(user=user)
        existing_map = {(c.habit1_id, c.habit2_id): c for c in existing_correlations}

        # Build lists for bulk operations
        to_create = []
        to_update = []

        for i in range(num_habits):
            for j in range(i + 1, num_habits):
                habit1_id = habit_ids[i]
                habit2_id = habit_ids[j]

                pearson_coef = (
                    pearson_matrix[i, j] if pearson_matrix is not None else None
                )
                spearman_coef = (
                    spearman_matrix[i, j] if spearman_matrix is not None else None
                )
                dtw_dist = dtw_matrix[i, j] if dtw_matrix is not None else None

                # Skip if Pearson is invalid
                if pearson_coef is None or np.isnan(pearson_coef):
                    continue

                # Prepare values
                pearson_decimal = Decimal(str(round(pearson_coef, 4)))
                dtw_decimal = None
                if dtw_dist is not None and not np.isnan(dtw_dist):
                    dtw_decimal = Decimal(str(round(dtw_dist, 4)))
                spearman_decimal = None
                if spearman_coef is not None and not np.isnan(spearman_coef):
                    spearman_decimal = Decimal(str(round(spearman_coef, 4)))

                existing = existing_map.get((habit1_id, habit2_id))

                if existing:
                    # Update existing record
                    existing.correlation_coefficient = pearson_decimal
                    existing.spearman_coefficient = spearman_decimal
                    existing.dtw_distance = dtw_decimal
                    existing.sample_size = num_dates
                    existing.start_date = start_date
                    existing.end_date = end_date
                    to_update.append(existing)
                else:
                    # Create new record
                    to_create.append(
                        HabitCorrelation(
                            user=user,
                            habit1=habit_map[habit1_id],
                            habit2=habit_map[habit2_id],
                            correlation_coefficient=pearson_decimal,
                            spearman_coefficient=spearman_decimal,
                            dtw_distance=dtw_decimal,
                            sample_size=num_dates,
                            start_date=start_date,
                            end_date=end_date,
                        )
                    )

        # Perform bulk operations
        if to_create:
            HabitCorrelation.objects.bulk_create(to_create)
        if to_update:
            HabitCorrelation.objects.bulk_update(
                to_update,
                [
                    "correlation_coefficient",
                    "spearman_coefficient",
                    "dtw_distance",
                    "sample_size",
                    "start_date",
                    "end_date",
                ],
            )

        return len(to_create) + len(to_update)

    def compute_pearson_matrix(self, matrix):
        """Compute Pearson correlation matrix for all habits at once."""
        try:
            # np.corrcoef computes the full correlation matrix
            # Input: each row is a variable (habit), each column is an observation (date)
            # Suppress warning for zero-variance rows (constant values) - results in NaN which we handle
            with np.errstate(divide="ignore", invalid="ignore"):
                correlation_matrix = np.corrcoef(matrix)
            return correlation_matrix
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"  Error computing Pearson correlation matrix: {e}")
            )
            return None

    def compute_spearman_matrix(self, matrix):
        """Compute Spearman rank correlation matrix for all habits at once."""
        try:
            # spearmanr with axis=1 treats each row as a variable
            # Returns correlation matrix and p-value matrix
            correlation_matrix, _ = spearmanr(matrix, axis=1)

            # Handle single pair case where spearmanr returns scalar
            if np.isscalar(correlation_matrix):
                correlation_matrix = np.array(
                    [[1.0, correlation_matrix], [correlation_matrix, 1.0]]
                )

            return correlation_matrix
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"  Error computing Spearman correlation matrix: {e}"
                )
            )
            return None

    def compute_dtw_matrix(self, matrix):
        """Compute DTW distance matrix for all habits at once."""
        if not HAS_DTW:
            return None

        try:
            # dtw.distance_matrix computes all pairwise distances at once
            # Input should be a list of sequences or 2D array where each row is a sequence
            distance_matrix = dtw.distance_matrix(matrix)
            return distance_matrix
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"  Error computing DTW distance matrix: {e}")
            )
            return None
