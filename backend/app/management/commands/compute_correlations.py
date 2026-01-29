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
from collections import defaultdict

import numpy as np
from scipy.stats import spearmanr

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
            help="Compute correlations for a specific user only",
        )
        parser.add_argument(
            "--min-sample-size",
            type=int,
            default=4,
            help="Minimum number of overlapping data points required",
        )

    def handle(self, *args, **options):
        days = options["days"]
        user_id = options.get("user_id")
        min_sample_size = options["min_sample_size"]

        end_date = timezone.now().date() - timedelta(days=1)
        start_date = end_date - timedelta(days=days - 1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Computing correlations from {start_date} to {end_date}"
            )
        )

        users = User.objects.filter(id=user_id) if user_id else User.objects.all()
        total = 0

        for user in users:
            count = self.compute_user_correlations(
                user, start_date, end_date, min_sample_size
            )
            total += count
            self.stdout.write(f"  User {user.username}: {count} correlations")

        self.stdout.write(self.style.SUCCESS(f"✓ Computed {total} total correlations"))

    # -------------------------------------------------------------------------

    def compute_user_correlations(self, user, start_date, end_date, min_sample_size):
        habits = list(user.habits.filter(archived=False).order_by("id"))

        if len(habits) < 2:
            return 0

        completions = Completion.objects.filter(
            habit__user=user,
            date__gte=start_date,
            date__lte=end_date,
        ).select_related("habit")

        habit_data = defaultdict(dict)
        for c in completions:
            habit_data[c.habit_id][c.date] = float(c.value)

        habit_ids = [h.id for h in habits if h.id in habit_data]
        if len(habit_ids) < 2:
            return 0

        habit_map = {h.id: h for h in habits}

        all_dates = sorted(
            {date for values in habit_data.values() for date in values.keys()}
        )

        if len(all_dates) < min_sample_size:
            return 0

        num_habits = len(habit_ids)
        num_dates = len(all_dates)

        # Raw matrix with NaN for missing data
        raw = np.full((num_habits, num_dates), np.nan, dtype=np.float64)

        for i, habit_id in enumerate(habit_ids):
            for j, date in enumerate(all_dates):
                if date in habit_data[habit_id]:
                    raw[i, j] = habit_data[habit_id][date]

        # Normalized matrix (DTW only)
        norm = np.full_like(raw, np.nan)
        for i in range(num_habits):
            row = raw[i]
            mask = ~np.isnan(row)
            if mask.sum() == 0:
                continue
            min_v = np.nanmin(row)
            max_v = np.nanmax(row)
            if max_v > min_v:
                norm[i, mask] = (row[mask] - min_v) / (max_v - min_v)
            else:
                norm[i, mask] = 1.0

        existing = HabitCorrelation.objects.filter(user=user)
        existing_map = {(c.habit1_id, c.habit2_id): c for c in existing}

        to_create = []
        to_update = []

        for i in range(num_habits):
            for j in range(i + 1, num_habits):
                h1_id = habit_ids[i]
                h2_id = habit_ids[j]

                x = raw[i]
                y = raw[j]

                overlap_mask = ~np.isnan(x) & ~np.isnan(y)
                overlap = overlap_mask.sum()

                if overlap < min_sample_size:
                    continue

                # Pearson (raw values)
                with np.errstate(divide="ignore", invalid="ignore"):
                    pearson = np.corrcoef(x[overlap_mask], y[overlap_mask])[0, 1]

                if np.isnan(pearson):
                    continue

                # Spearman (raw values)
                with np.errstate(divide="ignore", invalid="ignore"):
                    spearman, _ = spearmanr(
                        x[overlap_mask],
                        y[overlap_mask],
                    )

                # DTW (normalized, optional)
                dtw_value = None
                if HAS_DTW:
                    nx = norm[i][overlap_mask]
                    ny = norm[j][overlap_mask]
                    if len(nx) > 1 and len(ny) > 1:
                        dist = dtw.distance(nx, ny)
                        dtw_value = dist / (len(nx) + len(ny))

                pearson_d = Decimal(str(round(float(pearson), 4)))
                spearman_d = (
                    None
                    if np.isnan(spearman)
                    else Decimal(str(round(float(spearman), 4)))
                )
                dtw_d = (
                    None
                    if dtw_value is None
                    else Decimal(str(round(float(dtw_value), 4)))
                )

                key = (h1_id, h2_id)
                obj = existing_map.get(key)

                if obj:
                    obj.correlation_coefficient = pearson_d
                    obj.spearman_coefficient = spearman_d
                    obj.dtw_distance = dtw_d
                    obj.sample_size = overlap
                    obj.start_date = start_date
                    obj.end_date = end_date
                    to_update.append(obj)
                else:
                    to_create.append(
                        HabitCorrelation(
                            user=user,
                            habit1=habit_map[h1_id],
                            habit2=habit_map[h2_id],
                            correlation_coefficient=pearson_d,
                            spearman_coefficient=spearman_d,
                            dtw_distance=dtw_d,
                            sample_size=overlap,
                            start_date=start_date,
                            end_date=end_date,
                        )
                    )

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
