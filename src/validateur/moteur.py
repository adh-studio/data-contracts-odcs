"""Moteur de validation des data contracts ODCS.

Chaque verification produit un ResultatRegle avec un identifiant stable,
ce qui permet aux tests et au rapport HTML de cibler precisement chaque regle.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import Draft202012Validator


# ---------------------------------------------------------------------------
# Modele de resultat
# ---------------------------------------------------------------------------

@dataclass
class ResultatRegle:
    """Resultat de l'evaluation d'une regle du contrat."""

    regle_id: str
    categorie: str  # schema | qualite | sla | json_schema
    description: str
    statut: str  # OK | KO
    lignes_en_echec: int = 0
    details: str = ""

    @property
    def ok(self) -> bool:
        return self.statut == "OK"

    def to_dict(self) -> dict:
        return {
            "regle_id": self.regle_id,
            "categorie": self.categorie,
            "description": self.description,
            "statut": self.statut,
            "lignes_en_echec": self.lignes_en_echec,
            "details": self.details,
        }


@dataclass
class _Contexte:
    nom_jeu: str
    resultats: list[ResultatRegle] = field(default_factory=list)

    def ajouter(self, regle_id: str, categorie: str, description: str,
                indices_echec: list[int], details: str = "") -> None:
        nb = len(indices_echec)
        statut = "OK" if nb == 0 else "KO"
        extrait = ""
        if nb:
            apercu = ", ".join(str(i) for i in indices_echec[:5])
            extrait = f"lignes en echec (index 0-base) : {apercu}"
            if nb > 5:
                extrait += f" et {nb - 5} autres"
            if details:
                extrait = f"{details} ; {extrait}"
        self.resultats.append(ResultatRegle(
            regle_id=regle_id,
            categorie=categorie,
            description=description,
            statut=statut,
            lignes_en_echec=nb,
            details=extrait,
        ))


# ---------------------------------------------------------------------------
# Chargement
# ---------------------------------------------------------------------------

def charger_contrat(chemin: str | Path) -> dict:
    """Charge un contrat ODCS YAML et verifie sa structure minimale."""
    contrat = yaml.safe_load(Path(chemin).read_text(encoding="utf-8"))
    if contrat.get("kind") != "DataContract":
        raise ValueError(f"{chemin} : kind attendu 'DataContract', obtenu {contrat.get('kind')!r}")
    if not str(contrat.get("apiVersion", "")).startswith("v3"):
        raise ValueError(f"{chemin} : apiVersion ODCS v3 attendue")
    if not contrat.get("schema"):
        raise ValueError(f"{chemin} : section schema absente")
    return contrat


def charger_schema_json(chemin: str | Path) -> dict:
    schema = json.loads(Path(chemin).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


# ---------------------------------------------------------------------------
# Aides types
# ---------------------------------------------------------------------------

_MOTIF_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MOTIF_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")


def _est_nul(valeur) -> bool:
    if valeur is None:
        return True
    if isinstance(valeur, float) and math.isnan(valeur):
        return True
    if isinstance(valeur, str) and valeur.strip() == "":
        return True
    return False


def _valeur_conforme_au_type(valeur: str, type_logique: str) -> bool:
    if type_logique == "integer":
        try:
            return float(valeur) == int(float(valeur))
        except (TypeError, ValueError):
            return False
    if type_logique == "number":
        try:
            float(valeur)
            return True
        except (TypeError, ValueError):
            return False
    if type_logique == "date":
        return bool(_MOTIF_DATE.match(str(valeur)))
    if type_logique == "timestamp":
        return bool(_MOTIF_TIMESTAMP.match(str(valeur)))
    return isinstance(valeur, str)


def _convertir(valeur: str, type_logique: str):
    """Convertit une valeur texte vers le type natif attendu par JSON Schema."""
    if _est_nul(valeur):
        return None
    if type_logique == "integer":
        try:
            return int(float(valeur))
        except (TypeError, ValueError):
            return str(valeur)
    if type_logique == "number":
        try:
            return float(valeur)
        except (TypeError, ValueError):
            return str(valeur)
    return str(valeur)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def valider(df: pd.DataFrame, contrat: dict, schema_json: dict,
            maintenant: datetime | None = None) -> list[ResultatRegle]:
    """Valide un DataFrame (lu en texte brut) contre un contrat ODCS.

    Le DataFrame doit etre lu avec dtype=str pour que le moteur controle
    lui-meme les types logiques declares dans le contrat.
    """
    maintenant = maintenant or datetime.now()
    table = contrat["schema"][0]
    nom_table = table["name"]
    proprietes = table.get("properties", [])
    ctx = _Contexte(nom_jeu=nom_table)

    # 1. Schema : presence des colonnes -------------------------------------
    colonnes_attendues = [p["name"] for p in proprietes]
    manquantes = [c for c in colonnes_attendues if c not in df.columns]
    inconnues = [c for c in df.columns if c not in colonnes_attendues]
    ctx.ajouter(
        f"{nom_table}.schema.colonnes",
        "schema",
        "Toutes les colonnes declarees sont presentes, aucune colonne inconnue",
        list(range(1)) if (manquantes or inconnues) else [],
        details=f"manquantes={manquantes} inconnues={inconnues}" if (manquantes or inconnues) else "",
    )
    if manquantes:
        # Impossible d'aller plus loin de maniere fiable.
        return ctx.resultats

    # 2. Schema : non-nullite et types logiques ------------------------------
    for prop in proprietes:
        nom = prop["name"]
        serie = df[nom]
        if prop.get("required", False):
            indices_nuls = [i for i, v in enumerate(serie) if _est_nul(v)]
            ctx.ajouter(
                f"{nom_table}.{nom}.non_nul",
                "schema",
                f"Colonne {nom} : aucune valeur manquante (required)",
                indices_nuls,
            )
        type_logique = prop.get("logicalType", "string")
        indices_types = [
            i for i, v in enumerate(serie)
            if not _est_nul(v) and not _valeur_conforme_au_type(v, type_logique)
        ]
        ctx.ajouter(
            f"{nom_table}.{nom}.type",
            "schema",
            f"Colonne {nom} : valeurs conformes au type logique {type_logique}",
            indices_types,
        )

    # 3. Qualite : regles au niveau propriete ---------------------------------
    for prop in proprietes:
        nom = prop["name"]
        serie = df[nom]
        if prop.get("unique", False):
            dupliques = serie[~serie.apply(_est_nul)].duplicated(keep=False)
            indices = list(serie.index[dupliques])
            ctx.ajouter(
                f"{nom_table}.{nom}.unicite",
                "qualite",
                f"Colonne {nom} : valeurs uniques (cle primaire)",
                indices,
            )
        for regle in prop.get("quality", []) or []:
            _appliquer_regle_propriete(ctx, nom_table, nom, serie, regle)

    # 4. Qualite : regles au niveau table -------------------------------------
    for regle in table.get("quality", []) or []:
        _appliquer_regle_table(ctx, nom_table, df, regle)

    # 5. SLA : fraicheur et completude ----------------------------------------
    for sla in contrat.get("slaProperties", []) or []:
        propriete = sla.get("property")
        if propriete == "freshness":
            _verifier_fraicheur(ctx, nom_table, df, sla, maintenant)
        elif propriete == "completeness":
            _verifier_completude(ctx, nom_table, df, sla)

    # 6. JSON Schema : validation technique ligne a ligne ---------------------
    types_logiques = {p["name"]: p.get("logicalType", "string") for p in proprietes}
    validateur = Draft202012Validator(schema_json)
    indices_js: list[int] = []
    premier_message = ""
    for i, ligne in enumerate(df.to_dict(orient="records")):
        enregistrement = {
            cle: _convertir(valeur, types_logiques.get(cle, "string"))
            for cle, valeur in ligne.items()
        }
        enregistrement = {k: v for k, v in enregistrement.items() if v is not None}
        erreurs = list(validateur.iter_errors(enregistrement))
        if erreurs:
            indices_js.append(i)
            if not premier_message:
                premier_message = erreurs[0].message[:160]
    ctx.ajouter(
        f"{nom_table}.json_schema",
        "json_schema",
        "Chaque ligne est valide contre le JSON Schema du contrat",
        indices_js,
        details=f"premiere erreur : {premier_message}" if premier_message else "",
    )

    return ctx.resultats


def _appliquer_regle_propriete(ctx: _Contexte, nom_table: str, nom: str,
                               serie: pd.Series, regle: dict) -> None:
    nom_regle = regle.get("rule")
    description = regle.get("description", nom_regle or "regle")
    if nom_regle == "pattern":
        motif = re.compile(regle["pattern"])
        indices = [i for i, v in enumerate(serie)
                   if not _est_nul(v) and not motif.match(str(v))]
        ctx.ajouter(f"{nom_table}.{nom}.pattern", "qualite",
                    f"Colonne {nom} : {description}", indices)
    elif nom_regle == "validValues":
        autorisees = set(regle["validValues"])
        indices = [i for i, v in enumerate(serie)
                   if not _est_nul(v) and str(v) not in autorisees]
        ctx.ajouter(f"{nom_table}.{nom}.valeurs_valides", "qualite",
                    f"Colonne {nom} : {description}", indices)
    elif nom_regle == "range":
        borne_min = regle.get("mustBeGreaterOrEqualTo")
        borne_max = regle.get("mustBeLessOrEqualTo")
        indices = []
        for i, v in enumerate(serie):
            if _est_nul(v):
                continue
            try:
                x = float(v)
            except (TypeError, ValueError):
                indices.append(i)
                continue
            if borne_min is not None and x < float(borne_min):
                indices.append(i)
            elif borne_max is not None and x > float(borne_max):
                indices.append(i)
        ctx.ajouter(f"{nom_table}.{nom}.plage", "qualite",
                    f"Colonne {nom} : {description}", indices)


def _appliquer_regle_table(ctx: _Contexte, nom_table: str,
                           df: pd.DataFrame, regle: dict) -> None:
    nom_regle = regle.get("rule")
    description = regle.get("description", nom_regle or "regle")
    if nom_regle == "uniqueCombination":
        colonnes = regle["columns"]
        dupliques = df.duplicated(subset=colonnes, keep=False)
        indices = list(df.index[dupliques])
        ctx.ajouter(f"{nom_table}.unicite_combinaison", "qualite",
                    description, indices,
                    details=f"colonnes : {', '.join(colonnes)}" if indices else "")
    elif nom_regle == "ordreDates":
        props = {p["property"]: p["value"]
                 for p in regle.get("customProperties", []) or []}
        col_debut, col_fin = props["colonneDebut"], props["colonneFin"]
        debut = pd.to_datetime(df[col_debut], errors="coerce")
        fin = pd.to_datetime(df[col_fin], errors="coerce")
        masque = debut.notna() & fin.notna() & (fin < debut)
        indices = list(df.index[masque])
        ctx.ajouter(f"{nom_table}.ordre_dates", "qualite",
                    description, indices,
                    details=f"{col_fin} < {col_debut}" if indices else "")


def _verifier_fraicheur(ctx: _Contexte, nom_table: str, df: pd.DataFrame,
                        sla: dict, maintenant: datetime) -> None:
    element = sla.get("element", "")
    colonne = element.split(".")[-1]
    seuil_heures = float(sla["value"])
    if sla.get("unit") == "d":
        seuil_heures *= 24
    if colonne not in df.columns:
        ctx.ajouter(f"{nom_table}.sla.fraicheur", "sla",
                    sla.get("description", "Fraicheur"), [0],
                    details=f"colonne {colonne} absente")
        return
    horodatages = pd.to_datetime(df[colonne], errors="coerce")
    ages_heures = (maintenant - horodatages).dt.total_seconds() / 3600.0
    masque = horodatages.isna() | (ages_heures > seuil_heures) | (ages_heures < -1)
    indices = list(df.index[masque])
    pire = ages_heures.max()
    ctx.ajouter(
        f"{nom_table}.sla.fraicheur", "sla",
        f"Fraicheur : {colonne} plus recent que {seuil_heures:g} h "
        f"(SLA : {sla.get('description', '')})".strip(),
        indices,
        details=f"age maximal observe : {pire:.1f} h pour un seuil de {seuil_heures:g} h"
        if indices else "",
    )


def _verifier_completude(ctx: _Contexte, nom_table: str,
                         df: pd.DataFrame, sla: dict) -> None:
    seuil = float(sla["value"])
    total = df.shape[0] * df.shape[1]
    if total == 0:
        ctx.ajouter(f"{nom_table}.sla.completude", "sla",
                    "Completude : jeu de donnees vide", [0])
        return
    nb_nuls = int(df.map(_est_nul).to_numpy().sum())
    taux = 100.0 * (total - nb_nuls) / total
    conforme = taux >= seuil
    ctx.ajouter(
        f"{nom_table}.sla.completude", "sla",
        f"Completude : taux de cellules renseignees >= {seuil:g} %",
        [] if conforme else [0],
        details="" if conforme else f"taux observe : {taux:.2f} % ({nb_nuls} cellule(s) vide(s))",
    )


# ---------------------------------------------------------------------------
# Point d'entree fichier
# ---------------------------------------------------------------------------

def valider_fichier(chemin_contrat: str | Path, chemin_schema_json: str | Path,
                    chemin_csv: str | Path,
                    maintenant: datetime | None = None) -> list[ResultatRegle]:
    contrat = charger_contrat(chemin_contrat)
    schema_json = charger_schema_json(chemin_schema_json)
    df = pd.read_csv(chemin_csv, dtype=str, keep_default_na=False)
    df = df.replace({"": None})
    return valider(df, contrat, schema_json, maintenant=maintenant)
