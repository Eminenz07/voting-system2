"""Election URL routes — student and admin."""
from django.urls import path
from . import views

urlpatterns = [
    # ── Student routes ────────────────────────────────────────────────────────
    path('elections/', views.student_elections, name='elections'),
    path('elections/<int:election_id>/ballot/', views.student_ballot, name='ballot'),
    path('elections/<int:election_id>/vote/', views.student_vote, name='vote'),
    path('elections/<int:election_id>/results/', views.student_results, name='results'),
    path('announcements/', views.public_announcements, name='announcements'),

    # ── Admin routes ──────────────────────────────────────────────────────────
    path('admin/dashboard/', views.admin_dashboard, name='admin-dashboard'),

    path('admin/elections/', views.admin_elections, name='admin-elections'),
    path('admin/elections/<int:election_id>/', views.admin_election_detail, name='admin-election-detail'),
    path('admin/elections/<int:election_id>/publish/', views.admin_publish, name='admin-publish'),
    path('admin/elections/<int:election_id>/unpublish/', views.admin_unpublish, name='admin-unpublish'),
    path('admin/elections/<int:election_id>/results/', views.admin_results, name='admin-results'),

    # Nested: positions + candidates
    path('admin/elections/<int:election_id>/positions/', views.admin_positions, name='admin-positions'),
    path('admin/elections/<int:election_id>/positions/<int:position_id>/candidates/',
         views.admin_candidates, name='admin-candidates'),

    # Voters
    path('admin/voters/', views.admin_voters, name='admin-voters'),
    path('admin/voters/<int:voter_id>/verify/', views.admin_verify_voter, name='admin-verify-voter'),

    # Announcements
    path('admin/announcements/', views.admin_create_announcement, name='admin-announcements'),

    # Audit log
    path('admin/audit-log/', views.admin_audit_log, name='admin-audit-log'),
]
