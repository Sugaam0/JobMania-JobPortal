from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.core.serializers import serialize
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from account.models import User
from jobapp.forms import *
from jobapp.models import *
from jobapp.permission import *
User = get_user_model()
from django.template.loader import render_to_string
from PIL import Image, ImageDraw, ImageFont
import io
from django.http import HttpResponse
import base64
from django.core.mail import send_mail
from django.template.loader import render_to_string
from account.models import User


def home_view(request):

    published_jobs = Job.objects.filter(is_published=True).order_by('-timestamp')
    categories = Category.objects.all()
    jobs = published_jobs.filter(is_closed=False)
    total_candidates = User.objects.filter(role='employee').count()
    total_companies = User.objects.filter(role='employer').count()
    paginator = Paginator(jobs, 3)
    page_number = request.GET.get('page',None)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        job_lists=[]
        job_objects_list = page_obj.object_list.values()
        for job_list in job_objects_list:
            job_lists.append(job_list)
        

        next_page_number = None
        if page_obj.has_next():
            next_page_number = page_obj.next_page_number()

        prev_page_number = None       
        if page_obj.has_previous():
            prev_page_number = page_obj.previous_page_number()

        data={
            'job_lists':job_lists,
            'current_page_no':page_obj.number,
            'next_page_number':next_page_number,
            'no_of_page':paginator.num_pages,
            'prev_page_number':prev_page_number
        }    
        return JsonResponse(data)
    
    context = {

    'total_candidates': total_candidates,
    'total_companies': total_companies,
    'total_jobs': len(jobs),
    'total_completed_jobs':len(published_jobs.filter(is_closed=True)),
    'page_obj': page_obj,
    'categories': categories,
    }
    print('ok')
    return render(request, 'jobapp/index.html', context)



def job_list_View(request):
    # Fetch all categories for the filter
    categories = Category.objects.all()

    # Start with filtering jobs that are published and not closed
    job_list = Job.objects.filter(is_published=True, is_closed=False).order_by('-timestamp')

    # Get selected categories from the request GET parameters
    selected_categories = request.GET.getlist('categories')  # list of selected category IDs
    if selected_categories:
        # Filter the job list based on selected categories
        job_list = job_list.filter(category__id__in=selected_categories)

    # Paginate the filtered job list
    paginator = Paginator(job_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass the filtered job list and categories to the context
    context = {
        'page_obj': page_obj,
        'categories': categories,  # To render category filters in the template
        'selected_categories': selected_categories,  # Pass the selected categories
    }

    return render(request, 'jobapp/job-list.html', context)



@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def create_job_View(request):
    """
    Provide the ability to create job post
    """
    form = JobForm(request.POST or None)

    user = get_object_or_404(User, id=request.user.id)
    categories = Category.objects.all()

    if request.method == 'POST':

        if form.is_valid():

            instance = form.save(commit=False)
            instance.user = user
            instance.save()
            # for save tags
            form.save_m2m()
                   
            messages.success(
                    request, 'You have successfully posted your job! Please wait for review.')
            return redirect(reverse("jobapp:single-job", kwargs={
                                    'id': instance.id
                                    }))

    context = {
        'form': form,
        'categories': categories
    }
    return render(request, 'jobapp/post-job.html', context)


def single_job_view(request, id):
    """
    Provide the ability to view job details
    """
    if cache.get(id):
        job = cache.get(id)
    else:
        job = get_object_or_404(Job, id=id)
        cache.set(id,job , 60 * 15)
    related_job_list = job.tags.similar_objects()

    paginator = Paginator(related_job_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'job': job,
        'page_obj': page_obj,
        'total': len(related_job_list)

    }
    return render(request, 'jobapp/job-single.html', context)


def search_result_view(request):
    """
        User can search job with multiple fields
        User can search job with multiple fields

    User can search job with multiple fields

    """
    categories = Category.objects.all()
    
    job_list = Job.objects.order_by('-timestamp')

    # Keywords
    if 'job_title_or_company_name' in request.GET:
        job_title_or_company_name = request.GET['job_title_or_company_name']
        if job_title_or_company_name:
            job_list = job_list.filter(title__icontains=job_title_or_company_name) | job_list.filter(
                company_name__icontains=job_title_or_company_name)

    # Location
    if 'location' in request.GET:
        location = request.GET['location']
        if location:
            job_list = job_list.filter(location__icontains=location)

    # Job Type
    if 'job_type' in request.GET:
        job_type = request.GET['job_type']
        if job_type:
            job_list = job_list.filter(job_type__iexact=job_type)

    # Category
    if 'category' in request.GET and request.GET['category']:
        category = request.GET['category']
        print(f"Category ID from GET: {category}")
        job_list = job_list.filter(category__id=category)

    paginator = Paginator(job_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': categories,  # Ensure categories are passed to the template
    }

    return render(request, 'jobapp/result.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def apply_job_view(request, id):

    form = JobApplyForm(request.POST or None)
    user = get_object_or_404(User, id=request.user.id)
    applicant = Applicant.objects.filter(user=user, job=id)

    if not applicant:
        if request.method == 'POST':

            if form.is_valid():
                instance = form.save(commit=False)
                instance.user = user
                instance.save()
                
                job = get_object_or_404(Job, id=id)
                employer_email = job.user.email
                
                subject = f"New Job Application: {user.get_full_name()} applied for {job.title}"
                message = f"Dear {job.user.get_full_name()},\n\n" \
                          f"{user.get_full_name()} has applied for your job posting: {job.title}.\n\n" \
                          f"Please log in to the portal to view the application details."
                
                # Send the email
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=user.email,  # The email of the employee applying for the job
                    recipient_list=[employer_email],
                    fail_silently=False,
                )

                messages.success(
                    request, 'You have successfully applied for this job!')
                return redirect(reverse("jobapp:single-job", kwargs={
                    'id': id
                }))

        else:
            return redirect(reverse("jobapp:single-job", kwargs={
                'id': id
            }))

    else:

        messages.error(request, 'You already applied for the Job!')

        return redirect(reverse("jobapp:single-job", kwargs={
            'id': id
        }))


@login_required(login_url=reverse_lazy('account:login'))
def dashboard_view(request):
    """
    """
    jobs = []
    savedjobs = []
    appliedjobs = []
    total_applicants = {}
    if request.user.role == 'employer':

        jobs = Job.objects.filter(user=request.user.id)
        for job in jobs:
            count = Applicant.objects.filter(job=job.id).count()
            total_applicants[job.id] = count

    if request.user.role == 'employee':
        savedjobs = BookmarkJob.objects.filter(user=request.user.id)
        appliedjobs = Applicant.objects.filter(user=request.user.id)
    context = {

        'jobs': jobs,
        'savedjobs': savedjobs,
        'appliedjobs':appliedjobs,
        'total_applicants': total_applicants
    }

    return render(request, 'jobapp/dashboard.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def delete_job_view(request, id):

    job = get_object_or_404(Job, id=id, user=request.user.id)

    if job:

        job.delete()
        messages.success(request, 'Your Job Post was successfully deleted!')

    return redirect('jobapp:dashboard')


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def make_complete_job_view(request, id):
    job = get_object_or_404(Job, id=id, user=request.user.id)

    if job:
        try:
            job.is_closed = True
            job.save()
            messages.success(request, 'Your Job was marked closed!')
        except:
            messages.success(request, 'Something went wrong !')
            
    return redirect('jobapp:dashboard')



@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def all_applicants_view(request, id):

    all_applicants = Applicant.objects.filter(job=id)

    context = {

        'all_applicants': all_applicants
    }

    return render(request, 'jobapp/all-applicants.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def delete_bookmark_view(request, id):

    job = get_object_or_404(BookmarkJob, id=id, user=request.user.id)

    if job:

        job.delete()
        messages.success(request, 'Saved Job was successfully deleted!')

    return redirect('jobapp:dashboard')


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def applicant_details_view(request, id):
    user = get_object_or_404(User, id=id)
    applicant = get_object_or_404(User, id=id)

    context = {
        'user': user,
        'applicant': applicant
    }

    return render(request, 'jobapp/applicant-details.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def job_bookmark_view(request, id):

    form = JobBookmarkForm(request.POST or None)

    user = get_object_or_404(User, id=request.user.id)
    applicant = BookmarkJob.objects.filter(user=request.user.id, job=id)

    if not applicant:
        if request.method == 'POST':

            if form.is_valid():
                instance = form.save(commit=False)
                instance.user = user
                instance.save()

                messages.success(
                    request, 'You have successfully saved this job!')
                return redirect(reverse("jobapp:single-job", kwargs={
                    'id': id
                }))

        else:
            return redirect(reverse("jobapp:single-job", kwargs={
                'id': id
            }))

    else:
        messages.error(request, 'You already saved this Job!')

        return redirect(reverse("jobapp:single-job", kwargs={
            'id': id
        }))


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def job_edit_view(request, id=id):
    """
    Handle Job Update

    """

    job = get_object_or_404(Job, id=id, user=request.user.id)
    categories = Category.objects.all()
    form = JobEditForm(request.POST or None, instance=job)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        # for save tags
        # form.save_m2m()
        messages.success(request, 'Your Job Post Was Successfully Updated!')
        return redirect(reverse("jobapp:single-job", kwargs={
            'id': instance.id
        }))
    context = {

        'form': form,
        'categories': categories
    }

    return render(request, 'jobapp/job-edit.html', context)



def resume(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        about = request.POST.get('about', '')
        age = request.POST.get('age', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        skill1 = request.POST.get('skill1', '')
        skill2 = request.POST.get('skill2', '')
        skill3 = request.POST.get('skill3', '')
        skill4 =request.POST.get('skill4', '')
        skill5 =request.POST.get('skill5', '')
        degree1 = request.POST.get('degree1', '')
        college1 = request.POST.get('college1', '')
        year1 = request.POST.get('year1', '')
        degree2 = request.POST.get('degree2', '')
        college2 = request.POST.get('college2', '')
        year2 = request.POST.get('year2', '') 
        college3 = request.POST.get('college3', '')
        year3 = request.POST.get('year3', '')
        degree3 = request.POST.get('degree3', '') 
        lang1 = request.POST.get('lang1', '')
        lang2 = request.POST.get('lang2', '')
        lang3 = request.POST.get('lang3', '')     
        project1= request.POST.get('project1', '')
        durat1 = request.POST.get('duration1', '')
        desc1 = request.POST.get('desc1', '')
        project2 = request.POST.get('project2', '')
        durat2 = request.POST.get('duration2', '')
        desc2 = request.POST.get('desc2', '')
        company1 = request.POST.get('company1', '')
        post1 = request.POST.get('post1', '')
        duration1 = request.POST.get('duration1', '')
        lin11 = request.POST.get('lin11', '')
        company2 = request.POST.get('company2', '')
        post2 = request.POST.get('post2', '')
        duration2 = request.POST.get('duration2', '')
        lin21 = request.POST.get('lin21', '') 
        ach1 = request.POST.get('ach1', '')
        ach2 = request.POST.get('ach2', '')
        ach3 = request.POST.get('ach3', '') 
        return render(request, 'jobapp/resume_template.html', {'name':name, 
                                               'about':about, 'skill5':skill5,  
                                               'age':age, 'email':email, 
                                               'phone':phone, 'skill1':skill1,
                                               'skill2':skill2,  'skill3':skill3, 
                                               'skill4':skill4,  'degree1':degree1, 
                                               'college1':college1, 'year1':year1, 
                                               'college3':college3, 'year3':year3, 
                                               'degree3':degree3, 'lang1':lang1, 
                                               'lang2':lang2,  'lang3':lang3,
                                               'degree2':degree2,  'college2':college2, 
                                               'year2':year2, 'project1':project1,
                                               'durat1':durat1, 'desc1':desc1, 
                                               'project2':project2,  'durat2':durat2,
                                               'desc2':desc2, 'company1':company1, 
                                               'post1':post1, 'duration1': duration1, 
                                               'company2':company2, 'post2':post2, 
                                               'duration2': duration2,'lin11':lin11,
                                                'lin21':lin21, 'ach1':ach1,
                                                'ach2':ach2,'ach3':ach3 })
    
    return render(request, 'jobapp/create_resume.html')

def employee_list(request):
    # Fetch all users with the role of 'employee'
    category_id = request.GET.getlist('categories')
    employees = User.objects.filter(role='employee')

    # If you want filtering based on categories, you can add it here
    category_filter = request.GET.get('category')
    if category_filter:
        employees = employees.filter(interested_categories__name=category_filter)

    # You can also add other filters, such as by location, skills, etc.
    categories = Category.objects.all()
    context = {
        'employees': employees,
        'categories': categories,
        'selected_categories': category_id,
    }
    
    return render(request, 'jobapp/employee_list.html', context)

def blog_list_view(request):
    blogs = Blog.objects.all()
    return render(request, 'jobapp/blog_list.html', {'blogs': blogs})

@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def create_blog_view(request):
    if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user  # Assign logged-in user as the author
            blog.save()
            return redirect('jobapp:blog-list')  # Redirect to the blog list page
    else:
        form = BlogForm()
    return render(request, 'jobapp/blog_create.html', {'form': form})

def blog_single_view(request, blog_id):
    # Retrieve the blog object based on its ID
    blog = get_object_or_404(Blog, id=blog_id)
    
    # Render the blog details in the blog_single.html template
    return render(request, 'jobapp/blog_single.html', {'blog': blog})


