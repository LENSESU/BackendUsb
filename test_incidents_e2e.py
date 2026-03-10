"""Script de prueba e2e del endpoint de incidentes (#107, #108, #109)."""

import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000/api/v1"
RESULTS = []


def req(method, path, body=None, token=None):
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


def check(step, status, expected, body=None, extra_check=None):
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
print("FLUJO DE PRUEBA E2E — INCIDENTES (#107, #108, #109)")
print("=" * 60)

# ── PASO 1: Login estudiante ──
print("\n── PASO 1: Login como ESTUDIANTE ──")
s, b = req("POST", "/auth/login", {"email": "estudiante@usb.ve", "password": "estudiante123"})
check("Login estudiante", s, 200, b, lambda b: ("access_token" in b, "token recibido"))
est_token = b.get("access_token", "")
est_user_id = None

# Obtener user_id del /me
s2, b2 = req("GET", "/auth/me", token=est_token)
if s2 == 200:
    est_user_id = b2.get("user_id")

# ── PASO 2: Crear incidente (requiere UUIDs de category y photo) ──
print("\n── PASO 2: Crear incidente como ESTUDIANTE ──")
from uuid import uuid4
cat_id = str(uuid4())
photo_id = str(uuid4())
payload = {
    "category_id": cat_id,
    "description": "Luminaria dañada en el pasillo B del edificio MYS",
    "before_photo_id": photo_id,
    "priority": "Alta",
    "campus_place": "Edificio MYS, Piso 2",
    "latitude": 10.409,
    "longitude": -66.883,
}
s, b = req("POST", "/incidents/", payload, est_token)
check("#108 — Responde 201 Created", s, 201)
incident_id = b.get("id")

# ── PASO 3: Verificar metadatos automáticos ──
print("\n── PASO 3: Verificar metadatos automáticos (#107) ──")
check(
    "#107 — student_id = usuario autenticado",
    s, 201, b,
    lambda b: (b.get("student_id") == est_user_id, f"student_id={b.get('student_id','?')[:12]}...")
)
check(
    "#107 — created_at registrado automáticamente",
    s, 201, b,
    lambda b: (b.get("created_at") is not None, f"created_at={b.get('created_at','?')[:19]}")
)
check(
    "#107 — status inicial = 'Nuevo'",
    s, 201, b,
    lambda b: (b.get("status") == "Nuevo", f"status={b.get('status')}")
)
check(
    "Datos de negocio correctos",
    s, 201, b,
    lambda b: (
        b.get("description") == payload["description"]
        and b.get("category_id") == cat_id
        and b.get("priority") == "Alta",
        f"desc OK, cat OK, priority OK"
    )
)
check(
    "Ubicación registrada",
    s, 201, b,
    lambda b: (
        b.get("campus_place") == "Edificio MYS, Piso 2",
        f"campus={b.get('campus_place')}"
    )
)

# ── PASO 4: Obtener incidente por ID ──
print("\n── PASO 4: Obtener incidente por ID ──")
s, b = req("GET", f"/incidents/{incident_id}", token=est_token)
check("GET incidente por ID", s, 200, b, lambda b: (b.get("id") == incident_id, "id correcto"))

# ── PASO 5: Listar incidentes ──
print("\n── PASO 5: Listar incidentes ──")
s, b = req("GET", "/incidents/", token=est_token)
check("Listar incidentes", s, 200, b, lambda b: (isinstance(b, list) and len(b) >= 1, f"{len(b)} incidentes"))

# ── PASO 6: Sin token → 403 ──
print("\n── PASO 6: Sin token → 403 ──")
s, b = req("POST", "/incidents/", payload)
check("Crear sin token → 403", s, 403)
s, b = req("GET", "/incidents/")
check("Listar sin token → 403", s, 403)

# ── PASO 7: Token inválido → 401 ──
print("\n── PASO 7: Token inválido → 401 ──")
s, b = req("POST", "/incidents/", payload, "token.invalido.abc")
check("Token inválido → 401", s, 401)

# ── PASO 8: Login admin y crear incidente ──
print("\n── PASO 8: Admin crea incidente ──")
s, b = req("POST", "/auth/login", {"email": "admin@usb.ve", "password": "admin123"})
admin_token = b.get("access_token", "")
s3, b3 = req("GET", "/auth/me", token=admin_token)
admin_user_id = b3.get("user_id") if s3 == 200 else None

s, b = req("POST", "/incidents/", {
    "category_id": str(uuid4()),
    "description": "Incidente reportado por admin",
    "before_photo_id": str(uuid4()),
}, admin_token)
check("Admin crea incidente → 201", s, 201)
check(
    "Admin student_id = su propio user_id",
    s, 201, b,
    lambda b: (b.get("student_id") == admin_user_id, f"student_id={b.get('student_id','?')[:12]}...")
)

# ── PASO 9: Técnico crea incidente ──
print("\n── PASO 9: Técnico crea incidente ──")
s, b = req("POST", "/auth/login", {"email": "tecnico@usb.ve", "password": "tecnico123"})
tec_token = b.get("access_token", "")
s, b = req("POST", "/incidents/", {
    "category_id": str(uuid4()),
    "description": "Incidente reportado por técnico",
    "before_photo_id": str(uuid4()),
}, tec_token)
check("Técnico crea incidente → 201", s, 201)

# ═══════════════════════════════════════════════════════════════════
total = len(RESULTS)
passed = sum(RESULTS)
failed = total - passed
print("\n" + "=" * 60)
print(f"RESULTADO: {passed}/{total} pasaron", end="")
if failed:
    print(f" — {failed} fallaron")
else:
    print(" ✅ TODOS OK")
print("=" * 60)
