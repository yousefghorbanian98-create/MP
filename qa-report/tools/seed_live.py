"""بذر محیط QA محلی: یک ادمین (id=1) و ۲۵۰ عضو فیک.  فقط برای SQLite محلی."""
import sys
from db.base import get_session_factory
from db.models import AdminPermission, User
from app.security.jwt import create_access_token

ADMIN_PHONE = "09120000001"
PERMS = ["finance.read", "finance.write", "reports.confidential", "roles.manage", "flags.write"]  # KNOWN_PERMISSIONS در app/security/grants.py
N_MEMBERS = 250

S = get_session_factory()()
admin = S.query(User).filter_by(phone=ADMIN_PHONE).first()
if admin is None:
    admin = User(phone=ADMIN_PHONE, full_name="ادمین QA", role="admin")
    S.add(admin); S.commit()
    for p in PERMS:
        S.add(AdminPermission(user_id=admin.id, permission=p, note="qa seed"))
    S.commit()
members = []
for i in range(N_MEMBERS):
    phone = f"0913{i:07d}"
    u = S.query(User).filter_by(phone=phone).first()
    if u is None:
        u = User(phone=phone, full_name=f"عضو فیک {i+1}", role="member")
        S.add(u); S.commit()
    members.append(u.id)
S.close()
print("admin_id", admin.id, "members", len(members), file=sys.stderr)
