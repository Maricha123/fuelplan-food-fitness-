"""
Core logic for the Food & Fitness Recommendation System.
Shared by both the analysis notebook and the Streamlit app so behaviour stays consistent.
"""
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

ACTIVITY_MULT = {
    "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
    "active": 1.725, "very_active": 1.9,
}

GOAL_CAL_ADJUST = {"lose_weight": -500, "maintain": 0, "gain_muscle": 350}
GOAL_TAG = {"lose_weight": "weight-loss", "maintain": "maintenance", "gain_muscle": "muscle-gain"}

DIET_FILTER = {
    "none": None,
    "vegetarian": "vegetarian",
    "vegan": "vegan",
    "high-protein": "high-protein",
    "low-carb": "low-carb",
}


def water_intake_target(weight_kg: float, minutes_exercise: int = 0) -> float:
    """Returns recommended daily water intake in liters.

    Baseline: 35 ml per kg of bodyweight/day, a widely-used general hydration guideline.
    Plus ~12 ml per minute of exercise, to replace fluid lost through sweat
    (roughly in line with ~500-700 ml/hour during moderate activity).
    Does not account for climate, illness, or pregnancy - those raise needs further.
    """
    base_ml = weight_kg * 35
    exercise_ml = minutes_exercise * 12
    total_ml = base_ml + exercise_ml
    return round(total_ml / 1000, 2)


def bmi(weight_kg: float, height_cm: float) -> float:
    return round(weight_kg / (height_cm / 100) ** 2, 1)


def bmi_class(bmi_value: float) -> str:
    if bmi_value < 18.5:
        return "underweight"
    elif bmi_value < 25:
        return "normal"
    elif bmi_value < 30:
        return "overweight"
    return "obese"


def bmr_mifflin(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if gender == "male" else base - 161


def tdee(bmr_value: float, activity_level: str) -> float:
    return round(bmr_value * ACTIVITY_MULT[activity_level], 0)


def target_calories(tdee_value: float, goal: str) -> float:
    return max(1200, round(tdee_value + GOAL_CAL_ADJUST[goal], 0))


def macro_targets(target_kcal: float, goal: str):
    """Returns (protein_g, carbs_g, fat_g) split by goal."""
    if goal == "gain_muscle":
        p, c, f = 0.30, 0.45, 0.25
    elif goal == "lose_weight":
        p, c, f = 0.35, 0.35, 0.30
    else:
        p, c, f = 0.25, 0.50, 0.25
    return (
        round(target_kcal * p / 4, 1),
        round(target_kcal * c / 4, 1),
        round(target_kcal * f / 9, 1),
    )


def recommend_foods(food_df: pd.DataFrame, goal: str, diet_pref: str,
                     meal_type: str = None, top_n: int = 10) -> pd.DataFrame:
    """Content-based filtering: filters by diet/meal tag then ranks by fit for the goal."""
    df = food_df.copy()

    tag = DIET_FILTER.get(diet_pref)
    if tag:
        df = df[df["DietTags"].str.contains(tag, na=False)]

    if meal_type:
        df = df[df["MealType"].str.contains(meal_type, na=False)]

    if df.empty:
        return df

    if goal == "gain_muscle":
        df["FitScore"] = df["Protein_per100g"] * 2 + df["HealthScore"] * 0.5
    elif goal == "lose_weight":
        df["FitScore"] = df["HealthScore"] - df["Calories_per100g"] * 0.15 + df["Fiber_per100g"]
    else:
        df["FitScore"] = df["HealthScore"]

    return df.sort_values("FitScore", ascending=False).head(top_n)


def similar_foods(food_df: pd.DataFrame, food_id: str, top_n: int = 5) -> pd.DataFrame:
    """Cosine-similarity based 'foods like this one' — a classic content-based recommender."""
    features = ["Calories_per100g", "Protein_per100g", "Fat_per100g", "Carbs_per100g", "Fiber_per100g"]
    scaler = StandardScaler()
    X = scaler.fit_transform(food_df[features])
    sims = cosine_similarity(X)
    idx = food_df.index[food_df["FoodID"] == food_id]
    if len(idx) == 0:
        return pd.DataFrame()
    i = idx[0]
    pos = food_df.index.get_loc(i)
    sim_scores = list(enumerate(sims[pos]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n + 1]
    result_idx = [food_df.index[s[0]] for s in sim_scores]
    return food_df.loc[result_idx]


def recommend_exercises(ex_df: pd.DataFrame, goal: str, weight_kg: float,
                         minutes: int = 30, equipment_available: list = None,
                         top_n: int = 8) -> pd.DataFrame:
    df = ex_df.copy()
    tag = GOAL_TAG[goal]
    df = df[df["GoalTags"].str.contains(tag, na=False)]

    if equipment_available is not None:
        df = df[df["Equipment"].apply(
            lambda e: e == "none" or any(eq.lower() in e.lower() for eq in equipment_available)
        )]

    if df.empty:
        return df

    df["EstKcalBurned"] = (df["KcalPerKgPerHour"] * weight_kg * minutes / 60).round(0)
    return df.sort_values("EstKcalBurned", ascending=False).head(top_n)


def weekly_plan(food_df, ex_df, goal, diet_pref, weight_kg, minutes_per_day=30):
    """Builds a simple 7-day meal + workout skeleton."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    breakfast = recommend_foods(food_df, goal, diet_pref, "breakfast", top_n=7)
    lunch = recommend_foods(food_df, goal, diet_pref, "lunch", top_n=7)
    dinner = recommend_foods(food_df, goal, diet_pref, "dinner", top_n=7)
    snack = recommend_foods(food_df, goal, diet_pref, "snack", top_n=7)
    workouts = recommend_exercises(ex_df, goal, weight_kg, minutes_per_day, top_n=7)

    plan = []
    for i, day in enumerate(days):
        plan.append({
            "Day": day,
            "Breakfast": breakfast.iloc[i % len(breakfast)]["Food"] if len(breakfast) else "-",
            "Lunch": lunch.iloc[i % len(lunch)]["Food"] if len(lunch) else "-",
            "Dinner": dinner.iloc[i % len(dinner)]["Food"] if len(dinner) else "-",
            "Snack": snack.iloc[i % len(snack)]["Food"] if len(snack) else "-",
            "Workout": workouts.iloc[i % len(workouts)]["Exercise"] if len(workouts) else "Rest",
        })
    return pd.DataFrame(plan)