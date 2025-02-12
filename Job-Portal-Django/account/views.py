from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect , get_object_or_404
from django.urls import reverse, reverse_lazy
from account.forms import *
from jobapp.permission import user_is_employee 
from jobapp.models import Category


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


