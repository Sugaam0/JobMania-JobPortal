from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import accountType
from .models import User
from jobapp.models import Category

class AddUserForm(forms.ModelForm):
    """
    New User Form. Requires password confirmation.
    """
    skills = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter skills separated by commas.'}),
        required=False,
        label="Skills"
    )
    interested_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Interested Categories"
    )
    profile_image = forms.ImageField(required=False, label="Profile Image")
    about_me = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Write something about yourself.'}),
        required=False,
        label="About Me"
    )
    password1 = forms.CharField(
        label='Password', widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label='Confirm password', widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'gender', 'role', 'resume', 'interested_categories', 'skills', 'profile_image', 'about_me')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        resume = cleaned_data.get("resume")

        # Ensure resume is uploaded for employees
        if role == "employee" and not resume:
            raise forms.ValidationError("Resume is required for employees.")
        return cleaned_data

    def save(self, commit=True):
        # Save the provided password in hashed format
        skills = self.cleaned_data.get('skills')
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.about_me = self.cleaned_data.get('about_me')  # Save the "About Me" field
        if commit:
            user.save()
        if skills:
            user.skills = skills  # Save skills as a string
            user.save()
        return user


class UpdateUserForm(forms.ModelForm):
    """
    Update User Form. Doesn't allow changing password in the Admin.
    """
    interested_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    skills = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter skills separated by commas.'}),
        required=False,
        label="Skills"
    )
    profile_image = forms.ImageField(required=False, label="Profile Image")
    about_me = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Write something about yourself.'}),
        required=False,
        label="About Me"
    )
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            'email', 'password', 'first_name', 'last_name', 'gender', 'role', 'resume',
            'interested_categories', 'skills', 'profile_image', 'about_me', 'image_verified', 'is_active', 'is_staff'
        )

    def clean_password(self):
        # Password can't be changed in the admin
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    form = UpdateUserForm
    add_form = AddUserForm

    list_display = ('email', 'first_name', 'last_name', 'gender', 'role', 'is_staff')
    list_filter = ('is_staff', 'image_verified')  # Add image_verified to the list filter
    fieldsets = (
        (None, {'fields': ('email', 'password')}), 
        ('Personal info', {'fields': ('first_name', 'last_name', 'gender', 'role', 'resume', 'interested_categories', 'skills', 'profile_image', 'about_me', 'image_verified')}), 
        ('Permissions', {'fields': ('is_active', 'is_staff')}), 
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email', 'first_name', 'last_name', 'gender', 'role', 'resume',
                    'interested_categories', 'skills', 'profile_image', 'about_me', 'password1', 'password2'
                )
            }
        ),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email', 'first_name', 'last_name')

    def save_model(self, request, obj, form, change):
        # If the image is not verified, set the default image
        if not obj.image_verified:
            obj.profile_image = 'default-image.jpg'  # Set your default image path here
        super().save_model(request, obj, form, change)

admin.site.register(User, UserAdmin)

admin.site.register(accountType)
