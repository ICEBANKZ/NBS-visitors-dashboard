# PRD — NBS Front Desk Visitors Register

## Original Problem Statement
Build a professional FRONT DESK VISITORS REGISTER web application for the NATIONAL BUREAU OF STATISTICS capturing: Date, visitor's name, address, telephone, whom to see, department, purpose of visit (official/workshop/meetings), floor, tag number, time in & time out, status (tag submitted / no tag allocated). Authentication login for front desk staff. Green theme representing the national statistical office.

### User Choices
- Auth: BOTH JWT email/password AND Emergent-managed Google login.
- Roles: Admin + Front Desk (staff).
- Reporting: Dashboard stats + CSV/PDF export.
- One-click visitor check-out.
- NBS logo provided (oval "nbs", green).
- Visitor photo capture (live webcam, optional) + printable badge with QR.
- Geo-restriction: admin-configurable office GPS + radius; staff-only; admins exempt; hard block.
- Offline/online capability for front desk officers (work without internet).
- Admin can add/manage departments and office floor/wing numbers.

## Architecture
- Frontend: React 19 (CRA + craco), Tailwind, shadcn/ui, recharts, sonner, qrcode.react. Green theme (Work Sans headings, IBM Plex Sans body). PWA service worker (`public/sw.js`) + manifest.
- Backend: FastAPI (`/api` prefix), modular: `auth.py`, `admin.py`, `visitors.py`, `settings.py`, `database.py`, `models.py`, `server.py`.
- DB: MongoDB (UUID `id` fields, `_id` excluded). Collections: users, user_sessions, visitors, settings (geofence + options), login (n/a).
- Auth: dual — JWT httpOnly cookies (access+refresh) and Emergent Google session_token cookie; `get_current_user` accepts either. Admin seeded on startup.

## User Personas
- Front Desk Officer (staff): registers/checks out visitors on-site; geo-locked when enabled; can work offline.
- Administrator: full access, manages staff accounts, departments/floors, geofence; exempt from geo-restriction; anywhere access.

## Core Requirements (static)
Visitor fields + statuses, dual auth, RBAC, dashboard + export, check-out, photo+badge+QR, geofence, offline, admin-managed depts/floors.

## Implemented (2026-07-09)
- Auth: JWT login/register, Google session exchange, /me, logout; admin seed; password min length; self-role-change guard.
- Visitors: create (auto time_in, tag status), list (search/filter), get, update, one-click checkout, delete (admin), stats summary, CSV + PDF export.
- Admin: users CRUD (self-delete + self-demote blocked).
- Settings: geofence GET/PUT + verify (haversine, admin-exempt); options (departments/floors) GET/PUT seeded on startup.
- Frontend: split-screen Login (JWT + Google), sidebar Layout with NBS logo, Dashboard (stat cards + trend/purpose charts + recent), Visitors Register (table, filters, dialog form with webcam photo, checkout, edit, delete, print badge), Badge print page (logo/photo/details/QR), Admin Staff Accounts, Settings (geofence + departments/floors manager), GeoGate hard-block, Offline provider (queue + auto-sync + indicator), PWA SW/manifest.
- Testing: iteration_1 (25/25 backend, all FE), iteration_2 (34/34 backend, all FE). No open bugs.

## Known Notes
- Recharts logs cosmetic width(-1)/height(-1) warnings on first paint (non-functional).
- Photos stored as base64 data URLs in visitor docs (excluded from list responses).
- Google OAuth full redirect not E2E-tested (external); JWT is primary path.

## Backlog / Next
- P1: Object-storage for visitor photos (instead of base64) to keep docs lean.
- P1: Surface a toast if a queued offline record is rejected (4xx) during sync.
- P2: Department/floor usage analytics on dashboard; visitor pre-registration / expected-visitors.
- P2: SW cache size cap; installable PWA polish (offline splash).
- P2: Audit log of check-in/out actions per staff.
