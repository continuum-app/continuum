<script setup>
import { computed } from 'vue'
import * as LucideIcons from 'lucide-vue-next'
import { Star, CheckCircle2 } from 'lucide-vue-next'
import backgroundHabits from '@/data/backgroundHabits.json'

// Get icon component from name
const getIcon = (iconName) => {
    if (!iconName) return LucideIcons.Calendar
    const pascalCase = iconName
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join('')
    return LucideIcons[pascalCase] || LucideIcons.Calendar
}

// Create multiple rows of cards for the animation
// We duplicate and shuffle cards to create variety
const shuffleArray = (array) => {
    const arr = [...array]
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]]
    }
    return arr
}

// Create rows with different card orders
const rows = computed(() => {
    const result = []
    for (let i = 0; i < 6; i++) {
        // Duplicate and shuffle to fill the row
        const shuffled = shuffleArray(backgroundHabits)
        result.push([...shuffled, ...shuffled])
    }
    return result
})
</script>

<template>
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <!-- Rotating container for 45-degree angle -->
        <div class="cards-container">
            <div v-for="(row, rowIndex) in rows" :key="rowIndex" class="card-row"
                :class="rowIndex % 2 === 0 ? 'animate-slide-left' : 'animate-slide-right'"
                :style="{ animationDelay: `${rowIndex * -5}s` }">
                <div v-for="(habit, cardIndex) in row" :key="`${rowIndex}-${cardIndex}`"
                    class="card-item bg-white dark:bg-neutral-800 rounded-4xl p-5 shadow-lg border border-neutral-100 dark:border-neutral-700 opacity-60">
                    <!-- Habit Header -->
                    <div class="flex items-center gap-3 mb-3">
                        <div class="p-2.5 rounded-xl" :style="{ backgroundColor: habit.color + '20' }">
                            <component :is="getIcon(habit.icon)" :size="20" :style="{ color: habit.color }"
                                stroke-width="2.5" />
                        </div>
                        <div class="flex-1 min-w-0">
                            <h4 class="font-black text-neutral-900 dark:text-white text-sm truncate">{{ habit.name }}
                            </h4>
                            <p v-if="habit.unit" class="text-[10px] font-bold text-neutral-400 uppercase tracking-wide">
                                {{ habit.unit }}
                            </p>
                        </div>
                    </div>

                    <!-- Boolean Habit -->
                    <div v-if="habit.habit_type === 'boolean'" class="flex justify-center">
                        <div :class="[
                            'w-full py-2.5 rounded-xl font-black text-sm text-center',
                            habit.is_completed
                                ? 'bg-green-500 text-white'
                                : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300'
                        ]">
                            <CheckCircle2 v-if="habit.is_completed" :size="20" class="mx-auto" />
                            <span v-else class="text-xs">Not done</span>
                        </div>
                    </div>

                    <!-- Counter Habit -->
                    <div v-else-if="habit.habit_type === 'counter'" class="text-center">
                        <span class="text-3xl font-black" :style="{ color: habit.color }">
                            {{ habit.value }}
                        </span>
                    </div>

                    <!-- Value Habit -->
                    <div v-else-if="habit.habit_type === 'value'" class="text-center">
                        <span class="text-3xl font-black" :style="{ color: habit.color }">
                            {{ habit.value }}
                        </span>
                        <span v-if="habit.unit" class="text-sm font-bold text-neutral-400 ml-1">{{ habit.unit }}</span>
                    </div>

                    <!-- Rating Habit -->
                    <div v-else-if="habit.habit_type === 'rating'" class="flex justify-center gap-0.5">
                        <Star v-for="star in (habit.max_value || 5)" :key="star" :size="18"
                            :fill="star <= habit.value ? habit.color : 'transparent'" :style="{ color: habit.color }"
                            stroke-width="2" />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.cards-container {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 200vmax;
    height: 200vmax;
    transform: translate(-50%, -50%) rotate(-45deg);
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    justify-content: center;
}

.card-row {
    display: flex;
    gap: 1.5rem;
    flex-shrink: 0;
}

.card-item {
    flex-shrink: 0;
    width: 180px;
    min-width: 180px;
}

.animate-slide-left {
    animation: slideLeft 60s linear infinite;
}

.animate-slide-right {
    animation: slideRight 60s linear infinite;
}

@keyframes slideLeft {
    0% {
        transform: translateX(0);
    }

    100% {
        transform: translateX(-50%);
    }
}

@keyframes slideRight {
    0% {
        transform: translateX(-50%);
    }

    100% {
        transform: translateX(0);
    }
}
</style>
