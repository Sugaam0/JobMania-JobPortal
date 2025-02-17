from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from account.models import User
from jobapp.models import Category


class EmployeeRegistrationForm(UserCreationForm):
    skills = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter your skills, separated by commas.'}),
        required=False,
        label="Skills"
    )
    interested_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Use forms.SelectMultiple for dropdown instead
        required=False,
        label="Interested Categories"
    )
    profile_image = forms.ImageField(required=False, label="Profile Image")
    about_me = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Write something about yourself.'}),
        required=False,
        label="About Me"
    )

    def __init__(self, *args, **kwargs):
        UserCreationForm.__init__(self, *args, **kwargs)
        self.fields['gender'].required = True
        self.fields['first_name'].label = "First Name :"
        self.fields['last_name'].label = "Last Name :"
        self.fields['password1'].label = "Password :"
        self.fields['password2'].label = "Confirm Password :"
        self.fields['email'].label = "Email :"
        self.fields['gender'].label = "Gender :"
        self.fields['resume'].label = "Resume (JPG Format) :"
        self.fields['profile_image'].label = "Upload Profile Image :"
        self.fields['about_me'].label = "About Me :"

        # Adding placeholders
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Enter First Name'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'Enter Last Name'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Enter Email'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Enter Password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm Password'})
        self.fields['about_me'].widget.attrs.update({'placeholder': 'Write something about yourself'})

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2', 'gender', 'resume', 'profile_image', 'interested_categories', 'skills', 'about_me']

    def clean_gender(self):
        gender = self.cleaned_data.get('gender')
        if not gender:
            raise forms.ValidationError("Gender is required")
        return gender
    
    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            if not resume.name.endswith(".jpg"):
                raise forms.ValidationError("The resume must be in .jpg format.")
            if resume.size > 2 * 1024 * 1024:  # 2 MB limit
                raise forms.ValidationError("The resume file size should not exceed 2 MB.")
        return resume

    def save(self, commit=True):
        user = UserCreationForm.save(self, commit=False)
        user.role = "employee"
        user.resume = self.cleaned_data.get('resume')
        user.profile_image = self.cleaned_data.get('profile_image') or 'default-image.jpg'  # Set default if no image is uploaded
        user.about_me = self.cleaned_data.get('about_me')  # Save the About Me field
        if commit:
            user.save()
            user.interested_categories.set(self.cleaned_data.get('interested_categories'))
            skills = self.cleaned_data.get('skills')
            if skills:
                user.skills = skills  # Store skills as a string
                user.save()
        return user


class EmployerRegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        UserCreationForm.__init__(self, *args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['first_name'].label = "Company Name"
        self.fields['last_name'].label = "Company Address"
        self.fields['password1'].label = "Password"
        self.fields['password2'].label = "Confirm Password"

        # Adding placeholders
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Enter Company Name'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'Enter Company Address'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Enter Email'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Enter Password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm Password'})

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = UserCreationForm.save(self, commit=False)
        user.role = "employer"
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password = forms.CharField(strip=False, widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            self.user = authenticate(email=email, password=password)
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise forms.ValidationError("User Does Not Exist.")

            if not user.check_password(password):
                raise forms.ValidationError("Password Does not Match.")

            if not user.is_active:
                raise forms.ValidationError("User is not Active.")

        return super(UserLoginForm, self).clean(*args, **kwargs)

    def get_user(self):
        return self.user


class EmployeeProfileEditForm(forms.ModelForm):
    skills = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter your skills, separated by commas.'}),
        required=False,
        label="Skills"
    )
    profile_image = forms.ImageField(required=False, label="Update Profile Image")
    about_me = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Write something about yourself.'}),
        required=False,
        label="About Me"
    )

    def __init__(self, *args, **kwargs):
        super(EmployeeProfileEditForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Enter First Name'})
        self.fields['last_name'].widget.attrs.update({'placeholder': 'Enter Last Name'})

    class Meta:
        model = User
        fields = ["first_name", "last_name", "gender", "resume", "skills", "profile_image", "about_me"]
