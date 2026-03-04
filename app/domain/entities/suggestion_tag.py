from dataclasses import dataclass


@dataclass(slots=True)
class SuggestionTag:
    """Entidad de dominio para la relación sugerencia-etiqueta."""

    suggestion_id: int
    tag_id: int
