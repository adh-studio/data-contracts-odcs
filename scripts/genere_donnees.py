"""Genere les jeux de donnees synthetiques, conformes et volontairement casses.

Univers : enseigne de decoration et d'ameublement (canapes, luminaires,
vaisselle, tapis, rangement), magasins et entrepots en France.

Les horodatages sont calcules relativement a l'instant d'execution pour que
les SLA de fraicheur restent verifiables a tout moment. Le reste du contenu
est deterministe (graine fixe).

Usage : python scripts/genere_donnees.py [dossier_cible]
"""

from __future__ import annotations

import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

GRAINE = 20260113
RACINE = Path(__file__).resolve().parent.parent

FAMILLES = {
    "CAN": ("canapes", [
        "Canape 3 places Oslo tissu chine", "Canape d'angle Bergen velours",
        "Canape convertible Porto", "Canape 2 places Milan cuir",
    ]),
    "LUM": ("luminaires", [
        "Suspension rotin Bali", "Lampadaire arque laiton Elio",
        "Lampe a poser ceramique Sora", "Applique murale noire Pia",
    ]),
    "VAI": ("vaisselle", [
        "Assiette gres reactive Kyo lot de 4", "Mug emaille Fjord",
        "Saladier bambou Luna", "Service a the Hanoi 12 pieces",
    ]),
    "TAP": ("tapis", [
        "Tapis berbere Atlas 160x230", "Tapis jute naturel Goa rond",
        "Tapis shaggy Nuage gris", "Tapis d'exterieur Patio raye",
    ]),
    "RAN": ("rangement", [
        "Etagere echelle chene Lund", "Buffet cannage Saigon",
        "Panier osier Mimosa", "Colonne de rangement Brick",
    ]),
}
PAYS = ["FR", "PT", "VN", "IN", "PL", "IT"]
SITES = [("MAG-001", "magasin"), ("MAG-014", "magasin"), ("MAG-027", "magasin"),
         ("ENT-901", "entrepot"), ("ENT-902", "entrepot")]
FOURNISSEURS = ["FRN-1001", "FRN-1002", "FRN-2040", "FRN-3310"]
STATUTS = ["confirmee", "expediee", "recue", "brouillon"]


def _ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _skus(alea: random.Random) -> list[str]:
    skus = []
    for prefixe in FAMILLES:
        for _ in range(4):
            skus.append(f"{prefixe}-{alea.randint(10000, 99999)}")
    return sorted(set(skus))


def _ecrire(chemin: Path, entetes: list[str], lignes: list[list]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(entetes)
        ecrivain.writerows(lignes)


# ---------------------------------------------------------------------------
# Jeux conformes
# ---------------------------------------------------------------------------

def genere_stocks(skus: list[str], alea: random.Random, maintenant: datetime) -> list[list]:
    date_stock = maintenant.strftime("%Y-%m-%d")
    lignes = []
    for sku in skus:
        for site_id, type_site in SITES:
            maj = maintenant - timedelta(hours=alea.uniform(1, 6))
            lignes.append([
                date_stock, sku, site_id, type_site,
                alea.randint(0, 420), alea.randint(0, 35), _ts(maj),
            ])
    return lignes


def genere_commandes(skus: list[str], alea: random.Random, maintenant: datetime) -> list[list]:
    lignes = []
    for i in range(40):
        commande_id = f"CF-{maintenant.year}-{100000 + i}"
        sku = alea.choice(skus)
        date_commande = maintenant - timedelta(days=alea.randint(2, 30))
        date_livraison = date_commande + timedelta(days=alea.randint(7, 60))
        maj = maintenant - timedelta(hours=alea.uniform(2, 24))
        lignes.append([
            commande_id, alea.choice(FOURNISSEURS), sku,
            alea.randint(10, 800), round(alea.uniform(4.5, 890.0), 2),
            date_commande.strftime("%Y-%m-%d"), date_livraison.strftime("%Y-%m-%d"),
            alea.choice(STATUTS), _ts(maj),
        ])
    return lignes


def genere_referentiel(skus: list[str], alea: random.Random, maintenant: datetime) -> list[list]:
    lignes = []
    for sku in skus:
        prefixe = sku.split("-")[0]
        famille, libelles = FAMILLES[prefixe]
        prix = round(alea.uniform(9.9, 1890.0), 2)
        eco = round(prix * 0.01, 2) if famille in ("canapes", "rangement") else 0.0
        maj = maintenant - timedelta(hours=alea.uniform(6, 96))
        lignes.append([
            sku, alea.choice(libelles), famille, prix, min(eco, 200.0),
            alea.choice(PAYS), round(alea.uniform(0.2, 85.0), 2), _ts(maj),
        ])
    return lignes


# ---------------------------------------------------------------------------
# Jeux casses : chaque alteration correspond a une regle precise du contrat
# ---------------------------------------------------------------------------

def casse_stocks(lignes: list[list], maintenant: datetime) -> list[list]:
    lignes = [list(l) for l in lignes[:12]]
    lignes[0][1] = "XXX-99"                                   # pattern sku KO
    lignes[1][4] = -5                                         # plage quantite_disponible KO
    lignes[2][3] = "drive"                                    # validValues type_site KO
    lignes[3][6] = _ts(maintenant - timedelta(hours=72))      # fraicheur 24 h KO
    lignes[4][2] = ""                                         # non_nul site_id KO
    lignes[5] = list(lignes[6])                               # doublon date+sku+site KO
    return lignes


def casse_commandes(lignes: list[list], maintenant: datetime) -> list[list]:
    lignes = [list(l) for l in lignes[:12]]
    lignes[0][7] = "perdue"                                   # validValues statut KO
    lignes[1][4] = -12.5                                      # plage prix_unitaire_eur KO
    lignes[2][6] = (datetime.strptime(lignes[2][5], "%Y-%m-%d")
                    - timedelta(days=3)).strftime("%Y-%m-%d")  # ordreDates KO
    lignes[3][1] = ""                                         # non_nul fournisseur_id KO
    lignes[4][0] = lignes[5][0]
    lignes[4][2] = lignes[5][2]                               # doublon commande+sku KO
    lignes[6][8] = _ts(maintenant - timedelta(hours=120))     # fraicheur 48 h KO
    return lignes


def casse_referentiel(lignes: list[list], maintenant: datetime) -> list[list]:
    lignes = [list(l) for l in lignes[:12]]
    lignes[0][2] = "jardinage"                                # validValues famille KO
    lignes[1][3] = -10.0                                      # plage prix_vente_eur KO
    lignes[2][1] = ""                                         # non_nul libelle KO (completude 100 % KO)
    lignes[3][0] = lignes[4][0]                               # unicite sku KO
    lignes[5][7] = _ts(maintenant - timedelta(days=30))       # fraicheur 168 h KO
    lignes[6][5] = "France"                                   # pattern pays_origine KO
    return lignes


# ---------------------------------------------------------------------------

ENTETES = {
    "stocks_quotidiens": ["date_stock", "sku", "site_id", "type_site",
                          "quantite_disponible", "quantite_reservee", "horodatage_maj"],
    "commandes_fournisseurs": ["commande_id", "fournisseur_id", "sku",
                               "quantite_commandee", "prix_unitaire_eur",
                               "date_commande", "date_livraison_prevue",
                               "statut", "horodatage_maj"],
    "referentiel_produits": ["sku", "libelle", "famille", "prix_vente_eur",
                             "eco_participation_eur", "pays_origine",
                             "poids_kg", "date_maj"],
}


def generer_tout(dossier: Path, maintenant: datetime | None = None) -> dict[str, Path]:
    maintenant = maintenant or datetime.now()
    alea = random.Random(GRAINE)
    skus = _skus(alea)

    conformes = {
        "stocks_quotidiens": genere_stocks(skus, alea, maintenant),
        "commandes_fournisseurs": genere_commandes(skus, alea, maintenant),
        "referentiel_produits": genere_referentiel(skus, alea, maintenant),
    }
    casses = {
        "stocks_quotidiens": casse_stocks(conformes["stocks_quotidiens"], maintenant),
        "commandes_fournisseurs": casse_commandes(conformes["commandes_fournisseurs"], maintenant),
        "referentiel_produits": casse_referentiel(conformes["referentiel_produits"], maintenant),
    }

    chemins = {}
    for nom, lignes in conformes.items():
        chemin = dossier / "conformes" / f"{nom}.csv"
        _ecrire(chemin, ENTETES[nom], lignes)
        chemins[f"conformes/{nom}"] = chemin
    for nom, lignes in casses.items():
        chemin = dossier / "casses" / f"{nom}.csv"
        _ecrire(chemin, ENTETES[nom], lignes)
        chemins[f"casses/{nom}"] = chemin
    return chemins


if __name__ == "__main__":
    cible = Path(sys.argv[1]) if len(sys.argv) > 1 else RACINE / "data"
    chemins = generer_tout(cible)
    for cle, chemin in sorted(chemins.items()):
        print(f"genere : {chemin}")
