from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render, redirect
from .utils import send_verification_email
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import CustomUser, Category, Scenario, LevelOfDifficulty, Question
from django.core.signing import Signer, BadSignature, SignatureExpired
import random
from django.http import HttpResponseBadRequest  # For returning a 400 Bad Request response
from django.shortcuts import get_object_or_404  # For fetching an object or returning a 404 response if not found
from django.contrib.auth import authenticate, login, logout
signer = Signer()


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
    categories = Category.objects.all()
    difficulties = LevelOfDifficulty.objects.all()
    context = {"categories": categories, "difficulties": difficulties}
    return render(request, "appReviewer/reviewer.html", context)



@login_required
def generate_questions(request):
    if request.method == "POST" and request.headers.get("HX-Request"):
        # Get user-selected category, difficulty, and question count from the form
        category_name = request.POST.get("category")
        question_count = int(request.POST.get("question_count"))
        difficulty_name = request.POST.get("difficulty")

        # Fetch Category and LevelOfDifficulty objects from the database
        category = get_object_or_404(Category, name=category_name)
        difficulty = get_object_or_404(LevelOfDifficulty, name__iexact=difficulty_name)

        # Get all questions that have a scenario (grouped by scenario)
        scenario_questions = list(Question.objects.filter(
            category=category,
            level_of_difficulty=difficulty
        ).exclude(scenario__isnull=True).order_by("scenario"))

        # Group questions by scenario (only add a scenario once)
        grouped_questions = []
        seen_scenarios = set()
        scenario_question_count = 0  # Track how many scenario questions are included

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
        
        #  Shuffle questions **inside each scenario**
        for group in grouped_questions:
            random.shuffle(group["questions"])  

        # Get non-scenario questions, ensuring we don’t exceed question_count
        remaining_slots = question_count - scenario_question_count
        non_scenario_questions = list(Question.objects.filter(
            category=category,
            level_of_difficulty=difficulty,
            scenario__isnull=True
        ).order_by("?")[:remaining_slots])

        #  Shuffle non-scenario questions before adding them
        random.shuffle(non_scenario_questions)

        # Merge scenario-based questions with non-scenario questions
        final_questions = grouped_questions
        if non_scenario_questions:
            final_questions.append({"scenario": None, "questions": non_scenario_questions})

        #  Saving functionality (COMMENTED OUT for now)  
        # Uncomment when ready to store the generated quiz in the database  

        # # Create a GeneratedQuiz instance and save it  
        # generated_quiz = GeneratedQuiz.objects.create(
        #     user=request.user,  
        #     category=category,  
        #     number_of_questions=len(scenario_questions) + len(non_scenario_questions)  
        # )  

        # # Extract all selected questions and save them in ManyToMany field  
        # all_questions = [q for group in final_questions for q in group["questions"]]  
        # generated_quiz.questions.set(all_questions)  # Assigns questions to the quiz  

        # Render the template with grouped questions
        context = {
            "final_questions": final_questions,
            "category_name": category_name,
            "difficulty_name": difficulty_name
        }
        return render(request, "partials/generated_questions.html", context)

    return HttpResponseBadRequest("Invalid request")



@login_required
def submit_quiz(request):
    if request.method == "POST" and request.headers.get("HX-Request"):
        score = 1
        context= {"score": score}
        return render(request, "partials/quiz_result.html", context)
    return HttpResponseBadRequest("Invalid Request")



@login_required
def profile(request):
    return render(request, "appReviewer/profile.html")