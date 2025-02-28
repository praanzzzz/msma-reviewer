from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.hashers import make_password


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

    # Ensure password is always hashed before saving
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs) 

    def __str__(self):
        return self.email
    



class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

class Scenario(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    scene = models.TextField()
    image = models.ImageField(upload_to='scenario_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.scene}"



class LevelOfDifficulty(models.Model):
    LEVEL_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]
    name = models.CharField(max_length=10, choices=LEVEL_CHOICES, unique=True)

    def __str__(self):
        return self.name

class Question(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True, blank=True)
    level_of_difficulty = models.ForeignKey(LevelOfDifficulty, on_delete=models.CASCADE)
    question_text = models.TextField()
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)
    option_a = models.TextField()  
    option_b = models.TextField()  
    option_c = models.TextField() 
    option_d = models.TextField()  
    correct_option = models.CharField(
        max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )

    def __str__(self):
        return self.question_text
    


class GeneratedQuiz(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    number_of_questions = models.IntegerField()
    questions = models.ManyToManyField(Question)  # Many-to-Many with Question
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz by {self.user.email} on {self.category.name}"