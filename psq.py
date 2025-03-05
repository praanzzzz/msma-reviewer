import os
import django
import random
from datetime import timedelta

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projectReviewer.settings")  
django.setup()

from appReviewer.models import Scenario, Question, Topic, LevelOfDifficulty 

# Sample Lorem Ipsum Data
lorem_text = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
    "Duis aute irure dolor in reprehenderit in voluptate velit esse.",
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia.",
]

# Ensure Level of Difficulty exists
difficulty_levels = ["Easy", "Moderate", "Difficult"]
difficulties = {level: LevelOfDifficulty.objects.get_or_create(name=level)[0] for level in difficulty_levels}

# Fetch all topics
topics = Topic.objects.all()

if not topics.exists():
    print("❌ No topics found! Please add topics first.")
else:
    # Create Scenarios (2 per topic)
    scenarios = []
    for topic in topics:
        for i in range(2):  # 2 scenarios per topic
            scenario, created = Scenario.objects.get_or_create(
                name=f"Scenario {i+1} for {topic.name}",
                topic=topic
            )
            scenarios.append(scenario)

    # Create Questions (5 per topic, some linked to scenarios)
    for topic in topics:
        for i in range(5):  # 5 questions per topic
            scenario = random.choice(scenarios) if random.random() > 0.5 else None  # 50% chance of having a scenario
            question = Question.objects.create(
                topic=topic,
                scenario=scenario,
                level_of_difficulty=random.choice(list(difficulties.values())),
                question_text=random.choice(lorem_text),
                option_a="Option A",
                option_b="Option B",
                option_c="Option C",
                option_d="Option D",
                correct_option=random.choice(["A", "B", "C", "D"])
            )

    print("✅ Sample Scenarios and Questions added successfully!")
