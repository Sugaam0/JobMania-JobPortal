from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect , get_object_or_404
from django.urls import reverse, reverse_lazy
from account.forms import *
from jobapp.permission import user_is_employee 
from jobapp.models import Category
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
import random
import string
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

def get_success_url(request):
    """
    Handle Success Url After LogIN

    """
    if 'next' in request.GET and request.GET['next'] != '':
        return request.GET['next']
    else:
        return reverse('jobapp:home')



def employee_registration(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST, request.FILES)
        print("Form data:", request.POST)  # Debugging log for form data
        if form.is_valid():
            print("Form is valid")  # Debugging log for valid form
            user = form.save()
            user.image_verified = False
            # Debugging selected categories
            selected_categories = form.cleaned_data.get('interested_categories')
            print("Selected Categories:", selected_categories)

            messages.success(request, "Your account has been successfully created. Please log in.")
            return redirect('account:login')
        else:
            print("Form errors:", form.errors)  # Debugging log for errors
            messages.error(request, "There were errors in your submission. Please correct them.")
    else:
        form = EmployeeRegistrationForm()

    context = {'form': form}
    return render(request, 'account/employee-registration.html', context)

def employer_registration(request):

    """
    Handle Employee Registration 

    """

    form = EmployerRegistrationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Your account has been successfully created. Please log in.")
        return redirect('account:login')
    context={
        
            'form':form
        }

    return render(request,'account/employer-registration.html',context)


@login_required(login_url=reverse_lazy('accounts:login'))
@user_is_employee
def employee_edit_profile(request, id=id):

    """
    Handle Employee Profile Update Functionality

    """
    user = get_object_or_404(User, id=id)
    form = EmployeeProfileEditForm(request.POST or None, request.FILES or None, instance=user)
    if request.method == 'POST':
        form = EmployeeProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()  # This will update both skills and categories
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('account:edit-profile', id=user.id)  # Redirect to the same page
    else:
        form = EmployeeProfileEditForm(instance=user)

    return render(request,'account/employee-edit-profile.html', {'form': form})



def user_logIn(request):

    """
    Provides users to logIn

    """

    form = UserLoginForm(request.POST or None)
    

    if request.user.is_authenticated:
        return redirect('/')
    
    else:
        if request.method == 'POST':
            if form.is_valid():
                auth.login(request, form.get_user())
                return HttpResponseRedirect(get_success_url(request))
    context = {
        'form': form,
    }

    return render(request ,'account/login.html',context)


def user_logOut(request):
    """
    Provide the ability to logout
    """
    auth.logout(request)
    messages.success(request, 'You have Successfully logged out!')
    return redirect('account:login')


def generate_random_password(length=8):
    """Generates a random password of specified length."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            # Check if the user exists
            user = User.objects.get(email=email)

            # Generate new random password
            new_password = generate_random_password()

            # Update the user's password
            user.set_password(new_password)
            user.save()

            # Send the new password to the user's email
            send_mail(
                'Password Reset - JobMania',
                f'Hello {user.first_name},\n\nYour new password is: {new_password}\n\nPlease log in and change your password immediately.',
                'noreply@jobmania.com',  # Change to your "from" email
                [email],
                fail_silently=False,
            )

            messages.success(request, 'A new password has been sent to your email.')
            return redirect('account:login')

        except User.DoesNotExist:
            messages.error(request, 'No user found with this email.')

    return render(request, 'account/forgot_password.html')


class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput, label="Old Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password != confirm_password:
            raise forms.ValidationError("New password and confirm password do not match.")
        return cleaned_data

# View for handling password change
@login_required(login_url=reverse_lazy('accounts:login'))
def change_password(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            
            # Check if the old password is correct
            if not request.user.check_password(old_password):
                form.add_error('old_password', 'The old password is incorrect.')
            else:
                # Update the password
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep the user logged in
                messages.success(request, 'Your password has been updated successfully.')
                return redirect('account:edit-profile', request.user.id)
    else:
        form = CustomPasswordChangeForm()

    return render(request, 'account/change_password.html', {'form': form})