"""Interface en ligne de commande du validateur de data contracts.

Exemple :
    python -m validateur \
        --contrat contracts/stocks_quotidiens.odcs.yaml \
        --schema-json schemas/stocks_quotidiens.schema.json \
        --donnees data/conformes/stocks_quotidiens.csv

Code de sortie : 0 si toutes les regles sont OK, 1 sinon.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .moteur import valider_fichier


def principal(argv: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(
        prog="validateur",
        description="Valide un fichier CSV contre un data contract ODCS v3.",
    )
    parseur.add_argument("--contrat", required=True, help="Chemin du contrat YAML ODCS")
    parseur.add_argument("--schema-json", required=True, help="Chemin du JSON Schema equivalent")
    parseur.add_argument("--donnees", required=True, help="Chemin du fichier CSV a valider")
    parseur.add_argument("--maintenant", default=None,
                         help="Instant de reference ISO 8601 pour la fraicheur (defaut : horloge systeme)")
    parseur.add_argument("--sortie-json", default=None,
                         help="Chemin optionnel d'un rapport JSON")
    args = parseur.parse_args(argv)

    maintenant = datetime.fromisoformat(args.maintenant) if args.maintenant else None
    resultats = valider_fichier(args.contrat, args.schema_json, args.donnees,
                                maintenant=maintenant)

    largeur = max(len(r.regle_id) for r in resultats)
    print(f"Validation de {args.donnees} contre {args.contrat}")
    print("-" * (largeur + 40))
    for r in resultats:
        pastille = "OK" if r.ok else "KO"
        ligne = f"[{pastille}] {r.regle_id.ljust(largeur)}  {r.description}"
        if not r.ok:
            ligne += f"  ({r.lignes_en_echec} ligne(s) ; {r.details})"
        print(ligne)

    nb_ko = sum(1 for r in resultats if not r.ok)
    print("-" * (largeur + 40))
    print(f"{len(resultats)} regle(s) evaluee(s), {nb_ko} violation(s).")

    if args.sortie_json:
        Path(args.sortie_json).write_text(
            json.dumps([r.to_dict() for r in resultats], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return 0 if nb_ko == 0 else 1


if __name__ == "__main__":
    sys.exit(principal())
