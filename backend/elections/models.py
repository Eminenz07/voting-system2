"""
Election-related models.
Election → Position → Candidate
Vote, Nomination, Announcement, AuditLog
"""
from django.db import models
from django.conf import settings
import hashlib, uuid


class Election(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    TYPE_CHOICES = [
        ('university', 'University-wide'),
        ('faculty', 'Faculty'),
        ('departmental', 'Departmental'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    election_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='university')
    faculty_scope = models.CharField(max_length=100, blank=True, default='',
                                     help_text='Required for faculty/departmental elections')
    department_scope = models.CharField(max_length=100, blank=True, default='',
                                        help_text='Required for departmental elections')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    results_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name='created_elections')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def total_votes(self):
        return Vote.objects.filter(election=self).values('voter').distinct().count()

    @property
    def positions_count(self):
        return self.positions.count()


class Position(models.Model):
    """A role being contested in an election (e.g. President, Secretary)."""
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.election.title} — {self.title}'


class Candidate(models.Model):
    """A student nominated for a position."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=200)
    party = models.CharField(max_length=200, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    photo_url = models.URLField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.name} — {self.position.title}'


class Vote(models.Model):
    """
    A single vote: one per voter per position.
    The receipt_hash provides anonymous verification.
    """
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='votes')
    receipt_hash = models.CharField(max_length=64)
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-cast_at']
        constraints = [
            models.UniqueConstraint(
                fields=['voter', 'position'],
                name='unique_vote_per_position'
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.receipt_hash:
            raw = f'{self.voter_id}-{self.election_id}-{self.position_id}-{uuid.uuid4()}'
            self.receipt_hash = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Vote by {self.voter.matric} for {self.candidate.name}'


class Nomination(models.Model):
    """Self-nomination by a student for a position."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='nominations')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='nominations')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='nominations')
    party = models.CharField(max_length=200, blank=True, default='')
    manifesto = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'position'],
                name='unique_nomination_per_position'
            ),
        ]

    def __str__(self):
        return f'Nomination: {self.student.matric} for {self.position.title}'


class Announcement(models.Model):
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=255)
    body = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    election = models.ForeignKey(Election, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='announcements')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AuditLog(models.Model):
    """Immutable audit trail for all sensitive actions."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, related_name='audit_logs')
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.action} — {self.created_at}'
