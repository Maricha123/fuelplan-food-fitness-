import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from recommender import (
    bmi, bmi_class, bmr_mifflin, tdee, target_calories, macro_targets,
    recommend_foods, similar_foods, recommend_exercises, weekly_plan,
    water_intake_target,
)

# ----------------------------------------------------------------------------
# Page config + theme
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Food & Fitness Recommender",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#2D6A4F"      # deep forest green
ACCENT = "#EF6461"       # warm coral
GOLD = "#F4A259"         # gold highlight
BG = "#F5F7F2"           # cool off-white, sage-tinted
CARD = "#FFFFFF"
INK = "#1F2620"          # near-black charcoal-green
MUTED = "#5B6660"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"]  {{
    font-family: 'Inter', sans-serif;
    color: {INK};
}}
.stApp {{
    background: {BG};
}}
h1, h2, h3, h4 {{
    font-family: 'Space Grotesk', sans-serif !important;
    color: {INK} !important;
    letter-spacing: -0.01em;
}}
[data-testid="stSidebar"] {{
    background: {INK};
}}
[data-testid="stSidebar"] * {{
    color: #EAF0EA !important;
}}
[data-testid="stSidebar"] .stButton button {{
    background: {ACCENT};
    color: white;
    border: none;
    font-weight: 600;
}}
.hero {{
    background: linear-gradient(120deg, {PRIMARY} 0%, #1B4332 100%);
    padding: 28px 32px;
    border-radius: 18px;
    color: white;
    margin-bottom: 22px;
}}
.hero h1 {{ color: white !important; margin-bottom: 4px; font-size: 2rem; }}
.hero p {{ color: #D8E8DC; margin: 0; font-size: 0.95rem; }}
.metric-card {{
    background: {CARD};
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border-left: 5px solid {PRIMARY};
}}
.metric-card .label {{
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {MUTED};
    font-weight: 600;
}}
.metric-card .value {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: {INK};
}}
.section-eyebrow {{
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.75rem;
    font-weight: 600;
    color: {ACCENT};
    margin-bottom: -6px;
}}
div[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
}}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    food = pd.read_csv("food_nutrition.csv")
    ex = pd.read_csv("exercises.csv")
    return food, ex


food_df, ex_df = load_data()

# ----------------------------------------------------------------------------
# Sidebar — user inputs
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌱 Your Profile")
    st.caption("Built on 323 real foods + 30 evidence-based exercises")

    age = st.slider("Age", 15, 75, 24)
    gender = st.radio("Gender", ["male", "female"], horizontal=True)
    col_a, col_b = st.columns(2)
    height_cm = col_a.number_input("Height (cm)", 120.0, 220.0, 170.0, step=0.5)
    weight_kg = col_b.number_input("Weight (kg)", 35.0, 180.0, 68.0, step=0.5)

    activity_level = st.selectbox(
        "Activity level",
        ["sedentary", "light", "moderate", "active", "very_active"],
        index=2,
        format_func=lambda x: {
            "sedentary": "Sedentary (little/no exercise)",
            "light": "Light (1-3 days/week)",
            "moderate": "Moderate (3-5 days/week)",
            "active": "Active (6-7 days/week)",
            "very_active": "Very active (athlete / physical job)",
        }[x],
    )

    goal = st.selectbox(
        "Goal",
        ["lose_weight", "maintain", "gain_muscle"],
        format_func=lambda x: {"lose_weight": "Lose weight", "maintain": "Maintain", "gain_muscle": "Gain muscle"}[x],
    )

    diet_pref = st.selectbox(
        "Diet preference",
        ["none", "vegetarian", "vegan", "high-protein", "low-carb"],
    )

    minutes = st.slider("Minutes available to exercise / day", 10, 90, 30, step=5)
    equipment = st.multiselect(
        "Equipment you have access to",
        ["dumbbells", "barbell", "resistance band", "bicycle", "pool", "pull-up bar",
         "mat", "rowing machine", "elliptical machine", "jump rope", "ball", "gloves"],
        default=["dumbbells", "mat"],
    )

    generate = st.button("🔄 Generate my plan", width='stretch')

# ----------------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------------
st.markdown(f"""
<div class="hero">
  <h1>Food & Fitness Recommender</h1>
  <p>Personalized food & fitness recommendations, built from real nutrition data and MET-based exercise science.</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Compute metrics
# ----------------------------------------------------------------------------
b = bmi(weight_kg, height_cm)
bclass = bmi_class(b)
bmr_val = bmr_mifflin(weight_kg, height_cm, age, gender)
tdee_val = tdee(bmr_val, activity_level)
target = target_calories(tdee_val, goal)
protein_g, carbs_g, fat_g = macro_targets(target, goal)
water_l = water_intake_target(weight_kg, minutes)

m1, m2, m3, m4, m5 = st.columns(5)
for col, label, value, sub in [
    (m1, "BMI", f"{b}", bclass.capitalize()),
    (m2, "BMR", f"{bmr_val:.0f} kcal", "resting energy use"),
    (m3, "TDEE", f"{tdee_val:.0f} kcal", "total daily burn"),
    (m4, "Target intake", f"{target:.0f} kcal", goal.replace('_', ' ').title()),
    (m5, "Water", f"{water_l:.1f} L", f"~{water_l*4.2:.0f} glasses/day"),
]:
    col.markdown(f"""
    <div class="metric-card">
      <div class="label">{label}</div>
      <div class="value">{value}</div>
      <div style="color:{MUTED}; font-size:0.82rem; margin-top:2px;">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# BMI gauge + macro donut
g1, g2 = st.columns([1, 1])

with g1:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=b,
        number={"suffix": " BMI"},
        gauge={
            "axis": {"range": [10, 40]},
            "bar": {"color": INK},
            "steps": [
                {"range": [10, 18.5], "color": "#A9D6E5"},
                {"range": [18.5, 25], "color": "#95D5B2"},
                {"range": [25, 30], "color": "#F4A259"},
                {"range": [30, 40], "color": "#EF6461"},
            ],
        },
        title={"text": "BMI Range (underweight → obese)"},
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width='stretch')

with g2:
    macro_fig = px.pie(
        names=["Protein", "Carbs", "Fat"],
        values=[protein_g * 4, carbs_g * 4, fat_g * 9],
        color_discrete_sequence=[PRIMARY, GOLD, ACCENT],
        hole=0.55,
        title="Daily Macro Split (by calories)",
    )
    macro_fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(macro_fig, width='stretch')

st.caption(f"Target macros → Protein: **{protein_g:.0f}g** · Carbs: **{carbs_g:.0f}g** · Fat: **{fat_g:.0f}g**")

st.divider()

# ----------------------------------------------------------------------------
# Food recommendations
# ----------------------------------------------------------------------------
st.markdown('<div class="section-eyebrow">Recommendations</div>', unsafe_allow_html=True)
st.markdown("## 🍽️ Foods matched to your goal")

meal_tab, similar_tab = st.tabs(["By meal type", "Find similar foods"])

with meal_tab:
    meal_type = st.radio("Meal", ["breakfast", "lunch", "dinner", "snack"], horizontal=True, key="meal_radio")
    recs = recommend_foods(food_df, goal, diet_pref, meal_type, top_n=12)
    if recs.empty:
        st.warning("No foods match that combination — try a different diet preference.")
    else:
        c1, c2 = st.columns([1.3, 1])
        with c1:
            st.dataframe(
                recs[["Food", "Category", "Calories_per100g", "Protein_per100g", "Carbs_per100g", "Fat_per100g", "HealthScore"]]
                .rename(columns={
                    "Calories_per100g": "kcal/100g", "Protein_per100g": "Protein g/100g",
                    "Carbs_per100g": "Carbs g/100g", "Fat_per100g": "Fat g/100g", "HealthScore": "Health Score"
                }),
                width='stretch', hide_index=True, height=420,
            )
        with c2:
            bar = px.bar(
                recs.sort_values("FitScore"), x="FitScore", y="Food", orientation="h",
                color_discrete_sequence=[PRIMARY], title=f"Top matches for {meal_type}",
            )
            bar.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(bar, width='stretch')

with similar_tab:
    food_choice = st.selectbox("Pick a food you like", food_df["Food"] + " (" + food_df["FoodID"] + ")")
    chosen_id = food_choice.split("(")[-1].rstrip(")")
    sims = similar_foods(food_df, chosen_id, top_n=6)
    st.write("Nutritionally similar foods (cosine similarity on macro profile):")
    st.dataframe(
        sims[["Food", "Category", "Calories_per100g", "Protein_per100g", "Fat_per100g", "Carbs_per100g"]],
        width='stretch', hide_index=True,
    )

st.divider()

# ----------------------------------------------------------------------------
# Exercise recommendations
# ----------------------------------------------------------------------------
st.markdown('<div class="section-eyebrow">Recommendations</div>', unsafe_allow_html=True)
st.markdown("## 🏋️ Workouts for your session")

ex_recs = recommend_exercises(ex_df, goal, weight_kg, minutes, equipment_available=equipment or ["none"], top_n=10)
if ex_recs.empty:
    st.warning("No exercises match your equipment + goal combo — try adding equipment.")
else:
    e1, e2 = st.columns([1, 1.2])
    with e1:
        st.dataframe(
            ex_recs[["Exercise", "Category", "Intensity", "Equipment", "EstKcalBurned"]]
            .rename(columns={"EstKcalBurned": f"Est. kcal / {minutes} min"}),
            width='stretch', hide_index=True, height=380,
        )
    with e2:
        ebar = px.bar(
            ex_recs.sort_values("EstKcalBurned"), x="EstKcalBurned", y="Exercise", orientation="h",
            color="Category", color_discrete_sequence=[PRIMARY, ACCENT, GOLD],
            title=f"Estimated kcal burned in {minutes} min",
        )
        ebar.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(ebar, width='stretch')

st.divider()

# ----------------------------------------------------------------------------
# Weekly plan
# ----------------------------------------------------------------------------
st.markdown('<div class="section-eyebrow">7-day outlook</div>', unsafe_allow_html=True)
st.markdown("## 📅 Sample weekly plan")

plan_df = weekly_plan(food_df, ex_df, goal, diet_pref, weight_kg, minutes)
st.dataframe(plan_df, width='stretch', hide_index=True)

from datetime import date
import io

def build_report_text():
    lines = []
    lines.append("=" * 60)
    lines.append("FUELPLAN — PERSONAL FOOD & FITNESS REPORT")
    lines.append(f"Generated: {date.today().isoformat()}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("YOUR PROFILE")
    lines.append("-" * 60)
    lines.append(f"Age: {age}   Gender: {gender}   Height: {height_cm} cm   Weight: {weight_kg} kg")
    lines.append(f"Activity level: {activity_level}   Goal: {goal.replace('_',' ').title()}")
    lines.append(f"Diet preference: {diet_pref}   Exercise time/day: {minutes} min")
    lines.append("")
    lines.append("KEY NUMBERS")
    lines.append("-" * 60)
    lines.append(f"BMI: {b} ({bclass})")
    lines.append(f"BMR: {bmr_val:.0f} kcal/day")
    lines.append(f"TDEE: {tdee_val:.0f} kcal/day")
    lines.append(f"Target intake: {target:.0f} kcal/day")
    lines.append(f"Macro targets: Protein {protein_g:.0f}g | Carbs {carbs_g:.0f}g | Fat {fat_g:.0f}g")
    lines.append(f"Water intake target: {water_l:.1f} L/day (~{water_l*4.2:.0f} glasses)")
    lines.append("")
    lines.append("RECOMMENDED FOODS (top matches, all meal types)")
    lines.append("-" * 60)
    for meal in ["breakfast", "lunch", "dinner", "snack"]:
        meal_recs = recommend_foods(food_df, goal, diet_pref, meal, top_n=5)
        lines.append(f"\n{meal.title()}:")
        for _, r in meal_recs.iterrows():
            lines.append(f"  - {r['Food']} ({r['Calories_per100g']:.0f} kcal, {r['Protein_per100g']:.0f}g protein /100g)")
    lines.append("")
    lines.append("RECOMMENDED WORKOUTS")
    lines.append("-" * 60)
    for _, r in ex_recs.iterrows():
        lines.append(f"  - {r['Exercise']} ({r['Intensity']}) — ~{r['EstKcalBurned']:.0f} kcal in {minutes} min")
    lines.append("")
    lines.append("WEEKLY PLAN")
    lines.append("-" * 60)
    for _, r in plan_df.iterrows():
        lines.append(f"{r['Day']}: Breakfast: {r['Breakfast']} | Lunch: {r['Lunch']} | "
                      f"Dinner: {r['Dinner']} | Snack: {r['Snack']} | Workout: {r['Workout']}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("Generated by FuelPlan — a rule-based + content-based recommendation system")
    return "\n".join(lines)

def build_report_pdf():
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    PRIMARY_C = colors.HexColor(PRIMARY)
    ACCENT_C = colors.HexColor(ACCENT)
    INK_C = colors.HexColor(INK)
    MUTED_C = colors.HexColor(MUTED)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleFP", parent=styles["Title"], textColor=PRIMARY_C, fontSize=22, spaceAfter=2)
    subtitle_style = ParagraphStyle("SubtitleFP", parent=styles["Normal"], textColor=MUTED_C, fontSize=10, spaceAfter=14)
    h2 = ParagraphStyle("H2FP", parent=styles["Heading2"], textColor=PRIMARY_C, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("BodyFP", parent=styles["Normal"], fontSize=10, textColor=INK_C, leading=14)
    small = ParagraphStyle("SmallFP", parent=styles["Normal"], fontSize=8, textColor=MUTED_C, alignment=TA_CENTER)

    story = []
    story.append(Paragraph("FuelPlan", title_style))
    story.append(Paragraph(f"Personal Food &amp; Fitness Report — Generated {date.today().isoformat()}", subtitle_style))
    story.append(HRFlowable(width="100%", color=PRIMARY_C, thickness=1))

    story.append(Paragraph("Your Profile", h2))
    profile_data = [
        ["Age", str(age), "Gender", gender.title()],
        ["Height", f"{height_cm} cm", "Weight", f"{weight_kg} kg"],
        ["Activity level", activity_level.replace("_", " ").title(), "Goal", goal.replace("_", " ").title()],
        ["Diet preference", diet_pref.title(), "Exercise time/day", f"{minutes} min"],
    ]
    t = Table(profile_data, colWidths=[110, 140, 110, 140])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK_C),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
    ]))
    story.append(t)

    story.append(Paragraph("Key Numbers", h2))
    key_data = [
        ["BMI", f"{b} ({bclass})", "BMR", f"{bmr_val:.0f} kcal/day"],
        ["TDEE", f"{tdee_val:.0f} kcal/day", "Target intake", f"{target:.0f} kcal/day"],
        ["Protein target", f"{protein_g:.0f} g", "Carbs target", f"{carbs_g:.0f} g"],
        ["Fat target", f"{fat_g:.0f} g", "Water intake", f"{water_l:.1f} L/day"],
    ]
    t2 = Table(key_data, colWidths=[110, 140, 110, 140])
    t2.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK_C),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
    ]))
    story.append(t2)

    story.append(Paragraph("Recommended Foods", h2))
    for meal in ["breakfast", "lunch", "dinner", "snack"]:
        meal_recs = recommend_foods(food_df, goal, diet_pref, meal, top_n=5)
        story.append(Paragraph(f"<b>{meal.title()}</b>", body))
        rows = [["Food", "kcal/100g", "Protein g/100g"]]
        for _, r in meal_recs.iterrows():
            rows.append([r["Food"], f"{r['Calories_per100g']:.0f}", f"{r['Protein_per100g']:.0f}"])
        mt = Table(rows, colWidths=[280, 90, 130])
        mt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_C),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F2")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(mt)
        story.append(Spacer(1, 8))

    story.append(Paragraph("Recommended Workouts", h2))
    ex_rows = [["Exercise", "Intensity", f"Est. kcal / {minutes} min"]]
    for _, r in ex_recs.iterrows():
        ex_rows.append([r["Exercise"], r["Intensity"].title(), f"{r['EstKcalBurned']:.0f}"])
    ext = Table(ex_rows, colWidths=[260, 110, 130])
    ext.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT_C),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F2")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(ext)

    story.append(Paragraph("Weekly Plan", h2))
    plan_rows = [["Day", "Breakfast", "Lunch", "Dinner", "Snack", "Workout"]]
    for _, r in plan_df.iterrows():
        plan_rows.append([r["Day"], r["Breakfast"], r["Lunch"], r["Dinner"], r["Snack"], r["Workout"]])
    pt = Table(plan_rows, colWidths=[55, 90, 90, 90, 80, 95], repeatRows=1)
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_C),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F2")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(pt)

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#E0E0E0"), thickness=0.5))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Generated by FuelPlan — a rule-based + content-based food &amp; fitness recommendation system.",
        small,
    ))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

dl1, dl2, dl3 = st.columns(3)
with dl1:
    csv_buf = io.StringIO()
    plan_df.to_csv(csv_buf, index=False)
    st.download_button(
        "⬇️ Weekly plan (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"fuelplan_weekly_plan_{date.today().isoformat()}.csv",
        mime="text/csv",
        width='stretch',
    )
with dl2:
    st.download_button(
        "⬇️ Full report (TXT)",
        data=build_report_text(),
        file_name=f"fuelplan_report_{date.today().isoformat()}.txt",
        mime="text/plain",
        width='stretch',
    )
with dl3:
    st.download_button(
        "⬇️ Full report (PDF)",
        data=build_report_pdf(),
        file_name=f"fuelplan_report_{date.today().isoformat()}.pdf",
        mime="application/pdf",
        width='stretch',
    )

st.caption(
    "FuelPlan combines rule-based filtering (diet, meal type, goal) with content-based "
    "filtering (cosine similarity on nutrient vectors) over a cleaned nutrition dataset "
    "and a MET-based exercise table. Built for a university food & fitness recommender project."
)
