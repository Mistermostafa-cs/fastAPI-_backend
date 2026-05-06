# Academic Year Refactor – Integration Guide

## What was added

| File | Purpose |
|---|---|
| `app/db/new_entities.py` | `Term` and `SubjectOffering` SQLAlchemy models |
| `app/schemas/term_offerings.py` | Pydantic I/O schemas for the new models |
| `app/services/term_offering_service.py` | Business logic: auto-terms, subject queries, migration helper |
| `app/api/term_offerings.py` | New API router mounted at `/api/v1/v2/academics/…` |
| `app/db/models.py` | Updated to import `new_entities` so `create_all()` covers new tables |
| `app/api/academics.py` | Original file + auto-term creation on `POST /academics/academic-years` |
| `app/main.py` | Original file + includes `term_offerings_router` |
| `migrate_to_offerings.py` | Standalone CLI migration script |

## What was NOT changed

- `Student`, `StudentProfile`, `Enrollment`, `ClassSubject` models – untouched.
- All existing `/academics/*` API routes – identical behaviour.
- Old `ClassSubjects` table is kept and still backed by all existing FK relations.

---

## New database tables

### `Terms`
| Column | Type | Notes |
|---|---|---|
| TermID | PK | auto |
| AcademicYearID | FK → AcademicYears | |
| TermName | VARCHAR(50) | "Term 1" / "Term 2" |
| TermNumber | INT | 1 or 2 |
| StartDate | DATE | |
| EndDate | DATE | |
| IsActive | BOOL | |

Unique constraint on `(AcademicYearID, TermNumber)`.

### `SubjectOfferings`
| Column | Type | Notes |
|---|---|---|
| OfferingID | PK | auto |
| SubjectID | FK → Subjects | |
| TermID | FK → Terms | |
| ClassID | FK → Classes | |
| TeacherID | FK → TeacherProfiles | |
| LegacyClassSubjectID | FK → ClassSubjects (nullable) | migration traceability |
| IsActive | BOOL | |

Unique constraint on `(SubjectID, TermID, ClassID)`.

---

## New API endpoints

All mounted under `{API_PREFIX}/v2/academics/`.

### Terms

| Method | Path | Description |
|---|---|---|
| GET | `/terms` | List terms (filter: `?academic_year_id=`) |
| POST | `/terms` | Create term manually |
| POST | `/academic-years/{id}/init-terms` | Auto-create Term 1 + 2 for existing year |

### Subject Offerings

| Method | Path | Description |
|---|---|---|
| GET | `/subject-offerings` | List offerings (filters: `term_id`, `class_id`, `academic_year_id+class_id`) |
| POST | `/subject-offerings` | Create an offering |
| PATCH | `/subject-offerings/{id}/deactivate` | Deactivate an offering |

### Migration

| Method | Path | Description |
|---|---|---|
| POST | `/migrations/class-subjects-to-offerings` | Run migration (params: `academic_year_id`, `dry_run`) |

---

## Running the migration

### Via API (recommended for production)
```
POST /api/v1/v2/academics/migrations/class-subjects-to-offerings
     ?dry_run=true          # preview first
POST /api/v1/v2/academics/migrations/class-subjects-to-offerings
     ?academic_year_id=1    # then commit year by year
```

### Via CLI
```bash
# Preview all years
python migrate_to_offerings.py --dry-run

# Migrate a single year
python migrate_to_offerings.py --year 1

# Migrate all years
python migrate_to_offerings.py
```

---

## Auto-term creation

From now on, every `POST /academics/academic-years` call automatically creates
Term 1 and Term 2. The year span is split in half:

- **Term 1** → `StartDate … midpoint`
- **Term 2** → `midpoint+1 … EndDate`

For years created before this change, use the `init-terms` endpoint:
```
POST /api/v1/v2/academics/academic-years/1/init-terms
```

---

## Fetching subjects via the new system

```python
# Old way (still works)
db.query(ClassSubject).filter(ClassSubject.ClassID == class_id,
                               ClassSubject.AcademicYearID == year_id)

# New way
from app.services.term_offering_service import get_subjects_by_class_and_academic_year
offerings = get_subjects_by_class_and_academic_year(db, class_id, academic_year_id)

# Or by specific term
from app.services.term_offering_service import get_subjects_by_term
offerings = get_subjects_by_term(db, term_id, class_id)
```
