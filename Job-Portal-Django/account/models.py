from django.contrib.auth.models import AbstractUser
from django.db import models

from account.managers import CustomUserManager


JOB_TYPE = (
    ('M', "Male"),
    ('F', "Female"),

)

ROLE = (
    ('employer', "Employer"),
    ('employee', "Employee"),
)



class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, blank=False,
                              error_messages={
                                  'unique': "A user with that email already exists.",
                              })
    role = models.CharField(choices=ROLE,  max_length=10)
    gender = models.CharField(choices=JOB_TYPE, max_length=1)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    interested_categories = models.ManyToManyField(
        'jobapp.Category',  # Use lazy reference
        blank=True,
        related_name='users'
    )
    skills = models.TextField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.first_name+ ' ' + self.last_name
    
    def get_skills_list(self):
        # Convert the comma-separated string of skills into a list
        if self.skills:
            return self.skills.split(',')  # Split the skills string by commas
        return []
    
    def save(self, *args, **kwargs):
        if self.resume:
            # Check the file extension
            if not self.resume.name.endswith('.jpg'):
                raise ValueError("Only .jpg files are allowed for resume uploads.")
        super().save(*args, **kwargs)
        
    objects = CustomUserManager()
    
    
