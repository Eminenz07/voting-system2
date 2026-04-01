from django.contrib import admin
from .models import Election, Position, Candidate, Vote, Nomination, Announcement, AuditLog


class PositionInline(admin.TabularInline):
    model = Position
    extra = 0


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 0


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'election_type', 'status', 'start_date', 'end_date', 'results_published')
    list_filter = ('status', 'election_type', 'results_published')
    search_fields = ('title',)
    inlines = [PositionInline]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'election', 'order')
    list_filter = ('election',)
    inlines = [CandidateInline]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'party', 'status')
    list_filter = ('status', 'position__election')


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'election', 'position', 'candidate', 'cast_at')
    list_filter = ('election',)
    readonly_fields = ('receipt_hash',)


@admin.register(Nomination)
class NominationAdmin(admin.ModelAdmin):
    list_display = ('student', 'position', 'status', 'created_at')
    list_filter = ('status', 'election')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'election', 'created_at')
    list_filter = ('priority',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'created_at')
    list_filter = ('action',)
    readonly_fields = ('user', 'action', 'details', 'ip_address', 'created_at')
