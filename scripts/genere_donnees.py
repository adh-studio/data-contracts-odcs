"""Genere les jeux de donnees synthetiques, conformes et volontairement casses.

Univers : import et distribution de produits electroniques a Madagascar
(consoles et gaming, audio, telephonie, montres connectees, eclairage LED,
electromenager), fournisseurs de Shenzhen, Guangzhou, Yiwu, Dongguan et Dubai,
depots Ankorondrano, Analakely, Behoririka et Tamatave. Prix en ariary (MGA).

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
    "CON": ("consoles_gaming", [
        "Console PS5 Slim 1To", "Console PS5 Digital",
        "Manette DualSense blanche", "Manette Xbox sans fil",
    ]),
    "AUD": ("audio", [
        "Ecouteurs TWS Pro reduction de bruit", "Enceinte Bluetooth etanche",
        "Casque gaming filaire", "Barre de son 2.1",
    ]),
    "TEL": ("telephonie_accessoires", [
        "Smartphone 128 Go double SIM", "Powerbank 20000 mAh",
        "Chargeur rapide 65W GaN", "Coque renforcee universelle",
    ]),
    "MON": ("montres_connectees", [
        "Montre connectee AMOLED", "Bracelet connecte sport",
        "Montre GPS running", "Montre enfant avec carte SIM",
    ]),
    "LED": ("eclairage_led", [
        "Ruban LED RGB 5 metres", "Ampoule LED connectee E27",
        "Projecteur LED solaire 100W", "Lampe de bureau LED tactile",
    ]),
    "ELM": ("electromenager", [
        "Bouilloire electrique inox", "Blender 1.5 litre",
        "Fer a repasser vapeur", "Ventilateur sur pied",
    ]),
}
DEPOTS = [("DEP-001", "central"), ("DEP-002", "boutique"),
          ("DEP-003", "boutique"), ("DEP-004", "depot_regional")]
# Fournisseurs et mode de fret contractuel, calques sur le referentiel achats
# (Shenzhen, Guangzhou, Huaqiangbei, Yiwu, Dongguan, Dubai).
FOURNISSEURS = [("FRN-0001", "AIR"), ("FRN-0002", "AIR"), ("FRN-0003", "AIR"),
                ("FRN-0004", "SEA"), ("FRN-0005", "SEA"), ("FRN-0006", "SEA"),
                ("FRN-0007", "AIR"), ("FRN-0008", "AIR")]
DELAIS_FRET = {"AIR": (10, 15), "SEA": (40, 55)}
STATUTS = ["commande", "embarque", "en_transit", "dedouane", "receptionne"]


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
        for depot_id, type_depot in DEPOTS:
            maj = maintenant - timedelta(hours=alea.uniform(1, 6))
            lignes.append([
                date_stock, sku, depot_id, type_depot,
                alea.randint(0, 420), alea.randint(0, 35), _ts(maj),
            ])
    return lignes


def genere_lots(skus: list[str], alea: random.Random, maintenant: datetime) -> list[list]:
    lignes = []
    for i in range(40):
        lot_id = f"LOT-{maintenant.year}-{100000 + i}"
        sku = alea.choice(skus)
        fournisseur_id, mode_fret = alea.choice(FOURNISSEURS)
        delai_min, delai_max = DELAIS_FRET[mode_fret]
        date_commande = maintenant - timedelta(days=alea.randint(2, 60))
        date_arrivee = date_commande + timedelta(days=alea.randint(delai_min, delai_max))
        maj = maintenant - timedelta(hours=alea.uniform(2, 24))
        prix_unitaire = alea.randint(30, 3000) * 1000  # 30 000 a 3 000 000 MGA
        lignes.append([
            lot_id, fournisseur_id, sku,
            alea.randint(5, 500), prix_unitaire, mode_fret,
            date_commande.strftime("%Y-%m-%d"), date_arrivee.strftime("%Y-%m-%d"),
            alea.choice(STATUTS), _ts(maj),
        ])
    return lignes


def genere_referentiel(skus: list[str], alea: random.Random, maintenant: datetime) -> list[list]:
    lignes = []
    for sku in skus:
        prefixe = sku.split("-")[0]
        famille, noms = FAMILLES[prefixe]
        prix_vente = alea.randint(50, 3500) * 1000  # 50 000 a 3 500 000 MGA
        prix_achat = max(1000, int(prix_vente * alea.uniform(0.6, 0.8)) // 1000 * 1000)
        fournisseur_id, _ = alea.choice(FOURNISSEURS)
        maj = maintenant - timedelta(hours=alea.uniform(6, 96))
        lignes.append([
            sku, alea.choice(noms), famille, prix_achat, prix_vente,
            fournisseur_id, _ts(maj),
        ])
    return lignes


# ---------------------------------------------------------------------------
# Jeux casses : chaque alteration correspond a une regle precise du contrat
# ---------------------------------------------------------------------------

def casse_stocks(lignes: list[list], maintenant: datetime) -> list[list]:
    lignes = [list(l) for l in lignes[:12]]
    lignes[0][1] = "XXX-99"                                   # pattern sku KO
    lignes[1][4] = -5                                         # plage quantite_disponible KO
    lignes[2][3] = "conteneur"                                # validValues type_depot KO
    lignes[3][6] = _ts(maintenant - timedelta(hours=72))      # fraicheur 24 h KO
    lignes[4][2] = ""                                         # non_nul depot_id KO
    lignes[5] = list(lignes[6])                               # doublon date+sku+depot KO
    return lignes


def casse_lots(lignes: list[list], maintenant: datetime) -> list[list]:
    lignes = [list(l) for l in lignes[:12]]
    lignes[0][8] = "perdu"                                    # validValues statut KO
    lignes[1][4] = -12500                                     # plage prix_unitaire_mga KO
    lignes[2][7] = (datetime.strptime(lignes[2][6], "%Y-%m-%d")
                    - timedelta(days=3)).strftime("%Y-%m-%d")  # ordreDates KO
    lignes[3][1] = ""                                         # non_nul fournisseur_id KO
    lignes[4][0] = lignes[5][0]
    lignes[4][2] = lignes[5][2]                               # doublon lot+sku KO
    lignes[6][9] = _ts(maintenant - timedelta(hours=120))     # fraicheur 48 h KO
    lignes[7][5] = "ROUTE"                                    # validValues mode_fret KO
    return lignes


def casse_referentiel(lignes: list[list], maintenant: datetime) -> list[list]:
    lignes = [list(l) for l in lignes[:12]]
    lignes[0][2] = "jardinage"                                # validValues famille KO
    lignes[1][4] = -10000                                     # plage prix_vente_mga KO
    lignes[2][1] = ""                                         # non_nul nom KO (completude 100 % KO)
    lignes[3][0] = lignes[4][0]                               # unicite sku KO
    lignes[5][6] = _ts(maintenant - timedelta(days=30))       # fraicheur 168 h KO
    lignes[6][5] = "Shenzhen"                                 # pattern fournisseur_id KO
    return lignes


# ---------------------------------------------------------------------------

ENTETES = {
    "stocks_quotidiens": ["date_stock", "sku", "depot_id", "type_depot",
                          "quantite_disponible", "quantite_reservee", "horodatage_maj"],
    "lots_import": ["lot_id", "fournisseur_id", "sku",
                    "quantite_commandee", "prix_unitaire_mga", "mode_fret",
                    "date_commande", "date_arrivee_prevue",
                    "statut", "horodatage_maj"],
    "referentiel_produits": ["sku", "nom", "famille", "prix_achat_mga",
                             "prix_vente_mga", "fournisseur_id", "date_maj"],
}


def generer_tout(dossier: Path, maintenant: datetime | None = None) -> dict[str, Path]:
    maintenant = maintenant or datetime.now()
    alea = random.Random(GRAINE)
    skus = _skus(alea)

    conformes = {
        "stocks_quotidiens": genere_stocks(skus, alea, maintenant),
        "lots_import": genere_lots(skus, alea, maintenant),
        "referentiel_produits": genere_referentiel(skus, alea, maintenant),
    }
    casses = {
        "stocks_quotidiens": casse_stocks(conformes["stocks_quotidiens"], maintenant),
        "lots_import": casse_lots(conformes["lots_import"], maintenant),
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
