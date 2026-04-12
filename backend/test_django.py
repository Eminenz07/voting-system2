import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from elections.models import Election, Position, Candidate
e = Election.objects.create(title="Test", start_date="2026-01-01", end_date="2026-12-31")
p = Position.objects.create(election=e, title="Pos")
c = Candidate.objects.create(position=p, name="A")

positions = e.positions.prefetch_related('candidates').all()
for pos in positions:
    # Mimic views.py verbatim
    pos._prefetched_objects_cache['candidates'] = [
        cc for cc in pos.candidates.all() if cc.status == 'approved'
    ]

try:
    for p in positions:
        list(p.candidates.filter(status='approved'))
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
