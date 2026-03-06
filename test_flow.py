"""Script de prueba end-to-end del flujo completo de RBAC y ownership."""

import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000/api/v1"
RESULTS = []


def req(method: str, path: str, body=None, token=None):
    """Hace un request HTTP y devuelve (status, body_dict)."""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode()
            b = json.loads(raw) if raw.strip() else {}
        except Exception:
            b = {}
        return e.code, b


def check(step: str, status: int, expected: int, body=None, extra_check=None):
    ok = status == expected
    extra_ok = True
    extra_msg = ""
    if extra_check and ok:
        extra_ok, extra_msg = extra_check(body)
    passed = ok and extra_ok
    icon = "PASS" if passed else "FAIL"
    RESULTS.append(passed)
    print(f"  [{icon}] {step}")
    print(f"         Esperado: {expected} | Obtenido: {status}", end="")
    if extra_msg:
        print(f" | {extra_msg}", end="")
    if not ok:
        print(f"\n         Body: {json.dumps(body, ensure_ascii=False)[:200]}", end="")
    print()


# ═══════════════════════════════════════════════════════════════════
print("=" * 60)
print("FLUJO DE PRUEBA COMPLETO — #61 y #63")
print("=" * 60)

# ── PASO 1: Login estudiante ──
print("\n── PASO 1: Login como ESTUDIANTE ──")
s, b = req("POST", "/auth/login", {"email": "estudiante@usb.ve", "password": "estudiante123"})
check("Login estudiante", s, 200, b, lambda b: ("access_token" in b, "access_token recibido"))
est_token = b.get("access_token", "")
est_refresh = b.get("refresh_token", "")

# ── PASO 2: Crear item como estudiante ──
print("\n── PASO 2: Crear item como ESTUDIANTE ──")
s, b = req("POST", "/items/", {"name": "Item del estudiante", "description": "Test ownership"}, est_token)
check("Crear item", s, 201, b, lambda b: (b.get("owner_id") is not None, f"owner_id={b.get('owner_id','?')[:12]}..."))
item_id = b.get("id", "")
est_user_id = b.get("owner_id", "")

# ── PASO 3: Listar items como estudiante ──
print("\n── PASO 3: Listar items como ESTUDIANTE ──")
s, b = req("GET", "/items/", token=est_token)
check("Listar items", s, 200, b, lambda b: (isinstance(b, list) and len(b) > 0, f"{len(b)} items"))

# ── PASO 4: Obtener item por ID ──
print("\n── PASO 4: Obtener item por ID ──")
s, b = req("GET", f"/items/{item_id}", token=est_token)
check("Get item", s, 200, b, lambda b: (b.get("id") == item_id, f"id correcto"))

# ── PASO 5: Login técnico e intentar DELETE ajeno → 403 ──
print("\n── PASO 5: Login TECNICO + DELETE item ajeno ──")
s, b = req("POST", "/auth/login", {"email": "tecnico@usb.ve", "password": "tecnico123"})
check("Login tecnico", s, 200)
tec_token = b.get("access_token", "")

s, b = req("DELETE", f"/items/{item_id}", token=tec_token)
check("Tecnico DELETE item ajeno → 403", s, 403, b,
      lambda b: (b.get("detail", {}).get("error_code") == "CROSS_ACCESS_DENIED", f"error_code={b.get('detail',{}).get('error_code')}"))

# ── PASO 6: Login admin y DELETE item ajeno → 204 (bypass) ──
print("\n── PASO 6: Login ADMIN + DELETE item ajeno (bypass) ──")
s, b = req("POST", "/auth/login", {"email": "admin@usb.ve", "password": "admin123"})
check("Login admin", s, 200)
admin_token = b.get("access_token", "")

s, b = req("DELETE", f"/items/{item_id}", token=admin_token)
check("Admin DELETE item ajeno → 204", s, 204)

# ── PASO 7: Verificar item eliminado ──
print("\n── PASO 7: Verificar item eliminado ──")
s, b = req("GET", f"/items/{item_id}", token=admin_token)
check("Get item eliminado → 404", s, 404)

# ── PASO 8: Logout admin ──
print("\n── PASO 8: Logout ADMIN ──")
s, b = req("POST", "/auth/logout", token=admin_token)
check("Logout admin", s, 200, b, lambda b: ("message" in b, b.get("message", "")))

# ── PASO 9: Usar token revocado → 401 ──
print("\n── PASO 9: Token revocado → 401 ──")
s, b = req("GET", "/items/", token=admin_token)
check("List con token revocado → 401", s, 401, b,
      lambda b: (b.get("detail", {}).get("error_code") == "TOKEN_REVOKED", f"error_code={b.get('detail',{}).get('error_code')}"))

# ── PASO 10: Sin token → 403 ──
print("\n── PASO 10: Sin token → 403 ──")
s, b = req("GET", "/items/")
check("Listar sin token → 403", s, 403)
s, b = req("POST", "/items/", {"name": "x"})
check("Crear sin token → 403", s, 403)
s, b = req("DELETE", "/items/00000000-0000-0000-0000-000000000000")
check("Delete sin token → 403", s, 403)

# ── PASO 11: Token inválido → 401 ──
print("\n── PASO 11: Token inválido → 401 ──")
s, b = req("GET", "/items/", token="este.no.es.un.jwt.valido")
check("Token invalido → 401", s, 401)

# ── PASO 12: Refresh token ──
print("\n── PASO 12: Refresh token ──")
s, b = req("POST", "/auth/refresh", {"refresh_token": est_refresh})
check("Refresh token estudiante", s, 200, b,
      lambda b: ("access_token" in b, "nuevo access_token recibido"))

# ── PASO 13: Validate token ──
print("\n── PASO 13: Validate token ──")
s, b = req("POST", "/auth/validate", {"token": est_token})
check("Validate token valido", s, 200, b,
      lambda b: (b.get("valid") is True, f"valid={b.get('valid')}"))

s, b = req("POST", "/auth/validate", {"token": "token.falso"})
check("Validate token invalido", s, 200, b,
      lambda b: (b.get("valid") is False, f"valid={b.get('valid')}"))

# ── PASO 14: Dueño elimina su propio item ──
print("\n── PASO 14: Dueño elimina su propio item ──")
s, b = req("POST", "/items/", {"name": "Para borrar yo mismo"}, est_token)
check("Crear item propio", s, 201)
own_item_id = b.get("id", "")
s, b = req("DELETE", f"/items/{own_item_id}", token=est_token)
check("Dueño DELETE propio → 204", s, 204)

# ── PASO 15: GET /auth/me ──
print("\n── PASO 15: Auth /me ──")
s, b = req("GET", "/auth/me", token=est_token)
check("GET /me con token valido", s, 200, b,
      lambda b: (b.get("user_id") is not None, f"user_id={b.get('user_id','?')[:12]}..."))

# ═══════════════════════════════════════════════════════════════════
total = len(RESULTS)
passed = sum(RESULTS)
failed = total - passed
print("\n" + "=" * 60)
print(f"RESULTADO: {passed}/{total} pasaron", end="")
if failed:
    print(f" — {failed} fallaron ❌")
else:
    print(" ✅ TODOS OK")
print("=" * 60)
