from django import forms
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(
        max_length=50,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        error_messages={"required": "Password is required."},
    ) 
    password_confirmation = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        error_messages={"required": "Please confirm your password."},
    )
    class Meta:
        model = CustomUser
        fields = ["email", "password"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
   

    # enusre email is unique
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already used")
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get("password")
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(str(e))
        return password

    # used clean(self) because we check 2 fields.
    def clean(self):
        cleaned_data = super().clean()  #fetches the email, pass and c_pass
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("password_confirmation")

        if password != password_confirmation:
            self.add_error("password_confirmation", "Passwords do not match.")
        return cleaned_data
    



class LoginForm(forms.Form):
    email = forms.EmailField(
        label="",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="",
        max_length = 50,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )