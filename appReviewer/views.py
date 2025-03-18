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
def show_user_exams(request):
    generated_quiz = GeneratedQuiz.objects.filter(user_id=request.user.id)
    context={
        "generated_quiz": generated_quiz
    }
    return render(request, "appReviewer/show_user_exams.html", context)




@login_required
def fetch_subjects(request, course_id):
    subjects = Subject.objects.filter(course_id=course_id)
    return render(request, "partials/subjects.html", {"subjects": subjects})



'''
    DATA STRUCT AND ALGO TASKS:
        done=====add numbering
        add timer
        done ========(but still grouped by all shuffled scenario and all shuffled non scenario) randomize the scenario based questions and non scenario based question
        partially done =====30% 40% 30% difficulty
        done ======== shuffle options
    FEATURE RELATED TASKS:
        view feedback
        continue unfinished quiz
'''





@login_required
def generate_questions(request):
    if not request.user.is_subscribed:
        return render(request, "error_pages/not_subscribed.html")
    
    if request.method == "POST" and request.headers.get("HX-Request"):
        # Retrieve selected course, subject, and exam duration from the POST request
        selectedCourse = request.POST.get("selected_course")
        selectedSubject = request.POST.get("selected_subject")
        selectedDuration = request.POST.get("exam_duration")

        # Fetch the corresponding Course, Subject (linked to the Course), and TimeLimit objects
        course = get_object_or_404(Course, id=int(selectedCourse))
        subject = get_object_or_404(Subject, id=int(selectedSubject), course=course)
        duration = get_object_or_404(TimeLimit, time_duration=int(selectedDuration))

        # Get all topics related to the selected subject
        topics = Topic.objects.filter(subject=subject)

        # Map duration to a predefined number of questions, defaulting to 25 if not found
        duration_map = {1: 2, 2: 50, 3: 100}
        question_count = duration_map.get(duration.time_duration, 2)

        # Split question count for scenario and non-scenario
        scenario_count = question_count // 2
        non_scenario_count = question_count - scenario_count

        # Calculate difficulty level distribution for scenario based questions
        scenario_easy_count = round(scenario_count * 0.3)
        scenario_moderate_count = round(scenario_count * 0.4)
        scenario_difficult_count = scenario_count - scenario_easy_count - scenario_moderate_count

        # Calculate difficulty level distribution for non-scenario based questions
        non_scenario_easy_count = round(non_scenario_count * 0.3)
        non_scenario_moderate_count = round(non_scenario_count * 0.4)
        non_scenario_difficult_count = non_scenario_count - non_scenario_easy_count - non_scenario_moderate_count

        # Fetch scenario-based questions
        scenario_easy_questions = list(Question.objects.filter(topic__in=topics, level_of_difficulty=1).exclude(scenario__isnull=True).order_by("?")[:scenario_easy_count])
        scenario_moderate_questions = list(Question.objects.filter(topic__in=topics, level_of_difficulty=2).exclude(scenario__isnull=True).order_by("?")[:scenario_moderate_count])
        scenario_difficult_questions = list(Question.objects.filter(topic__in=topics, level_of_difficulty=3).exclude(scenario__isnull=True).order_by("?")[:scenario_difficult_count])

        scenario_questions = scenario_easy_questions + scenario_moderate_questions + scenario_difficult_questions
        random.shuffle(scenario_questions)

        # Fetch non-scenario-based questions
        non_scenario_easy_questions = list(Question.objects.filter(topic__in=topics, level_of_difficulty=1, scenario__isnull=True).order_by("?")[:non_scenario_easy_count])
        non_scenario_moderate_questions = list(Question.objects.filter(topic__in=topics, level_of_difficulty=2, scenario__isnull=True).order_by("?")[:non_scenario_moderate_count])
        non_scenario_difficult_questions = list(Question.objects.filter(topic__in=topics, level_of_difficulty=3, scenario__isnull=True).order_by("?")[:non_scenario_difficult_count])

        non_scenario_questions = non_scenario_easy_questions + non_scenario_moderate_questions + non_scenario_difficult_questions
        random.shuffle(non_scenario_questions)

        # Group scenario questions by scenario
        scenario_groups = {}
        for question in scenario_questions:
            if question.scenario:
                if question.scenario not in scenario_groups:
                    scenario_groups[question.scenario] = []
                # Add the question to the corresponding scenario group
                scenario_groups[question.scenario].append(question)

        # Create a structured list where each entry contains a scenario and its associated questions
        final_questions = []
        for scenario, questions in scenario_groups.items():
            final_questions.append({"scenario": scenario, "questions": questions})

        # If there are questions that don't belong to any scenario, add them as a separate group
        if non_scenario_questions:
            final_questions.append({"scenario": None, "questions": non_scenario_questions})

        # Create a new GeneratedQuiz instance for the user with the specified subject and duration
        generated_quiz = GeneratedQuiz.objects.create(user=request.user, subject=subject, duration=duration)

        # Flatten the grouped questions into a single list to associate them with the generated quiz
        all_questions_list = []
        for group in final_questions:
            all_questions_list.extend(group["questions"])
        
        # Assign all selected questions to the generated quiz
        generated_quiz.questions.set(all_questions_list)

        # Initialize question numbering
        question_number = 1
        for group in final_questions:
            for question in group["questions"]:
                # Assign a sequential number to each question
                question.number = question_number

                # Shuffle answer choices randomly
                options = [("A", question.option_a), ("B", question.option_b), ("C", question.option_c), ("D", question.option_d)]
                random.shuffle(options)

                # Assign the shuffled options back to the question
                question.option_a = options[0][1]
                question.option_b = options[1][1]
                question.option_c = options[2][1]
                question.option_d = options[3][1]

                # Adjust the correct option letter to match the new shuffled choices
                correct_letter = question.correct_option
                for new_letter, option_value in options:
                    if correct_letter == "A" and option_value == question.option_a:
                        question.correct_option = new_letter
                    elif correct_letter == "B" and option_value == question.option_b:
                        question.correct_option = new_letter
                    elif correct_letter == "C" and option_value == question.option_c:
                        question.correct_option = new_letter
                    elif correct_letter == "D" and option_value == question.option_d:
                        question.correct_option = new_letter

                # Increment question number for the next question
                question_number += 1
        context = {
            "final_questions": final_questions,
            "generated_quiz_id": generated_quiz.id,
            "subject": subject.name,
            "duration": duration.time_duration}
        return render(request, "partials/generated_questions.html", context)
    return redirect("reviewer")







@login_required
def submit_quiz(request):
    if not request.user.is_subscribed:
        return render(request, "error_pages/not_subscribed.html")
    
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
                "summary_id": summary.id,
                }
            return render(request, "partials/quiz_result.html", context)
        except Exception as e:
            return HttpResponseBadRequest(f"Error processing quiz submission: {str(e)}")
    return redirect("reviewer")

        





@login_required
def view_feedback(request):
    """
    Displays the feedback for a user's submitted quiz, highlighting incorrect answers.
    """
    # if request.method == "GET" and request.headers.get("HX-Request"):
    summary_id = request.GET.get("summary_id")

    if not summary_id or not summary_id.isdigit():
        return render(request, "partials/view_feedback.html", {"error": "Invalid Summary ID"})

    summary = get_object_or_404(Summary, id=int(summary_id), user=request.user)
    generated_quiz = summary.generated_quiz
    questions = generated_quiz.questions.all()

    user_answers = json.loads(summary.user_answers)  # Load user's answers from JSON

    feedback_data = []
    for question in questions:
        question_data = {
            "question": question,
            "user_answer": user_answers.get(str(question.id)),
            "correct_answer": question.correct_option,
            "options": {
                "A": question.option_a,
                "B": question.option_b,
                "C": question.option_c,
                "D": question.option_d,
            },
            "is_correct": user_answers.get(str(question.id)) == question.correct_option,
        }
        feedback_data.append(question_data)

    context = {
        "feedback_data": feedback_data,
        "summary": summary,
    }

    # Serve partial for HTMX requests
    if request.headers.get("HX-Request"):
        return render(request, "partials/view_feedback.html", context)

    # Serve full page template for direct URL access or page refresh
    return redirect("reviewer")
      
       







@login_required
def fetchquizresult(request, quiz_id):
    quiz = get_object_or_404(GeneratedQuiz, id=quiz_id)
    summaries = Summary.objects.filter(generated_quiz=quiz)
    if summaries.exists():
        summary = summaries.first()
        summary_id = summary.id
    else:
        summary = None
        summary_id = None #add this line
    # Compute percentage safely
    percentage = 0
    if summary and summary.num_items > 0:
        percentage = (summary.score / summary.num_items) * 100

    context = {
        "quiz": quiz,
        "summary": summary,
        "percentage": percentage,
        "summary_id": summary_id,
    }
    if request.headers.get("HX-Request"):
        return render(request, "partials/fetchquizresult.html", context)
    return redirect('reviewer')




@login_required
def profile(request):
    return render(request, "appReviewer/profile.html")