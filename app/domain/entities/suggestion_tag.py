from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class SuggestionTag:
    """Entidad de dominio para la relación sugerencia-etiqueta."""

    suggestion_id: UUID
    tag_id: UUID
