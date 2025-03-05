from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from datetime import timedelta


# enables email verification instead of username
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        """Creates and saves a superuser with the given email and password."""
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_subscribed', True)

        return self.create_user(email, password, **extra_fields)




class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_subscribed = models.BooleanField(default=False)
    username = None
    first_name = None
    last_name = None
    # default values of AbstractUser: password, is_staff, is_active, is_superuser, date_joined, last_login

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Ensures password is always hashed before saving
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs) 

    def __str__(self):
        return self.email
    





class Course(models.Model):
    name = models.CharField(max_length=70)
    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.name} ------------{self.course}"
    

class Topic(models.Model):
    name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.name} --------{self.subject}"
    

class Scenario(models.Model):
    name = models.TextField()
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='scenario_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


class LevelOfDifficulty(models.Model):
    LEVEL_CHOICES = [
        ('Easy', 'Easy'),
        ('Moderate', 'Moderate'),
        ('Difficult', 'Difficult'),
    ]
    name = models.CharField(max_length=13, choices=LEVEL_CHOICES, unique=True)

    def __str__(self):
        return self.name



class Question(models.Model):
    question_text = models.TextField()
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)
    option_a = models.TextField()  
    option_b = models.TextField()  
    option_c = models.TextField() 
    option_d = models.TextField()  
    correct_option = models.CharField(
        max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True, blank=True)
    level_of_difficulty = models.ForeignKey(LevelOfDifficulty, on_delete=models.CASCADE)

    def __str__(self):
        return self.question_text
    


class TimeLimit(models.Model):
    TIME_LIMIT_CHOICES = [
            (1, "1 hour"),
            (2, "2 hours"),
            (3, "3 hours") 
        ]
    time_duration = models.IntegerField(choices=TIME_LIMIT_CHOICES)

    class Meta:
        ordering = ['time_duration'] 

    def __str__(self):
        return self.get_time_duration_display()



class GeneratedQuiz(models.Model):
    # id as identifier
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    duration = models.ForeignKey(TimeLimit, on_delete = models.CASCADE, null=True)
    scenario = models.ManyToManyField(Scenario, blank=True) 
    questions = models.ManyToManyField(Question)
    created_at = models.DateTimeField(auto_now_add=True)
    is_finished = models.BooleanField(default = False)

    class Meta:
        ordering = ['-created_at'] 

    def __str__(self):
        return f"Quiz {self.id} by {self.user.email} - {self.subject.name} "



class Summary(models.Model):
    # id as identifier
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    generated_quiz = models.ForeignKey(GeneratedQuiz, on_delete=models.CASCADE, related_name="summaries")
    user_answers = models.JSONField(default=dict)  # Example: {"5": "A", "7": "C"}
    correct_questions = models.ManyToManyField(Question, related_name="correct_answers", blank=True)
    incorrect_questions = models.ManyToManyField(Question, related_name="incorrect_answers", blank=True)
    score = models.IntegerField()
    num_items = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] 

    def __str__(self):
        return (f"Summary {self.id} by {self.user.email} - {self.generated_quiz.subject.name} | {self.score}/{self.num_items}")