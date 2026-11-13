# Data Contracts ODCS, domaine Offre et Supply

[![CI](https://github.com/adh-studio/data-contracts-odcs/actions/workflows/ci.yml/badge.svg)](https://github.com/adh-studio/data-contracts-odcs/actions/workflows/ci.yml)

Rapport de conformite en ligne : https://adh-studio.github.io/data-contracts-odcs/

Systeme de Data Contracts conforme a l'esprit de l'Open Data Contract Standard
(ODCS v3, projet Bitol de la Linux Foundation) pour trois flux critiques du
domaine Offre et Supply d'une enseigne de decoration et d'ameublement :

| Flux | Contenu | SLA fraicheur | SLA completude |
|---|---|---|---|
| `stocks_quotidiens` | photo quotidienne des stocks par produit et par site (magasins, entrepots) | 24 h | 99 % |
| `commandes_fournisseurs` | lignes de commandes d'achat (canapes, luminaires, vaisselle, tapis, rangement) | 48 h | 99 % |
| `referentiel_produits` | referentiel maitre des produits du catalogue | 7 jours | 100 % |

## Contexte metier

Dans une organisation Data Mesh, chaque domaine publie ses donnees comme des
produits. Le data contract est l'interface formelle entre le domaine producteur
(supply, achats, referentiels) et les consommateurs (prevision de la demande,
tableaux de bord ruptures, e-commerce). Il fixe par ecrit :

- le schema et la semantique de chaque colonne ;
- les regles de gestion (formats de references, statuts autorises, plages de valeurs, unicite) ;
- les SLA de fraicheur, de completude et de disponibilite ;
- le proprietaire du produit et les canaux de support.

Ce depot rend ces engagements executables : chaque contrat est verifie
automatiquement par un validateur, et toute violation casse la CI.

## Architecture

```
contracts/     3 contrats YAML fideles a la structure ODCS v3
               (apiVersion, kind: DataContract, schema, quality, slaProperties,
                support, team, customProperties)
schemas/       equivalents JSON Schema (draft 2020-12) pour la validation technique
src/validateur moteur Python : schema, types logiques, regles qualite,
               fraicheur relative, completude, JSON Schema ligne a ligne
scripts/       generateur de donnees synthetiques + generateur du rapport HTML
data/          jeu conforme et jeu volontairement casse pour chaque flux
tests/         22 tests pytest : structure des contrats, zero violation sur les
               jeux conformes, detection exhaustive des violations introduites
docs/          rapport de conformite HTML publie sur GitHub Pages
```

Le validateur evalue quatre categories de regles et retourne un code de sortie
non nul des qu'une regle est violee, ce qui le rend directement utilisable dans
un pipeline d'orchestration (Airflow, dbt, n8n) ou en CI.

## Installation

Prerequis : Python 3.11, 3.12 ou 3.13 (versions validees pour les dependances
epinglees, notamment pandas 2.2.3).

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Rejouer les tests

```bash
./run_e2e.sh
```

Ou manuellement :

```bash
python scripts/genere_donnees.py
PYTHONPATH=src python -m pytest tests/ -v
```

## Valider un fichier a la main

```bash
PYTHONPATH=src python -m validateur \
  --contrat contracts/stocks_quotidiens.odcs.yaml \
  --schema-json schemas/stocks_quotidiens.schema.json \
  --donnees data/casses/stocks_quotidiens.csv
```

Le rapport liste chaque regle avec son statut OK ou KO, les lignes en echec et
le detail de la violation. L'option `--sortie-json` produit un rapport machine.

## Ce que ce projet demontre pour un role de Product Owner Data et IA

- **Data Contracts formels** : trois contrats ODCS v3 complets avec schema,
  semantique colonne par colonne, regles de gestion et criteres d'acceptation
  exprimes comme des regles de qualite executables.
- **SLA et SLO de data products** : fraicheur, completude, frequence et
  disponibilite declarees dans le contrat et verifiees par la machine, pas
  seulement promises dans un document.
- **Recette fonctionnelle automatisee** : le jeu de donnees volontairement
  casse joue le role de plan de recette ; les tests verifient que chaque
  violation attendue est bien detectee, ce qui valide le validateur lui-meme.
- **Posture Data Mesh** : contrat porte par un domaine (Offre et Supply), avec
  owner, steward et canaux de support identifies, pret a etre reference dans un
  catalogue de data products.
- **Industrialisation** : CI GitHub Actions, rapport de conformite publie sur
  GitHub Pages, outil en ligne de commande integrable dans n'importe quel
  pipeline.
