"""Election serializers for both student and admin APIs."""
from rest_framework import serializers
from .models import Election, Position, Candidate, Vote, Nomination, Announcement, AuditLog


# ── Shared / Student ─────────────────────────────────────────────────────────

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['id', 'name', 'party', 'bio', 'photo_url', 'status']
        read_only_fields = ['id']


class PositionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)

    class Meta:
        model = Position
        fields = ['id', 'title', 'order', 'candidates']
        read_only_fields = ['id']


class ElectionListSerializer(serializers.ModelSerializer):
    """Serializer for listing elections — lightweight."""
    total_votes = serializers.IntegerField(read_only=True)
    positions_count = serializers.IntegerField(read_only=True)
    has_voted = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'election_type',
                  'faculty_scope', 'department_scope',
                  'status', 'start_date', 'end_date',
                  'results_published', 'total_votes', 'positions_count',
                  'has_voted', 'created_at']

    def get_has_voted(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Vote.objects.filter(election=obj, voter=request.user).exists()


class BallotSerializer(serializers.Serializer):
    """For GET /elections/<id>/ballot/ — returns election + positions + candidates."""
    election = ElectionListSerializer()
    positions = PositionSerializer(many=True)
    has_voted = serializers.BooleanField()


class CastVoteSerializer(serializers.Serializer):
    """Input for POST /elections/<id>/vote/"""
    position = serializers.IntegerField()
    candidate = serializers.IntegerField()


class VoteBallotSerializer(serializers.Serializer):
    """Wraps the full ballot submission."""
    votes = CastVoteSerializer(many=True)


# ── Results ───────────────────────────────────────────────────────────────────

class CandidateResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    party = serializers.CharField()
    votes = serializers.IntegerField()
    percentage = serializers.FloatField()


class PositionResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    total_votes = serializers.IntegerField()
    candidates = CandidateResultSerializer(many=True)


class ElectionResultSerializer(serializers.Serializer):
    election = ElectionListSerializer()
    total_votes = serializers.IntegerField()
    eligible_voters = serializers.IntegerField()
    turnout = serializers.FloatField()
    results_published = serializers.BooleanField()
    positions = PositionResultSerializer(many=True)


# ── Admin ─────────────────────────────────────────────────────────────────────

class ElectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'election_type',
                  'faculty_scope', 'department_scope',
                  'status', 'start_date', 'end_date']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PositionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'title', 'order']


class CandidateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['id', 'name', 'party', 'bio', 'photo_url', 'status']


class AnnouncementSerializer(serializers.ModelSerializer):
    election_title = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'body', 'priority', 'election',
                  'election_title', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_election_title(self, obj):
        return obj.election.title if obj.election else None

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class NominationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_matric = serializers.CharField(source='student.matric', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)

    class Meta:
        model = Nomination
        fields = ['id', 'election', 'position', 'student', 'student_name',
                  'student_matric', 'position_title', 'party', 'manifesto',
                  'status', 'created_at', 'reviewed_at']
        read_only_fields = ['id', 'student', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    user_matric = serializers.CharField(source='user.matric', read_only=True, default='—')

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_matric', 'action', 'details',
                  'ip_address', 'created_at']
