"""Blacklist de tokens para implementar logout (invalidación de tokens)."""


# En producción, esto debería ser Redis o similar para persistencia
# y compartir entre instancias de la aplicación
_token_blacklist: set[str] = set()


def add_token_to_blacklist(token: str) -> None:
    """
    Agrega un token a la blacklist para invalidarlo.
    
    Args:
        token: Token JWT a invalidar
    """
    _token_blacklist.add(token)


def is_token_blacklisted(token: str) -> bool:
    """
    Verifica si un token está en la blacklist.
    
    Args:
        token: Token JWT a verificar
    
    Returns:
        True si el token está blacklisted, False en caso contrario
    """
    return token in _token_blacklist


def clear_blacklist() -> None:
    """Limpia la blacklist (útil para testing)."""
    _token_blacklist.clear()


def get_blacklist_size() -> int:
    """Devuelve el tamaño actual de la blacklist."""
    return len(_token_blacklist)


# Nota para producción:
# Esta implementación en memoria no es adecuada para producción con múltiples instancias.
# Considere usar:
# 1. Redis con TTL igual al tiempo de expiración del token
# 2. Base de datos con limpieza periódica de tokens expirados
# 3. Sistema de sesiones con estado en caché distribuida
