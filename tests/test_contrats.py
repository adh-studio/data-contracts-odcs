"""Tests de structure des contrats ODCS et de leurs equivalents JSON Schema."""

import pytest

from validateur import charger_contrat, charger_schema_json

FLUX = ["stocks_quotidiens", "lots_import", "referentiel_produits"]


@pytest.mark.parametrize("flux", FLUX)
def test_contrat_structure_odcs(racine, flux):
    contrat = charger_contrat(racine / "contracts" / f"{flux}.odcs.yaml")
    assert contrat["kind"] == "DataContract"
    assert contrat["apiVersion"].startswith("v3")
    assert contrat["domain"] == "import-distribution"
    assert contrat["tenant"] == "import-distribution-madagascar"
    assert contrat["status"] == "active"
    assert contrat["id"].startswith("urn:datacontract:import-distribution:")
    # Semantique : chaque colonne est decrite
    for prop in contrat["schema"][0]["properties"]:
        assert prop.get("description"), f"{flux}.{prop['name']} sans description"
        assert prop.get("logicalType"), f"{flux}.{prop['name']} sans logicalType"


@pytest.mark.parametrize("flux", FLUX)
def test_contrat_sla_fraicheur_et_completude(racine, flux):
    contrat = charger_contrat(racine / "contracts" / f"{flux}.odcs.yaml")
    proprietes_sla = {s["property"] for s in contrat["slaProperties"]}
    assert {"freshness", "completeness", "frequency", "availability"} <= proprietes_sla


@pytest.mark.parametrize("flux", FLUX)
def test_contrat_possede_owner_et_support(racine, flux):
    contrat = charger_contrat(racine / "contracts" / f"{flux}.odcs.yaml")
    roles = {m["role"] for m in contrat["team"]}
    assert "owner" in roles
    outils = {s["tool"] for s in contrat["support"]}
    assert {"slack", "email"} <= outils


@pytest.mark.parametrize("flux", FLUX)
def test_schema_json_valide_et_aligne(racine, flux):
    contrat = charger_contrat(racine / "contracts" / f"{flux}.odcs.yaml")
    schema = charger_schema_json(racine / "schemas" / f"{flux}.schema.json")
    colonnes_contrat = {p["name"] for p in contrat["schema"][0]["properties"]}
    assert set(schema["properties"].keys()) == colonnes_contrat
    requis_contrat = {p["name"] for p in contrat["schema"][0]["properties"]
                      if p.get("required")}
    assert set(schema["required"]) == requis_contrat
