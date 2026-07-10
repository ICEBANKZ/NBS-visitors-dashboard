# NBS Front Desk Register — Testing Playbook

## Accounts (see /app/memory/test_credentials.md)
- Admin: admin@nbs.gov / Admin@NBS2026 (role admin, geo-exempt)
- Staff: staff@nbs.gov / Staff@NBS2026 (role staff, geo-locked when geofence enabled)

## Auth (dual system)
- JWT email/password: POST /api/auth/login, /register → sets httpOnly access_token + refresh_token cookies (secure, samesite=none).
- Google (Emergent): POST /api/auth/session {session_id} → sets session_token cookie.
- GET /api/auth/me works with either cookie or Authorization: Bearer.
- Same-origin: frontend uses REACT_APP_BACKEND_URL; cookies flow automatically with withCredentials.

## Backend curl
```
curl -c c.txt -X POST $URL/api/auth/login -H "Content-Type: application/json" -d '{"email":"admin@nbs.gov","password":"Admin@NBS2026"}'
curl -b c.txt $URL/api/auth/me
```

## Visitors
- POST /api/visitors (auth): visit_date, visitor_name, whom_to_see, department, purpose required; time_in auto; tag_status auto (tag_allocated if tag_number else no_tag_allocated); visit_status checked_in. Optional photo (base64 data URL).
- GET /api/visitors (filters: search, purpose, status, visit_date) — excludes photo.
- GET /api/visitors/{id} — includes photo.
- POST /api/visitors/{id}/checkout — sets time_out, visit_status=checked_out, tag_submitted if was allocated.
- PUT /api/visitors/{id}; DELETE /api/visitors/{id} (admin only).
- GET /api/visitors/stats/summary; GET /api/visitors/export/csv; /export/pdf.

## Admin users
- /api/users GET/POST/PUT/DELETE (admin only). Cannot delete own account.

## Geofence (admin Settings)
- GET /api/settings/geofence (auth); PUT (admin).
- POST /api/settings/geofence/verify {latitude, longitude} → {allowed, distance_m, radius_m}.
- Admin always allowed (exempt). Disabled geofence → everyone allowed.
- DEFAULT STATE: geofence DISABLED (so normal login works). Office coords stored: 9.05785, 7.49508, radius 200m.
- To test hard block: as staff, enable geofence with far-away office; staff verify returns allowed=false.

## Frontend notes
- Photo capture uses webcam (getUserMedia) — NOT available in headless; treat photo as optional/skip.
- Print badge: /badge/{id} renders logo, photo, details, QR (qrcode.react).
- Staff must NOT see "Staff Accounts" or "Settings" nav; /users and /settings redirect staff to /dashboard.
