"""Tests e2e du validateur : conformite des jeux propres et detection
exhaustive des violations introduites dans les jeux casses."""

import pytest

from validateur import valider_fichier
from validateur.cli import principal

FLUX = ["stocks_quotidiens", "commandes_fournisseurs", "referentiel_produits"]

# Chaque alteration de scripts/genere_donnees.py doit etre detectee par la
# regle correspondante. C'est le coeur de la recette fonctionnelle.
VIOLATIONS_ATTENDUES = {
    "stocks_quotidiens": {
        "stocks_quotidiens.sku.pattern",
        "stocks_quotidiens.quantite_disponible.plage",
        "stocks_quotidiens.type_site.valeurs_valides",
        "stocks_quotidiens.sla.fraicheur",
        "stocks_quotidiens.site_id.non_nul",
        "stocks_quotidiens.unicite_combinaison",
        "stocks_quotidiens.json_schema",
    },
    "commandes_fournisseurs": {
        "commandes_fournisseurs.statut.valeurs_valides",
        "commandes_fournisseurs.prix_unitaire_eur.plage",
        "commandes_fournisseurs.ordre_dates",
        "commandes_fournisseurs.fournisseur_id.non_nul",
        "commandes_fournisseurs.unicite_combinaison",
        "commandes_fournisseurs.sla.fraicheur",
        "commandes_fournisseurs.json_schema",
    },
    "referentiel_produits": {
        "referentiel_produits.famille.valeurs_valides",
        "referentiel_produits.prix_vente_eur.plage",
        "referentiel_produits.libelle.non_nul",
        "referentiel_produits.sku.unicite",
        "referentiel_produits.sla.fraicheur",
        "referentiel_produits.pays_origine.pattern",
        "referentiel_produits.sla.completude",
        "referentiel_produits.json_schema",
    },
}


def _valider(racine, dossier_donnees, flux, jeu, maintenant):
    return valider_fichier(
        racine / "contracts" / f"{flux}.odcs.yaml",
        racine / "schemas" / f"{flux}.schema.json",
        dossier_donnees / jeu / f"{flux}.csv",
        maintenant=maintenant,
    )


@pytest.mark.parametrize("flux", FLUX)
def test_jeu_conforme_sans_violation(racine, dossier_donnees, maintenant, flux):
    resultats = _valider(racine, dossier_donnees, flux, "conformes", maintenant)
    violations = [r.regle_id for r in resultats if not r.ok]
    assert violations == [], f"violations inattendues sur jeu conforme : {violations}"
    # Le moteur doit couvrir les 4 categories de regles
    categories = {r.categorie for r in resultats}
    assert categories == {"schema", "qualite", "sla", "json_schema"}


@pytest.mark.parametrize("flux", FLUX)
def test_jeu_casse_toutes_les_violations_detectees(racine, dossier_donnees,
                                                   maintenant, flux):
    resultats = _valider(racine, dossier_donnees, flux, "casses", maintenant)
    detectees = {r.regle_id for r in resultats if not r.ok}
    attendues = VIOLATIONS_ATTENDUES[flux]
    manquees = attendues - detectees
    assert not manquees, f"violations non detectees : {sorted(manquees)}"


@pytest.mark.parametrize("flux", FLUX)
def test_cli_code_sortie(racine, dossier_donnees, maintenant, flux, capsys):
    base = [
        "--contrat", str(racine / "contracts" / f"{flux}.odcs.yaml"),
        "--schema-json", str(racine / "schemas" / f"{flux}.schema.json"),
        "--maintenant", maintenant.isoformat(),
    ]
    code_ok = principal(base + ["--donnees",
                                str(dossier_donnees / "conformes" / f"{flux}.csv")])
    assert code_ok == 0
    code_ko = principal(base + ["--donnees",
                                str(dossier_donnees / "casses" / f"{flux}.csv")])
    assert code_ko == 1
    sortie = capsys.readouterr().out
    assert "violation(s)" in sortie


def test_cli_rapport_json(racine, dossier_donnees, maintenant, tmp_path):
    sortie = tmp_path / "rapport.json"
    principal([
        "--contrat", str(racine / "contracts" / "stocks_quotidiens.odcs.yaml"),
        "--schema-json", str(racine / "schemas" / "stocks_quotidiens.schema.json"),
        "--donnees", str(dossier_donnees / "conformes" / "stocks_quotidiens.csv"),
        "--maintenant", maintenant.isoformat(),
        "--sortie-json", str(sortie),
    ])
    import json
    rapport = json.loads(sortie.read_text(encoding="utf-8"))
    assert all(r["statut"] == "OK" for r in rapport)
    assert any(r["regle_id"] == "stocks_quotidiens.sla.fraicheur" for r in rapport)
