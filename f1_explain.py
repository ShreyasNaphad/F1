import json
from groq import Groq
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # loads .env file

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# -----------------------------
# 1. Load driver knowledge
# -----------------------------
with open("driver_knowledge.json", "r") as f:
    DRIVER_KNOWLEDGE = json.load(f)



# -----------------------------
# 3. Context helpers
# -----------------------------
def get_driver_context(driver_name):
    return [
        d for d in DRIVER_KNOWLEDGE
        if d["surname"].lower() == driver_name.lower()
    ]


def get_comparison_context(driver_a, driver_b):
    return [
        d for d in DRIVER_KNOWLEDGE
        if d["surname"].lower() in [driver_a.lower(), driver_b.lower()]
    ]


# -----------------------------
# 4. System prompts
# -----------------------------
SYSTEM_PROMPT = """
You are a Formula 1 race analyst and storyteller.

RULES YOU MUST FOLLOW:
- Use the provided statistics ONLY for internal reasoning.
- DO NOT show raw numbers, calculations, or metric values to the user.
- DO NOT mention terms like delta_vs_team, finish_std, or reliability labels.
- Translate statistics into natural F1 language.
- Explain performance like a race analyst on a broadcast.
- Focus on driving style, consistency, pressure handling, and car extraction.
- Be engaging, intuitive, and insightful.
- If the data is insufficient, say:
  "There isn't enough historical data to make a confident comparison."

Your goal is to make the user FEEL like they understand F1 better,
not like they are reading a technical report.
"""


# -----------------------------
# 5. Single-driver explanation
# -----------------------------
def explain_driver(driver_name, question):
    context = get_driver_context(driver_name)

    if not context:
        return "Insufficient data to answer based on available statistics."

    prompt = f"""
{SYSTEM_PROMPT}

Driver data:
{context}

Question:
{question}

Answer:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=900
    )

    return response.choices[0].message.content


# -----------------------------
# 6. Driver comparison
# -----------------------------
def compare_drivers(driver_a, driver_b):
    context = get_comparison_context(driver_a, driver_b)

    if len(context) < 2:
        return "Insufficient data to compare the selected drivers."

    prompt = f"""
{SYSTEM_PROMPT}

Driver A data:
{context[0]}

Driver B data:
{context[1]}

Compare {driver_a} and {driver_b} based on:
- skill relative to car
- consistency
- reliability

Answer:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=800
    )

    return response.choices[0].message.content


# 7. Similarity Explanation (NEW)
# -----------------------------
def explain_similarity_multi(target_driver, matches):
    """
    Explains the connection between the target and the 3 matches found by vectors.
    """
    match_names = [m['surname'] for m in matches]

    prompt = f"""
    {SYSTEM_PROMPT}

    Context:
    We performed a Vector Cosine Similarity search on '{target_driver}'.
    The algorithm identified these 3 drivers as the closest statistical matches:
    {match_names}

    Task:
    Write a short segment (as a commentator) explaining the common thread between these drivers.
    - Do they all share a specific driving style (e.g. Smooth, Aggressive)?
    - Are they all World Champion caliber or Midfield consistent scorers?
    - Do NOT mention "Cosine Similarity" or "Vectors". Use terms like "Profile", "Career Trajectory", "Driving DNA".
     Negative Constraint:
    - NO "Commentator:" prefixes.
    - NO "(Music)" or stage directions.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=700
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Connection Error: {e}"


def narrate_race_story(stats):
    """Race Rewind Narrative"""
    fact_sheet = f"""
    Event: {stats['year']} {stats['gp_name']}
    Driver: {stats['driver']} ({stats['team']})
    Start: P{stats['grid']} | Finish: P{stats['finish']}
    Result Status: {stats['status']}
    Positions Gained: {stats['delta']}
    """

    prompt = f"""
    You are the narrator of a Formula 1 documentary series.

    DATA ANCHORS:
    {fact_sheet}

    TASK:
    Write a dramatic, 150-word recap of this race specifically from {stats['driver']}'s perspective.

    INSTRUCTIONS:
    1. Use your internal knowledge of the {stats['year']} {stats['gp_name']} to mention real incidents if known.
    2. If specific incidents are unknown, focus purely on the tactical drive based on the Data Anchors.
    3. NO script labels. Just the story.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=700
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Connection Error: {e}"

