# Product Requirements Document
## Adeleke University E-Voting System — MVP

**Version:** 1.0  
**Date:** March 2026  
**Author:** Engineering Team  
**Status:** Approved for Development

---

## 1. Executive Summary

The AU E-Voting System is a secure, web-based digital voting platform for Adeleke University. It replaces paper ballots for Student Union Government (SUG) elections, faculty-level representative elections, and departmental elections. The platform serves students as voters, university administrators as election managers, and faculty administrators as scoped election managers.

The MVP focuses on correctness, trust, and usability over feature breadth. Every decision — from the results embargo to the audit log — is designed so that students and staff trust the outcome.

---

## 2. Goals & Success Metrics

| Goal | Metric |
|---|---|
| Students can vote from any device | ≥ 90% mobile-responsive test score |
| Zero double-votes | UniqueConstraint enforced at DB level |
| Admins control result timing | Results only visible after explicit publish action |
| Transparent process | Every vote action logged in immutable audit trail |
| Fast adoption | Student can register, verify, and vote in under 3 minutes |

---

## 3. User Roles

### 3.1 Student (Voter)
- Any enrolled student with a valid matric number
- Can register, complete verification, browse elections, cast votes, view published results
- Cannot see unpublished results or other students' votes

### 3.2 University Administrator (UniAdmin)
- Full platform access across all elections
- Can create/edit/delete elections of any type (university-wide, faculty, departmental)
- Can manage candidates (approve nominations or create directly)
- Can manage voters (verify, deactivate)
- Can publish/unpublish results at any time
- Can view live vote tallies before publishing
- Can view full audit logs

### 3.3 Faculty Administrator (FacultyAdmin)
- Scoped to their assigned faculty only
- Can create elections for their faculty or its departments
- Can manage candidates within their faculty scope
- Can publish results for their faculty elections
- Cannot access other faculties' data or university-wide elections

---

## 4. Feature Specifications

### 4.1 Authentication & Registration

**Registration (Students):**
- Fields: First Name, Last Name, Matric Number, Department, Faculty, Password (min 8 chars)
- Matric number is the unique identifier and login credential
- Account starts as `unverified`

**Login:**
- Students: Matric number + Password → Token
- Admins: Admin ID + Password → Token  
- Role-based redirect after login (student portal vs admin portal)
- Token stored in localStorage, sent as `Authorization: Token <key>` header

**Verification (MVP — Simple):**
- Admin marks students as verified via the Voters management page
- Future versions: OTP to university email, ID card scan, biometric
- Unverified students can browse elections but cannot cast votes
- System shows clear "Verify your account to vote" prompt

### 4.2 Elections

**Election Types:**
- `university` — open to all verified students
- `faculty` — open to verified students in the specified faculty
- `departmental` — open to verified students in the specified department

**Election Lifecycle:**
```
draft → active → completed
         ↕
      cancelled
```

- `draft`: Created but not yet open; students cannot see it
- `active`: Voting is open; visible to eligible students
- `completed`: Voting window closed (auto or manual); results may or may not be published
- `cancelled`: Abandoned election

**Election Fields:**
- Title, Description, Type, Faculty Scope (if faculty/dept), Department Scope (if dept)
- Start Date/Time, End Date/Time
- Status, Results Published (bool)
- Created by, Created at

**Auto-completion:** A scheduled task (or on-request check) marks elections `completed` when `end_date` passes.

### 4.3 Positions & Candidates

**Positions:** Each election has one or more positions (e.g. President, VP, Secretary General). Positions have a display order.

**Candidates:**
- Each candidate belongs to one position
- Fields: Name, Party/Affiliation, Bio (up to 500 chars), Photo URL
- Status: `pending` (nomination) | `approved` | `rejected`

**Candidate Nomination (MVP — Admin-managed):**
- UniAdmin/FacultyAdmin can directly create approved candidates
- Students can submit nominations (name, bio, photo); admin approves/rejects
- Nominations only accepted while election is in `draft` status

### 4.4 Voting

**Eligibility check before ballot loads:**
1. Student is verified
2. Election is active
3. Student has not already voted in this election
4. Student is in the correct scope (faculty/department) for faculty/dept elections

**Ballot flow:**
1. Student opens election → sees list of positions with candidate cards
2. Selects one candidate per position (or explicitly abstains)
3. Review screen showing all selections
4. Confirmation checkbox → Submit
5. Success screen with receipt hash

**Vote integrity:**
- `UniqueConstraint(voter, position)` at DB level — prevents double-vote even under concurrency
- `Vote.position` FK stored directly on the Vote row (denormalized) for the constraint
- `bulk_create` used for atomicity; `IntegrityError` caught and returns 409

### 4.5 Results Management (Key Feature)

**Before publishing:**
- Admin sees full live tallies in admin panel at all times
- Students see only "Results Pending" status
- No vote counts, percentages, or winner information exposed via API to student tokens

**Publishing:**
- UniAdmin or FacultyAdmin clicks "Publish Results" button
- Sets `election.results_published = True`
- Immediately visible to all eligible students
- Can be unpublished (reverted to Pending) if needed before certification

**Results display (once published):**
- Bar chart per position
- Vote count + percentage per candidate
- Turnout rate (votes cast / eligible voters)
- Winner highlighted

### 4.6 Announcements

- Admins can post announcements attached to an election (e.g. "Voting opens tomorrow at 8am")
- Also global announcements not tied to a specific election
- Students see announcements on their dashboard
- Announcement fields: Title, Body, Election (optional FK), Priority (normal/urgent), Created At

### 4.7 Audit Log

Every significant action writes an immutable audit entry:

| Event | Triggered By |
|---|---|
| `USER_REGISTERED` | Student registration |
| `USER_VERIFIED` | Admin verifies voter |
| `VOTE_CAST` | Student submits ballot |
| `ELECTION_CREATED` | Admin |
| `ELECTION_STATUS_CHANGED` | Admin or auto |
| `RESULTS_PUBLISHED` | Admin |
| `RESULTS_UNPUBLISHED` | Admin |
| `CANDIDATE_APPROVED` | Admin |
| `LOGIN_FAILED` | Auth system |

Audit entries: `actor`, `action`, `target`, `metadata (JSON)`, `ip_address`, `timestamp`

---

## 5. System Architecture

### 5.1 Backend — Django REST Framework

```
backend/
├── config/
│   ├── settings.py          # Env-aware settings
│   ├── urls.py              # Root URL routing
│   └── wsgi.py
├── accounts/                # Users, auth, verification
│   ├── models.py            # User (AbstractUser)
│   ├── serializers.py
│   ├── views.py             # register, login, logout, me, profile, verify
│   └── urls.py
├── elections/               # Core domain
│   ├── models.py            # Election, Position, Candidate, Vote, Nomination, Announcement, AuditLog
│   ├── serializers.py
│   ├── views.py             # All election, voting, results, admin endpoints
│   └── urls.py
└── manage.py
```

**Key API Endpoints:**

```
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/logout/
GET    /api/auth/me/
PUT    /api/auth/profile/

GET    /api/elections/                          # Student: active elections
GET    /api/elections/<id>/ballot/              # Student: ballot + has_voted
POST   /api/elections/<id>/vote/               # Student: cast votes
GET    /api/elections/<id>/results/            # Student: published results only

GET    /api/announcements/                     # Student: all announcements

GET    /api/admin/dashboard/                   # Admin: KPIs
GET    /api/admin/elections/                   # Admin: all elections
POST   /api/admin/elections/                   # Admin: create election
PATCH  /api/admin/elections/<id>/              # Admin: update election
POST   /api/admin/elections/<id>/publish/      # Admin: publish results
POST   /api/admin/elections/<id>/unpublish/    # Admin: unpublish results
GET    /api/admin/elections/<id>/results/      # Admin: live results (always)
GET    /api/admin/voters/                      # Admin: all students
POST   /api/admin/voters/<id>/verify/          # Admin: verify student
GET    /api/admin/audit-log/                   # Admin: audit entries
POST   /api/admin/announcements/               # Admin: create announcement
POST   /api/admin/candidates/<id>/approve/     # Admin: approve nomination
```

### 5.2 Frontend — Vanilla HTML/CSS/JS

```
frontend/
├── assets/
│   ├── css/
│   │   └── app.css          # Global variables, utilities, components
│   └── js/
│       └── app.js           # Shared: API client, auth, toast, nav, dark mode
├── student/
│   ├── login.html           # Landing + Login (combined)
│   ├── signup.html          # Registration
│   ├── dashboard.html       # Student home
│   ├── elections.html       # Elections list
│   ├── ballot.html          # Vote casting
│   ├── results.html         # Published results
│   └── profile.html         # Account management
└── admin/
    ├── login.html           # Admin login
    ├── dashboard.html       # Admin overview
    ├── elections.html       # Election management list
    ├── create-election.html # Full election wizard
    ├── results.html         # Results + publish control
    └── voters.html          # Voter management + verification
```

**Shared `app.js` pattern (no duplication):**
Every page includes `/assets/js/app.js` which provides:
- `API` object with all fetch wrappers
- `Auth` object (getSession, setSession, requireRole)
- `Toast` (showToast)
- `Nav` (createStudentNav, createAdminNav)
- Dark mode

Each page has a small inline `<script>` calling its page-specific logic.

### 5.3 Database — SQLite (dev) / PostgreSQL (prod)

```
accounts_user          — custom user model
elections_election     — election events
elections_position     — positions within elections
elections_candidate    — candidates for positions
elections_vote         — immutable vote records
elections_nomination   — student candidate applications
elections_announcement — news for students
elections_auditlog     — immutable action history
```

---

## 6. Data Models (Summary)

```python
# accounts
User: matric, first_name, last_name, email, password,
      role(student|uni_admin|faculty_admin),
      faculty, department, is_verified, is_active

# elections
Election: title, description, type(university|faculty|departmental),
          faculty_scope, department_scope, start_date, end_date,
          status(draft|active|completed|cancelled),
          results_published, created_by

Position: election, title, order
Candidate: position, name, party, bio, photo_url, status(pending|approved|rejected)
Vote: voter, candidate, position, timestamp  — unique(voter, position)
Nomination: election, position, applicant, name, party, bio, photo_url,
            status(pending|approved|rejected), reviewed_by, reviewed_at
Announcement: title, body, election(optional), priority(normal|urgent),
              created_by, created_at
AuditLog: actor, action, target_type, target_id, metadata, ip_address, timestamp
```

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Security** | Token auth, role-based access, DB-level vote uniqueness |
| **Performance** | Annotated querysets (no N+1), paginated list endpoints |
| **Accessibility** | WCAG 2.1 AA colour contrast, keyboard navigation |
| **Responsive** | Mobile-first; works on 320px screens |
| **Audit** | All state-changing actions logged |
| **Error handling** | All API errors return `{error: "..."}` with appropriate HTTP codes |
| **Timezone** | All dates stored UTC, displayed in Africa/Lagos |

---

## 8. Out of Scope (Post-MVP)

- Email / SMS OTP verification
- Biometric ID scan
- Blockchain vote ledger
- Real-time WebSocket updates
- Candidate campaign pages (extended)
- Multi-language support
- Native mobile app
- Two-factor admin authentication
- SAML/SSO with university identity provider

---

## 9. Milestones

| Week | Deliverable |
|---|---|
| 1 | Backend models, migrations, seed data, auth endpoints |
| 2 | Election CRUD, voting endpoint, results API |
| 3 | Student frontend (login, dashboard, ballot, results) |
| 4 | Admin frontend (dashboard, election management, results publish, voter verification) |
| 5 | Integration testing, bug fixes, deployment |
