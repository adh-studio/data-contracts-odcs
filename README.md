# Data Contracts ODCS, import et distribution a Madagascar

[![CI](https://github.com/adh-studio/data-contracts-odcs/actions/workflows/ci.yml/badge.svg)](https://github.com/adh-studio/data-contracts-odcs/actions/workflows/ci.yml)

Rapport de conformite en ligne : https://adh-studio.github.io/data-contracts-odcs/

Systeme de Data Contracts conforme a l'esprit de l'Open Data Contract Standard
(ODCS v3, projet Bitol de la Linux Foundation) pour trois flux critiques d'une
activite d'import et de distribution de produits electroniques a Madagascar :
consoles et gaming, audio, telephonie et accessoires, montres connectees,
eclairage LED et electromenager, avec des prix en ariary (MGA).

| Flux | Contenu | SLA fraicheur | SLA completude |
|---|---|---|---|
| `stocks_quotidiens` | photo quotidienne des stocks par produit et par depot (Ankorondrano, Analakely, Behoririka, Tamatave), publiee avant 7h | 24 h | 99 % |
| `lots_import` | lignes de lots d'import fournisseurs (Shenzhen, Guangzhou, Yiwu, Dongguan, Dubai), fret AIR 10 a 15 jours ou SEA 40 a 55 jours, rafraichies a J+1 | 48 h | 99 % |
| `referentiel_produits` | referentiel maitre du catalogue electronique, prix d'achat et de vente en MGA, revu chaque semaine | 7 jours | 100 % |

## Contexte metier

L'activite repose sur une chaine import complete : commande aupres des
fournisseurs asiatiques et de Dubai, fret aerien ou maritime, dedouanement a
Tamatave ou Ivato, puis distribution entre le depot central Ankorondrano, les
boutiques Analakely et Behoririka et le depot regional de Tamatave. Le data
contract est l'interface formelle entre les systemes producteurs (suivi des
imports, inventaires des depots, catalogue) et les consommateurs (prevision de
la demande, tableaux de bord ruptures, entrepot analytique). Il fixe par
ecrit :

- le schema et la semantique de chaque colonne ;
- les regles de gestion (formats de references, modes de fret et statuts autorises, ordre des dates, plages de valeurs en MGA, unicite) ;
- les SLA de fraicheur, de completude et de disponibilite ;
- le proprietaire du produit et les canaux de support.

Ce depot rend ces engagements executables : chaque contrat est verifie
automatiquement par un validateur, et toute violation casse la CI.

Il complete l'entrepot analytique
[supply-dbt-warehouse](https://github.com/adh-studio/supply-dbt-warehouse)
construit sur les memes flux : ces contrats, poses en amont de l'ingestion,
auraient empeche la derive de schema `stock_disponible` /
`quantite_disponible` rencontree dans cet entrepot, en bloquant le fichier non
conforme des la premiere livraison.

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
  --contrat contracts/lots_import.odcs.yaml \
  --schema-json schemas/lots_import.schema.json \
  --donnees data/casses/lots_import.csv
```

Le rapport liste chaque regle avec son statut OK ou KO, les lignes en echec et
le detail de la violation. L'option `--sortie-json` produit un rapport machine.

## Ce que ce projet demontre pour un role de Product Owner Data et IA

- **Data Contracts formels** : trois contrats ODCS v3 complets avec schema,
  semantique colonne par colonne, regles de gestion et criteres d'acceptation
  exprimes comme des regles de qualite executables.
- **SLA et SLO de data products** : fraicheur (stocks avant 7h, lots a J+1,
  referentiel hebdomadaire), completude, frequence et disponibilite declarees
  dans le contrat et verifiees par la machine, pas seulement promises dans un
  document.
- **Recette fonctionnelle automatisee** : le jeu de donnees volontairement
  casse joue le role de plan de recette ; les tests verifient que chaque
  violation attendue est bien detectee, ce qui valide le validateur lui-meme.
- **Posture Data Mesh** : contrat porte par un domaine (import-distribution),
  avec owner, steward et canaux de support identifies, pret a etre reference
  dans un catalogue de data products.
- **Industrialisation** : CI GitHub Actions, rapport de conformite publie sur
  GitHub Pages, outil en ligne de commande integrable dans n'importe quel
  pipeline.
