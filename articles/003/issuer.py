"""Task-scoped capabilities; demonstration only, not cryptographically signed."""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from uuid import uuid4

@dataclass
class Capability:
    token: str
    task_id: str
    tenant: str
    action: str
    resource: str
    expires_at: datetime
    revoked: bool = False

class Issuer:
    def __init__(self):
        self.grants = {}

    def issue(self, task_id, tenant, action, resource, ttl_seconds=60):
        grant = Capability(uuid4().hex, task_id, tenant, action, resource,
                           datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds))
        self.grants[grant.token] = grant
        return grant.token

    def validate(self, token, task_id, tenant, action, resource):
        grant = self.grants.get(token)
        return bool(grant and not grant.revoked
                    and datetime.now(timezone.utc) < grant.expires_at
                    and (grant.task_id, grant.tenant, grant.action, grant.resource)
                    == (task_id, tenant, action, resource))

    def revoke(self, token):
        if token in self.grants:
            self.grants[token].revoked = True
