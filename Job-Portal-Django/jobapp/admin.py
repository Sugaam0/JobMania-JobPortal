from django.contrib import admin
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from django.db.models import F
from .models import Category, Applicant, Job, BookmarkJob, User, Blog

# Register the Category model
admin.site.register(Category)

class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('job', 'user', 'timestamp')

admin.site.register(Applicant, ApplicantAdmin)

class BookmarkJobAdmin(admin.ModelAdmin):
    list_display = ('job', 'user', 'timestamp')

admin.site.register(BookmarkJob, BookmarkJobAdmin)

# Job Admin with auto email on publish
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'is_closed', 'timestamp')

    # Override save_model to send email when is_published is set to True
    def save_model(self, request, obj, form, change):
        # Check if the 'is_published' field was changed to True
        if obj.is_published and not change:  # Only send email when it's newly marked as published
            self.send_email_to_employees(obj)
        elif obj.is_published and change and form.has_changed() and 'is_published' in form.changed_data:
            # Send email if 'is_published' was changed to True
            self.send_email_to_employees(obj)

        # Save the object after checking
        super().save_model(request, obj, form, change)

    def send_email_to_employees(self, job):
        selected_category = job.category
        employees = User.objects.filter(role='employee', interested_categories=selected_category)
        
        for employee in employees:
            subject = f"New Published Job in Your Interested Category: {selected_category.name}"
            message = f"Dear {employee.get_full_name()},\n\n" \
                      f"A new job has been published in the {selected_category.name} category that matches your interests!\n\n" \
                      f"Job Title: {job.title}\n" \
                      f"Company: {job.company_name}\n" \
                      f"Location: {job.location}\n\n" \
                      f"Please visit the portal to apply."

            send_mail(
                subject=subject,
                message=message,
                from_email=job.user.email,
                recipient_list=[employee.email],
                fail_silently=False,
            )

# Register the Job model with the custom admin
admin.site.register(Job, JobAdmin)

class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    
    search_fields = ('title', 'content')
    
admin.site.register(Blog, BlogAdmin)