"""Wyjątki komunikacji ze sterownikiem."""


class EsterownikError(Exception):
    """Błąd bazowy."""


class AuthError(EsterownikError):
    """Sterownik odrzucił login lub hasło."""


class ConnectionFailed(EsterownikError):
    """Brak połączenia albo nieoczekiwana odpowiedź HTTP."""


class ParseError(EsterownikError):
    """Odpowiedź sterownika ma nieoczekiwany format."""


class WriteError(EsterownikError):
    """Sterownik nie przyjął zapisu."""
