from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .utils import send_verification_email
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import CustomUser, Course, Subject, Topic, Scenario, LevelOfDifficulty, Question, GeneratedQuiz, Summary, TimeLimit
from django.core.signing import Signer, BadSignature, SignatureExpired
import random
from django.http import HttpResponseBadRequest 
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
signer = Signer()
import json


#                fadgMSMA@2025

# Create your views here.
def landing_page(request):
    return render(request, "appReviewer/landing_page.html", {})

@login_required
def dashboard(request):
    return render(request, "appReviewer/dashboard.html", {})

def my_register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_verified = False
            user.is_active = False
            user.save()
            send_verification_email(user)
            messages.info(request, "Please check and verify email.")
            return redirect("my_register")
    
    else:
        form = RegisterForm()
    return render(request, "auth_pages/my_register.html", {"form": form})


def verify_email(request, token):
    try:
        user_id = signer.unsign(token)  # Decode user ID from token
        user = CustomUser.objects.get(pk=user_id)  # Get the user

        # Mark as verified and active
        user.is_verified = True
        user.is_active = True
        user.save()
        messages.success(request, "Email verified Succesfully")
        return redirect("my_login")
    except SignatureExpired:
        messages.error(request, "Verification link expired. Please register again.")
    except (BadSignature, CustomUser.DoesNotExist):
        print("Email verification failed. Invalid or expired verification link.")
        messages.error(request, "Invalid verification link")



def my_login(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(request, email=email, password=password) # it only checks is_active = True
            if user is None:
                messages.error(request, "Invalid credentials or Account deactivated.")
            elif not user.is_verified:
                messages.info(request, "Please check and verify your email.")
            elif not user.is_active:
                messages.info(request, "Account is deactived")
            else:
                messages.success(request, "Succesfully Loggedin")
                login(request, user)
                return redirect("dashboard")
    context = {"form": form}
    return render(request, "auth_pages/my_login.html", context)


@login_required
def my_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect("my_login")


@login_required
def reviewer(request):
    courses = Course.objects.all()
    subjects = Subject.objects.all()
    exam_duration = TimeLimit.objects.all()
    generated_quiz = GeneratedQuiz.objects.filter(user_id=request.user.id)
    context = {
        "courses":courses,
        "subjects":subjects,
        "exam_duration":exam_duration,
        "generated_quiz": generated_quiz}
    return render(request, "appReviewer/reviewer.html", context)


@login_required
def fetch_subjects(request, course_id):
    subjects = Subject.objects.filter(course_id=course_id)
    return render(request, "partials/subjects.html", {"subjects": subjects})



'''
    DATA STRUCT AND ALGO TASKS:
        number of questions do not work
        add timer
        randomize the scenario based questions and non scenario based question
        shuffle the options
        30% 40% 30% difficulty
    FEATURE RELATED TASKS:
        view feedback
        continue unfinished quiz
'''

@login_required
def generate_questions(request):
    if request.method == "POST" and request.headers.get("HX-Request"):
        # Get user-selected course, subject and duration from the form
        selectedCourse = request.POST.get("selected_course")
        selectedSubject = request.POST.get("selected_subject")
        selectedDuration = request.POST.get("exam_duration")

        course = get_object_or_404(Course, id=int(selectedCourse))
        subject = get_object_or_404(Subject, id=int(selectedSubject), course=course)
        duration = get_object_or_404(TimeLimit, time_duration=int(selectedDuration))

        # Get topics under the selected subject
        topics = Topic.objects.filter(subject=subject)

        # Determine the number of questions to fetch based on duration
        duration_map = {1: 25, 2: 50, 3: 100}
        question_count = duration_map.get(duration.time_duration, 25)

        # Fetch scenario-based questions
        scenario_questions = list(Question.objects.filter(
            topic__in=topics
        ).exclude(scenario__isnull=True).order_by("scenario"))

        grouped_questions = []
        seen_scenarios = set()
        scenario_question_count = 0

        for question in scenario_questions:
            if question.scenario not in seen_scenarios:
                grouped_questions.append({
                    "scenario": question.scenario,
                    "questions": []
                })
                seen_scenarios.add(question.scenario)

            # Add question to its scenario group
            for group in grouped_questions:
                if group["scenario"] == question.scenario:
                    if scenario_question_count < question_count:
                        group["questions"].append(question)
                        scenario_question_count += 1

        # Shuffle scenario questions
        for group in grouped_questions:
            random.shuffle(group["questions"])

        # Fetch non-scenario questions
        remaining_slots = question_count - scenario_question_count
        non_scenario_questions = list(Question.objects.filter(
            topic__in=topics,
            scenario__isnull=True
        ).order_by("?")[:remaining_slots])

        random.shuffle(non_scenario_questions)

        # Merge scenario and non-scenario questions
        final_questions = grouped_questions
        if non_scenario_questions:
            final_questions.append({"scenario": None, "questions": non_scenario_questions})

        # Create and save the GeneratedQuiz instance
        generated_quiz = GeneratedQuiz.objects.create(
            user=request.user,
            subject=subject,
            duration=duration 
        )

        # Assign questions to the quiz
        all_questions = [q for group in final_questions for q in group["questions"]]
        generated_quiz.questions.set(all_questions)

        # Assign scenarios if any
        scenarios = {q.scenario for q in all_questions if q.scenario}
        if scenarios:
            generated_quiz.scenario.set(scenarios)

        # Render the template with grouped questions
        context = {
            "final_questions": final_questions,
            "generated_quiz_id": generated_quiz.id,
            "subject": subject.name,
            "duration":duration.time_duration,
        }
        return render(request, "partials/generated_questions.html", context)

    return HttpResponseBadRequest("Invalid request")






@login_required
def submit_quiz(request):
    if request.method == "POST" and request.headers.get("HX-Request"):
        try:
            # Retrieve and validate generated_quiz_id
            generated_quiz_id = request.POST.get("generated_quiz_id")
            if not generated_quiz_id or not generated_quiz_id.isdigit():
                return HttpResponseBadRequest("Invalid quiz ID.")

            generated_quiz = get_object_or_404(GeneratedQuiz, id=int(generated_quiz_id), user=request.user)

            # Extract user answers dynamically
            user_answers = {}
            for key, value in request.POST.items():
                if key.startswith("answers_"):  # Ensure we only get answers
                    question_id = key.split("_")[1]  # Extract question ID
                    user_answers[question_id] = value  # Store answer

            if not user_answers:
                return HttpResponseBadRequest("No answers received.")

            # Fetch all questions from the generated quiz
            questions = generated_quiz.questions.all()
            correct_questions = []
            incorrect_questions = []
            score = 0


            # determines if user is correct or wrong per question
            for question in questions:
                correct_answer = question.correct_option 
                user_answer = user_answers.get(str(question.id))  # Retrieve stored answer
                if user_answer and user_answer == correct_answer:
                    correct_questions.append(question)
                    score += 1
                else:
                    incorrect_questions.append(question)

            # Save the quiz summary
            summary = Summary.objects.create(
                user=request.user,
                generated_quiz=generated_quiz,
                user_answers=json.dumps(user_answers),
                num_items=len(questions),
                score=score,
            )
            summary.correct_questions.set(correct_questions)
            summary.incorrect_questions.set(incorrect_questions)

            # marks the generated_quiz table to finished = true
            generated_quiz.is_finished = True
            generated_quiz.save()
            # Render result partial
            context = {
                "score": score, 
                "num_items": len(questions),
                }
            return render(request, "partials/quiz_result.html", context)
        except Exception as e:
            return HttpResponseBadRequest(f"Error processing quiz submission: {str(e)}")



# used in sidebar to dynamically show quiz result
@login_required
def fetchquizresult(request, quiz_id):
    quiz = get_object_or_404(GeneratedQuiz, id=quiz_id)
    summaries = Summary.objects.filter(generated_quiz=quiz)  # Get all summaries for debugging
    if summaries.exists():
        summary = summaries.first()
    else:
        summary = None
    # Compute percentage safely
    percentage = 0
    if summary and summary.num_items > 0:
        percentage = (summary.score / summary.num_items) * 100
    context = {
       "quiz": quiz,
       "summary": summary,
       "percentage": percentage,
    }
    return render(request, "partials/fetchquizresult.html", context)




@login_required
def profile(request):
    return render(request, "appReviewer/profile.html")