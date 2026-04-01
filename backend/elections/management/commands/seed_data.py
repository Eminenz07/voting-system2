"""
Management command to seed the database with demo data.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from elections.models import Election, Position, Candidate, Announcement


class Command(BaseCommand):
    help = 'Seed the database with demo data for development'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database…')

        # ── Create admin user ─────────────────────────────────────────────
        admin, created = User.objects.get_or_create(
            matric='ADMIN001',
            defaults={
                'first_name': 'System',
                'last_name': 'Admin',
                'email': 'admin@adelekeuniversity.edu.ng',
                'role': 'uni_admin',
                'is_verified': True,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('✓ Admin user created (ADMIN001 / admin123)'))
        else:
            self.stdout.write('  Admin user already exists.')

        # ── Create faculty admin ──────────────────────────────────────────
        fac_admin, created = User.objects.get_or_create(
            matric='FACADMIN01',
            defaults={
                'first_name': 'Faculty',
                'last_name': 'Admin',
                'email': 'facadmin@adelekeuniversity.edu.ng',
                'faculty': 'Sciences',
                'role': 'faculty_admin',
                'is_verified': True,
                'is_staff': True,
            }
        )
        if created:
            fac_admin.set_password('admin123')
            fac_admin.save()
            self.stdout.write(self.style.SUCCESS('✓ Faculty admin created (FACADMIN01 / admin123)'))

        # ── Create sample students ────────────────────────────────────────
        students_data = [
            {'matric': '24/0850', 'first_name': 'Adebayo', 'last_name': 'Johnson',
             'faculty': 'Sciences', 'department': 'Computer Science', 'is_verified': True},
            {'matric': '24/0912', 'first_name': 'Chidinma', 'last_name': 'Okafor',
             'faculty': 'Sciences', 'department': 'Mathematics', 'is_verified': True},
            {'matric': '23/1045', 'first_name': 'Fatima', 'last_name': 'Bello',
             'faculty': 'Engineering', 'department': 'Civil Engineering', 'is_verified': True},
            {'matric': '23/0788', 'first_name': 'Emmanuel', 'last_name': 'Adeyemi',
             'faculty': 'Arts', 'department': 'English', 'is_verified': True},
            {'matric': '24/1100', 'first_name': 'Grace', 'last_name': 'Nwankwo',
             'faculty': 'Sciences', 'department': 'Computer Science', 'is_verified': False},
        ]

        for sd in students_data:
            student, created = User.objects.get_or_create(
                matric=sd['matric'],
                defaults={**sd, 'email': f'{sd["first_name"].lower()}@student.au.edu.ng'}
            )
            if created:
                student.set_password('student123')
                student.save()

        self.stdout.write(self.style.SUCCESS(f'✓ {len(students_data)} students seeded'))

        # ── Create elections ──────────────────────────────────────────────
        now = timezone.now()

        # Active university-wide election
        e1, _ = Election.objects.get_or_create(
            title='2026 Student Union Government Elections',
            defaults={
                'description': 'General elections for all SUG executive positions for the 2026/2027 academic session.',
                'election_type': 'university',
                'status': 'active',
                'start_date': now - timedelta(days=1),
                'end_date': now + timedelta(days=6),
                'created_by': admin,
            }
        )
        # Positions + Candidates for e1
        positions_data = [
            {
                'title': 'President',
                'candidates': [
                    {'name': 'Oluwaseun Akinlade', 'party': 'Progressive Students Alliance'},
                    {'name': 'Amaka Eze', 'party': 'United Campus Front'},
                    {'name': 'Ibrahim Musa', 'party': 'Independent'},
                ]
            },
            {
                'title': 'Vice President',
                'candidates': [
                    {'name': 'David Okonkwo', 'party': 'Progressive Students Alliance'},
                    {'name': 'Hauwa Abdullahi', 'party': 'United Campus Front'},
                ]
            },
            {
                'title': 'General Secretary',
                'candidates': [
                    {'name': 'Chiamaka Igwe', 'party': 'Progressive Students Alliance'},
                    {'name': 'Tunde Bakare', 'party': 'Campus Reform Movement'},
                    {'name': 'Ruth Obi', 'party': 'United Campus Front'},
                ]
            },
        ]

        for i, pd in enumerate(positions_data):
            pos, _ = Position.objects.get_or_create(
                election=e1, title=pd['title'],
                defaults={'order': i + 1}
            )
            for cd in pd['candidates']:
                Candidate.objects.get_or_create(
                    position=pos, name=cd['name'],
                    defaults={'party': cd['party'], 'status': 'approved'}
                )

        # Completed election (results published)
        e2, _ = Election.objects.get_or_create(
            title='Faculty of Sciences Representative Election',
            defaults={
                'description': 'Election for the Faculty of Sciences student representative.',
                'election_type': 'faculty',
                'faculty_scope': 'Sciences',
                'status': 'completed',
                'results_published': True,
                'start_date': now - timedelta(days=14),
                'end_date': now - timedelta(days=7),
                'created_by': admin,
            }
        )

        pos_rep, _ = Position.objects.get_or_create(
            election=e2, title='Faculty Representative',
            defaults={'order': 1}
        )
        c1, _ = Candidate.objects.get_or_create(
            position=pos_rep, name='Kemi Adeola',
            defaults={'party': 'Science Students Forum', 'status': 'approved'}
        )
        c2, _ = Candidate.objects.get_or_create(
            position=pos_rep, name='Chukwuemeka Nwosu',
            defaults={'party': 'Independent', 'status': 'approved'}
        )

        # Draft election
        e3, _ = Election.objects.get_or_create(
            title='Department of Computer Science Class Rep Election',
            defaults={
                'description': 'Election for 400-level class representative.',
                'election_type': 'departmental',
                'faculty_scope': 'Sciences',
                'department_scope': 'Computer Science',
                'status': 'draft',
                'start_date': now + timedelta(days=7),
                'end_date': now + timedelta(days=14),
                'created_by': admin,
            }
        )

        self.stdout.write(self.style.SUCCESS('✓ 3 elections seeded'))

        # ── Announcements ─────────────────────────────────────────────────
        Announcement.objects.get_or_create(
            title='2026 SUG Elections Are Now Live!',
            defaults={
                'body': 'The Student Union Government elections are now open for voting. All verified students are encouraged to cast their votes before the deadline. Remember, every vote counts!',
                'priority': 'urgent',
                'election': e1,
                'created_by': admin,
            }
        )
        Announcement.objects.get_or_create(
            title='Voter Verification Drive',
            defaults={
                'body': 'All unverified students should visit the Student Affairs office with their ID cards for immediate verification. You must be verified before you can vote.',
                'priority': 'normal',
                'created_by': admin,
            }
        )
        Announcement.objects.get_or_create(
            title='Faculty of Sciences Results Published',
            defaults={
                'body': 'The results for the Faculty of Sciences Representative Election have been published. You can view the results in the Results section.',
                'priority': 'normal',
                'election': e2,
                'created_by': admin,
            }
        )

        self.stdout.write(self.style.SUCCESS('✓ Announcements seeded'))

        # ── Add some votes to completed election ──────────────────────────
        from elections.models import Vote
        verified_students = User.objects.filter(role='student', is_verified=True, faculty='Sciences')
        for student in verified_students[:2]:
            Vote.objects.get_or_create(
                election=e2, position=pos_rep, candidate=c1, voter=student,
            )
        for student in verified_students[2:3]:
            Vote.objects.get_or_create(
                election=e2, position=pos_rep, candidate=c2, voter=student,
            )

        self.stdout.write(self.style.SUCCESS('✓ Sample votes seeded'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═══════════════════════════════════════'))
        self.stdout.write(self.style.SUCCESS('  Database seeded successfully!'))
        self.stdout.write(self.style.SUCCESS('═══════════════════════════════════════'))
        self.stdout.write('')
        self.stdout.write('  Login credentials:')
        self.stdout.write(f'  Admin:   ADMIN001 / admin123')
        self.stdout.write(f'  Faculty: FACADMIN01 / admin123')
        self.stdout.write(f'  Student: 24/0850 / student123')
        self.stdout.write('')
