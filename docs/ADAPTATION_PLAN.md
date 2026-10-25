# AIHMS adaptation plan

Source snapshot imported on 2026-10-25 through the GitHub connector because shell DNS is restricted. All 198 original files were checked against their Git blob hashes before modification. This is a source import into a new local repository, not a full Git history clone.

1. Replace product branding with AI Hospital Management System (AIHMS), remove personal biography/contact/profile links and previous deployment URLs; retain framework dependency notices.
2. Correct portable configuration, remove shared secrets, add explicit environment examples and a single Docker Compose workflow with PostgreSQL, Redis, backend, worker, frontend, and local mail.
3. Add repeatable synthetic development accounts and data, using a password provided by the operator; no embedded reusable credentials.
4. Repair high-impact integration/security issues found during inspection: public staff-role registration, editable role verification fields, prescription ownership, appointment conflicts/rescheduling, unsafe uploaded files, private file delivery, two-factor login challenge, shared external notification targets and silent AI success.
5. Add targeted regression tests, execute all feasible static/runtime checks, and document verification limits explicitly.

Keep the imported Django REST Framework/Next.js architecture. Do not restart the cancelled greenfield implementation or claim the much larger initial specification is delivered by this adaptation.
