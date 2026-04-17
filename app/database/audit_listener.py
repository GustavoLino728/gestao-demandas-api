from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from app.database.base import AuditMixin
from app.core.context import get_current_user_id, get_current_ip


# Campos que nunca devem aparecer no diff (evita poluição no log)
_IGNORED_FIELDS = frozenset({
    "created_at", "updated_at", "created_by_id", "updated_by_id"
})


def _get_changes(obj) -> dict:
    """Retorna apenas os campos que realmente mudaram com valores old/new."""
    changes = {}
    state = inspect(obj)

    for attr in state.attrs:
        if attr.key in _IGNORED_FIELDS:
            continue
        history = attr.load_history()
        if history.has_changes():
            old = history.deleted[0] if history.deleted else None
            new = history.added[0] if history.added else None
            if old != new:
                changes[attr.key] = {"old": old, "new": new}
    return changes


@event.listens_for(Session, "before_flush")
def audit_before_flush(session: Session, flush_context, instances):
    """
    Roda automaticamente antes de todo flush.
    Detecta objetos novos, modificados e deletados.
    """
    # Import lazy para evitar circular imports
    from app.domain.audit.models import AuditLog, AuditAction

    user_id = get_current_user_id()
    ip = get_current_ip()

    # Objetos novos (INSERT)
    for obj in session.new:
        if not isinstance(obj, AuditMixin):
            continue
        # Seta o created_by_id e updated_by_id automaticamente
        if user_id and not obj.created_by_id:
            obj.created_by_id = user_id
            obj.updated_by_id = user_id

        session.add(AuditLog(
            entity_type=obj.__class__.__name__,
            entity_id=obj.id,   # pode ser None antes do flush — ver nota abaixo
            action=AuditAction.CREATE,
            changes=None,       # CREATE não precisa de diff
            user_id=user_id,
            ip_address=ip,
        ))

    # Objetos modificados (UPDATE)
    for obj in session.dirty:
        if not isinstance(obj, AuditMixin):
            continue
        changes = _get_changes(obj)
        if not changes:
            continue

        # Atualiza o updated_by_id automaticamente
        if user_id:
            obj.updated_by_id = user_id

        session.add(AuditLog(
            entity_type=obj.__class__.__name__,
            entity_id=obj.id,
            action=AuditAction.UPDATE,
            changes=changes,
            user_id=user_id,
            ip_address=ip,
        ))

    # Objetos deletados (DELETE)
    for obj in session.deleted:
        if not isinstance(obj, AuditMixin):
            continue
        session.add(AuditLog(
            entity_type=obj.__class__.__name__,
            entity_id=obj.id,
            action=AuditAction.DELETE,
            changes=None,
            user_id=user_id,
            ip_address=ip,
        ))