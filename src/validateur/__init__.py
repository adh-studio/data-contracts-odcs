"""Validateur de Data Contracts conformes a l'esprit de l'ODCS v3 (Bitol).

Valide un fichier de donnees (CSV) contre :
- le schema declare dans le contrat YAML (colonnes, types logiques, non-nullite) ;
- les regles de qualite (pattern, validValues, range, unicite, ordre de dates) ;
- les SLA (fraicheur relative a un instant de reference, completude) ;
- l'equivalent JSON Schema pour la validation technique ligne a ligne.
"""

from .moteur import (
    ResultatRegle,
    charger_contrat,
    charger_schema_json,
    valider,
    valider_fichier,
)

__all__ = [
    "ResultatRegle",
    "charger_contrat",
    "charger_schema_json",
    "valider",
    "valider_fichier",
]

__version__ = "1.0.0"
