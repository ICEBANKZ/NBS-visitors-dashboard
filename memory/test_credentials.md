# Test Credentials — NBS Front Desk Visitors Register

## Admin (JWT email/password)
- Email: `admin@nbs.gov`
- Password: `Admin@NBS2026`
- Role: admin

## Front Desk Staff (create via Admin panel, or self-register at /login → "Create account")
- Any staff account created gets role `staff`.
- Example test staff (create if needed): `staff@nbs.gov` / `Staff@NBS2026`

## Google Auth (Emergent-managed)
- "Continue with Google" on the login page.
- Google-authenticated users are auto-created with role `staff` on first login.
- No app-managed password for Google accounts.

## Auth endpoints
- POST /api/auth/register  (name, email, password) → creates staff
- POST /api/auth/login      (email, password)
- POST /api/auth/session    (session_id)  → Emergent Google exchange
- GET  /api/auth/me
- POST /api/auth/logout

## Notes
- Cookies: httpOnly `access_token` + `refresh_token` (JWT) or `session_token` (Google), secure + samesite=none.
- Admin user management: /api/users (GET/POST/PUT/DELETE) — admin only.
