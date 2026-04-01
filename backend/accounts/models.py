"""
Custom User model for AU E-Voting System.
Uses matric number as the unique login identifier.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager for matric-based authentication."""

    def create_user(self, matric, password=None, **extra_fields):
        if not matric:
            raise ValueError('Matric number is required')
        user = self.model(matric=matric.strip().upper(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, matric, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'uni_admin')
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('first_name', 'Admin')
        extra_fields.setdefault('last_name', 'User')
        return self.create_user(matric, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with matric number as the primary identifier.
    Roles: student, faculty_admin, uni_admin
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty_admin', 'Faculty Admin'),
        ('uni_admin', 'University Admin'),
    ]

    matric = models.CharField(max_length=20, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, default='')
    faculty = models.CharField(max_length=100, blank=True, default='')
    department = models.CharField(max_length=100, blank=True, default='')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_verified = models.BooleanField(default=False)

    # Django admin requirements
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'matric'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.matric} — {self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_admin(self):
        return self.role in ('uni_admin', 'faculty_admin')
