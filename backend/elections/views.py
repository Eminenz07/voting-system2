"""
Election views — Student & Admin API endpoints.
Covers all routes defined in the PRD.
"""
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from accounts.models import User
from accounts.serializers import UserSerializer
from .models import (
    Election, Position, Candidate, Vote,
    Nomination, Announcement, AuditLog,
)
from .serializers import (
    ElectionListSerializer, BallotSerializer, VoteBallotSerializer,
    ElectionCreateSerializer, PositionCreateSerializer,
    CandidateCreateSerializer, AnnouncementSerializer,
    NominationSerializer, AuditLogSerializer,
)


def get_client_ip(request):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    return x.split(',')[0].strip() if x else request.META.get('REMOTE_ADDR')


def is_admin(user):
    return user.role in ('uni_admin', 'faculty_admin')


def log_action(user, action, details='', request=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        details=details,
        ip_address=get_client_ip(request) if request else None,
    )


# ══════════════════════════════════════════════════════════════════════════════
# STUDENT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_elections(request):
    """GET /api/elections/ — list elections visible to student."""
    user = request.user
    elections = Election.objects.exclude(status='draft')

    # Scope filtering for students
    if user.role == 'student':
        elections = elections.filter(
            Q(election_type='university') |
            Q(election_type='faculty', faculty_scope=user.faculty) |
            Q(election_type='departmental', faculty_scope=user.faculty,
              department_scope=user.department)
        )

    serializer = ElectionListSerializer(elections, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_ballot(request, election_id):
    """GET /api/elections/<id>/ballot/ — get ballot for voting."""
    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'detail': 'Election not found.'}, status=404)

    if election.status != 'active':
        return Response({'detail': 'This election is not currently active.'}, status=400)

    has_voted = Vote.objects.filter(election=election, voter=request.user).exists()
    positions = election.positions.prefetch_related('candidates').all()

    # Only show approved candidates
    for pos in positions:
        pos._prefetched_objects_cache['candidates'] = [
            c for c in pos.candidates.all() if c.status == 'approved'
        ]

    return Response({
        'election': ElectionListSerializer(election, context={'request': request}).data,
        'positions': [{
            'id': p.id,
            'title': p.title,
            'order': p.order,
            'candidates': [{
                'id': c.id,
                'name': c.name,
                'party': c.party,
                'bio': c.bio,
                'photo_url': c.photo_url,
            } for c in p.candidates.filter(status='approved')],
        } for p in positions],
        'has_voted': has_voted,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_vote(request, election_id):
    """POST /api/elections/<id>/vote/ — cast votes."""
    user = request.user

    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'detail': 'Election not found.'}, status=404)

    if election.status != 'active':
        return Response({'detail': 'This election is not currently active.'}, status=400)

    if not user.is_verified:
        return Response({'detail': 'Your account must be verified to vote.'}, status=403)

    # Check if already voted in this election
    if Vote.objects.filter(election=election, voter=user).exists():
        return Response({'detail': 'You have already voted in this election.'}, status=400)

    serializer = VoteBallotSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    votes_data = serializer.validated_data['votes']

    receipt_hash = None
    with transaction.atomic():
        for vote_item in votes_data:
            try:
                position = Position.objects.get(id=vote_item['position'], election=election)
                candidate = Candidate.objects.get(
                    id=vote_item['candidate'], position=position, status='approved'
                )
            except (Position.DoesNotExist, Candidate.DoesNotExist):
                return Response(
                    {'detail': f'Invalid position or candidate ID.'},
                    status=400
                )

            vote = Vote(
                election=election,
                position=position,
                candidate=candidate,
                voter=user,
            )
            vote.save()
            receipt_hash = vote.receipt_hash  # Last one becomes the master receipt

    log_action(user, 'vote_cast', f'Election: {election.title}', request)

    return Response({
        'detail': 'Vote cast successfully.',
        'receipt': f'VR-{receipt_hash}',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_results(request, election_id):
    """GET /api/elections/<id>/results/ — published results only."""
    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'detail': 'Election not found.'}, status=404)

    if not election.results_published:
        return Response({'detail': 'Results have not been published yet.'}, status=403)

    return Response(_build_results(election, request))


@api_view(['GET'])
@permission_classes([AllowAny])
def public_announcements(request):
    """GET /api/announcements/ — all announcements."""
    anns = Announcement.objects.select_related('election').all()[:50]
    return Response(AnnouncementSerializer(anns, many=True).data)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

def admin_required(view_func):
    """Decorator to enforce admin role."""
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({'detail': 'Admin access required.'}, status=403)
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    wrapper.__doc__ = view_func.__doc__
    return wrapper


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_dashboard(request):
    """GET /api/admin/dashboard/ — KPIs and overview for admin dashboard."""
    user = request.user
    total_students = User.objects.filter(role='student').count()
    verified_students = User.objects.filter(role='student', is_verified=True).count()

    elections_qs = Election.objects.all()
    if user.role == 'faculty_admin':
        elections_qs = elections_qs.filter(faculty_scope=user.faculty)

    active_elections = elections_qs.filter(status='active').count()
    draft_elections = elections_qs.filter(status='draft').count()
    total_votes = Vote.objects.filter(election__in=elections_qs).count()
    pending_nominations = Nomination.objects.filter(
        status='pending',
        election__in=elections_qs
    ).count()

    recent = elections_qs[:8]

    return Response({
        'total_students': total_students,
        'verified_students': verified_students,
        'active_elections': active_elections,
        'draft_elections': draft_elections,
        'total_votes': total_votes,
        'pending_nominations': pending_nominations,
        'recent_elections': ElectionListSerializer(
            recent, many=True, context={'request': request}
        ).data,
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_elections(request):
    """
    GET  /api/admin/elections/   — list all elections
    POST /api/admin/elections/   — create new election
    """
    if request.method == 'GET':
        qs = Election.objects.all()
        if request.user.role == 'faculty_admin':
            qs = qs.filter(faculty_scope=request.user.faculty)
        return Response(ElectionListSerializer(qs, many=True, context={'request': request}).data)

    # POST: create
    serializer = ElectionCreateSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    election = serializer.save()
    log_action(request.user, 'election_created', f'{election.title}', request)
    return Response(ElectionCreateSerializer(election).data, status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_election_detail(request, election_id):
    """
    GET    /api/admin/elections/<id>/
    PATCH  /api/admin/elections/<id>/   — update status, details
    DELETE /api/admin/elections/<id>/
    """
    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    if request.method == 'GET':
        return Response(ElectionListSerializer(election, context={'request': request}).data)

    if request.method == 'DELETE':
        title = election.title
        election.delete()
        log_action(request.user, 'election_deleted', title, request)
        return Response(status=204)

    # PATCH
    serializer = ElectionCreateSerializer(election, data=request.data, partial=True,
                                          context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    log_action(request.user, 'election_updated', f'{election.title}', request)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_publish(request, election_id):
    """POST /api/admin/elections/<id>/publish/"""
    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    election.results_published = True
    election.save()
    log_action(request.user, 'results_published', election.title, request)
    return Response({'detail': 'Results published.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_unpublish(request, election_id):
    """POST /api/admin/elections/<id>/unpublish/"""
    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    election.results_published = False
    election.save()
    log_action(request.user, 'results_unpublished', election.title, request)
    return Response({'detail': 'Results unpublished.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_results(request, election_id):
    """GET /api/admin/elections/<id>/results/ — admin can always see live tallies."""
    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    return Response(_build_results(election, request))


# ── Positions & Candidates (nested CRUD for election creation wizard) ─────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_positions(request, election_id):
    """
    GET  /api/admin/elections/<id>/positions/
    POST /api/admin/elections/<id>/positions/
    """
    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    if request.method == 'GET':
        from .serializers import PositionSerializer
        positions = election.positions.prefetch_related('candidates').all()
        return Response(PositionSerializer(positions, many=True).data)

    serializer = PositionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    position = serializer.save(election=election)
    return Response(PositionCreateSerializer(position).data, status=201)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_candidates(request, election_id, position_id):
    """
    GET  /api/admin/elections/<id>/positions/<pid>/candidates/
    POST /api/admin/elections/<id>/positions/<pid>/candidates/
    """
    try:
        position = Position.objects.get(id=position_id, election_id=election_id)
    except Position.DoesNotExist:
        return Response({'detail': 'Position not found.'}, status=404)

    if request.method == 'GET':
        candidates = position.candidates.all()
        return Response(CandidateCreateSerializer(candidates, many=True).data)

    serializer = CandidateCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    candidate = serializer.save(position=position)
    return Response(CandidateCreateSerializer(candidate).data, status=201)


# ── Voters ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_voters(request):
    """GET /api/admin/voters/ — list all students."""
    students = User.objects.filter(role='student')
    return Response(UserSerializer(students, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_verify_voter(request, voter_id):
    """POST /api/admin/voters/<id>/verify/"""
    try:
        student = User.objects.get(id=voter_id, role='student')
    except User.DoesNotExist:
        return Response({'detail': 'Student not found.'}, status=404)

    student.is_verified = True
    student.save()
    log_action(request.user, 'voter_verified', f'{student.matric}', request)
    return Response({'detail': f'{student.matric} verified.'})


# ── Announcements Admin ──────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_create_announcement(request):
    """POST /api/admin/announcements/"""
    serializer = AnnouncementSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    ann = serializer.save()
    log_action(request.user, 'announcement_created', ann.title, request)
    return Response(AnnouncementSerializer(ann).data, status=201)


# ── Audit Log ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def admin_audit_log(request):
    """GET /api/admin/audit-log/"""
    logs = AuditLog.objects.select_related('user').all()[:200]
    return Response(AuditLogSerializer(logs, many=True).data)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _build_results(election, request):
    """Build the full results payload for an election."""
    positions = election.positions.prefetch_related('candidates').all()
    total_votes = Vote.objects.filter(election=election).values('voter').distinct().count()

    # Eligible voters count
    if election.election_type == 'university':
        eligible = User.objects.filter(role='student', is_verified=True).count()
    elif election.election_type == 'faculty':
        eligible = User.objects.filter(
            role='student', is_verified=True, faculty=election.faculty_scope
        ).count()
    else:
        eligible = User.objects.filter(
            role='student', is_verified=True,
            faculty=election.faculty_scope, department=election.department_scope
        ).count()

    eligible = max(eligible, 1)  # Avoid division by zero
    turnout = round(total_votes / eligible * 100, 1)

    positions_data = []
    for pos in positions:
        candidates = pos.candidates.filter(status='approved')
        pos_votes = Vote.objects.filter(position=pos)
        pos_total = pos_votes.count()

        cand_data = []
        for c in candidates:
            c_votes = pos_votes.filter(candidate=c).count()
            pct = round(c_votes / pos_total * 100, 1) if pos_total > 0 else 0
            cand_data.append({
                'id': c.id,
                'name': c.name,
                'party': c.party,
                'votes': c_votes,
                'percentage': pct,
            })

        # Sort by votes descending
        cand_data.sort(key=lambda x: x['votes'], reverse=True)

        positions_data.append({
            'id': pos.id,
            'title': pos.title,
            'total_votes': pos_total,
            'candidates': cand_data,
        })

    return {
        'election': ElectionListSerializer(election, context={'request': request}).data,
        'total_votes': total_votes,
        'eligible_voters': eligible,
        'turnout': turnout,
        'results_published': election.results_published,
        'positions': positions_data,
    }
