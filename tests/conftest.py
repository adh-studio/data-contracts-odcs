import sys
from datetime import datetime
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from genere_donnees import generer_tout  # noqa: E402


@pytest.fixture(scope="session")
def racine() -> Path:
    return RACINE


@pytest.fixture(scope="session")
def maintenant() -> datetime:
    return datetime.now()


@pytest.fixture(scope="session")
def dossier_donnees(tmp_path_factory, maintenant) -> Path:
    """Regenere les jeux de donnees dans un dossier temporaire.

    Les horodatages sont relatifs a l'instant du test, ce qui rend les
    verifications de fraicheur deterministes.
    """
    dossier = tmp_path_factory.mktemp("donnees")
    generer_tout(dossier, maintenant=maintenant)
    return dossier
