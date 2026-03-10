"""Prueba manual paso a paso de #107, #108, #109 contra Docker."""
import json, urllib.request, urllib.error

BASE = "http://localhost:8000/api/v1"

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

print("=" * 60)
print("  PRUEBA MANUAL — #107, #108, #109")
print("=" * 60)

# --- Login ---
print("\n1) Login como estudiante@usb.ve")
s, b = req("POST", "/auth/login", {"email": "estudiante@usb.ve", "password": "estudiante123"})
token = b["access_token"]
s2, me = req("GET", "/auth/me", token=token)
user_id = me["user_id"]
print(f"   user_id del JWT: {user_id}")

# --- #108: Crear incidente → 201 ---
from uuid import uuid4
print("\n2) POST /incidents/ — Crear incidente")
payload = {
    "category_id": str(uuid4()),
    "description": "Luminaria danada en pasillo B",
    "before_photo_id": str(uuid4()),
    "priority": "Alta",
    "campus_place": "Edificio MYS, Piso 2",
}
print(f"   Payload enviado (SIN student_id, SIN created_at, SIN status):")
for k, v in payload.items():
    print(f"     {k}: {v}")

s, inc = req("POST", "/incidents/", payload, token)

print(f"\n   >>> HTTP Status: {s}")
print(f"   {'PASS' if s == 201 else 'FAIL'} #108 — Respuesta 201 Created")

# --- #107: Metadatos automáticos ---
print(f"\n3) Verificar metadatos automaticos (#107)")

print(f"\n   student_id en respuesta: {inc.get('student_id')}")
print(f"   user_id del JWT:         {user_id}")
match_user = inc.get("student_id") == user_id
print(f"   {'PASS' if match_user else 'FAIL'} #107 — student_id = usuario autenticado")

print(f"\n   created_at: {inc.get('created_at')}")
has_created = inc.get("created_at") is not None
print(f"   {'PASS' if has_created else 'FAIL'} #107 — created_at asignado automaticamente")

print(f"\n   status: {inc.get('status')}")
is_nuevo = inc.get("status") == "Nuevo"
print(f"   {'PASS' if is_nuevo else 'FAIL'} #107 — Estado inicial = 'Nuevo'")

print(f"\n   El cliente NO envio student_id, created_at ni status.")
print(f"   El backend los asigno automaticamente. El cliente no los controla.")

# --- #109: Pruebas de auth ---
print(f"\n4) Pruebas de autenticacion (#109)")

s_no_token, _ = req("POST", "/incidents/", payload)
print(f"   Sin token     -> HTTP {s_no_token}  {'PASS' if s_no_token == 403 else 'FAIL'} (esperado 403)")

s_bad_token, _ = req("POST", "/incidents/", payload, "token.invalido.abc")
print(f"   Token invalido -> HTTP {s_bad_token}  {'PASS' if s_bad_token == 401 else 'FAIL'} (esperado 401)")

# --- Resumen ---
results = [s == 201, match_user, has_created, is_nuevo, s_no_token == 403, s_bad_token == 401]
passed = sum(results)
print(f"\n{'=' * 60}")
print(f"  RESULTADO: {passed}/{len(results)} verificaciones pasaron", end="")
if passed == len(results):
    print(" ✅")
else:
    print(f" — {len(results)-passed} fallaron")
print("=" * 60)

print(f"\n  Respuesta completa del incidente creado:")
print(json.dumps(inc, indent=2, ensure_ascii=False))
