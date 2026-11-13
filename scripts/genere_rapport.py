"""Genere le rapport HTML de conformite dans docs/index.html.

Pour chaque contrat, le validateur est execute sur le jeu conforme et sur le
jeu volontairement casse. Le rapport affiche chaque regle en vert (OK) ou en
rouge (KO). Concu pour GitHub Pages, chemins relatifs, aucune dependance
externe.

Usage : python scripts/genere_rapport.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from html import escape
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from validateur import valider_fichier  # noqa: E402

FLUX = ["stocks_quotidiens", "commandes_fournisseurs", "referentiel_produits"]

STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
       margin: 0; background: #f6f7f9; color: #1c2733; }
@media (prefers-color-scheme: dark) {
  body { background: #11161c; color: #e6edf3; }
  .carte { background: #1a222c !important; border-color: #2c3844 !important; }
  table { border-color: #2c3844 !important; }
  th { background: #222d39 !important; }
  td, th { border-color: #2c3844 !important; }
  .meta { color: #9fb0c0 !important; }
}
header { background: #14532d; color: #fff; padding: 28px 24px; }
header h1 { margin: 0 0 6px; font-size: 1.5rem; }
header p { margin: 0; opacity: .85; }
main { max-width: 1080px; margin: 0 auto; padding: 24px 16px 64px; }
.carte { background: #fff; border: 1px solid #dde3ea; border-radius: 10px;
         padding: 18px 20px; margin: 22px 0; }
.carte h2 { margin: 0 0 4px; font-size: 1.15rem; }
.meta { color: #5b6b7b; font-size: .85rem; margin: 0 0 12px; }
.table-scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: .85rem;
        border: 1px solid #dde3ea; }
th, td { border: 1px solid #dde3ea; padding: 7px 10px; text-align: left;
         vertical-align: top; }
th { background: #eef1f5; font-weight: 600; }
td.id { font-family: ui-monospace, 'SF Mono', Menlo, monospace; font-size: .78rem;
        white-space: nowrap; }
.ok, .ko { display: inline-block; padding: 2px 10px; border-radius: 999px;
           font-weight: 700; font-size: .75rem; }
.ok { background: #d9f2e3; color: #14532d; }
.ko { background: #fde2e2; color: #991b1b; }
.resume { display: flex; gap: 14px; flex-wrap: wrap; margin: 10px 0 0; }
.pastille { border-radius: 8px; padding: 8px 14px; font-size: .85rem;
            background: #eef1f5; }
@media (prefers-color-scheme: dark) {
  .pastille { background: #222d39; }
  .ok { background: #10402a; color: #7ee2a8; }
  .ko { background: #4a1414; color: #ff9f9f; }
}
footer { text-align: center; color: #5b6b7b; font-size: .8rem; padding: 18px; }
"""


def section_jeu(titre: str, resultats) -> str:
    nb_ko = sum(1 for r in resultats if not r.ok)
    lignes = []
    for r in resultats:
        badge = '<span class="ok">OK</span>' if r.ok else '<span class="ko">KO</span>'
        lignes.append(
            "<tr>"
            f'<td class="id">{escape(r.regle_id)}</td>'
            f"<td>{escape(r.categorie)}</td>"
            f"<td>{escape(r.description)}</td>"
            f"<td>{badge}</td>"
            f"<td>{r.lignes_en_echec or ''}</td>"
            f"<td>{escape(r.details)}</td>"
            "</tr>"
        )
    etat = ("toutes les regles sont respectees" if nb_ko == 0
            else f"{nb_ko} violation(s) detectee(s)")
    return f"""
    <h3>{escape(titre)}</h3>
    <p class="meta">{len(resultats)} regle(s) evaluee(s), {etat}.</p>
    <div class="table-scroll">
    <table>
      <thead><tr><th>Regle</th><th>Categorie</th><th>Description</th>
      <th>Statut</th><th>Lignes KO</th><th>Details</th></tr></thead>
      <tbody>{''.join(lignes)}</tbody>
    </table>
    </div>
    """


def principal() -> int:
    maintenant = datetime.now()
    sections = []
    total_ok = total_ko = 0

    for flux in FLUX:
        contrat = RACINE / "contracts" / f"{flux}.odcs.yaml"
        schema = RACINE / "schemas" / f"{flux}.schema.json"
        bloc = [f'<section class="carte"><h2>Contrat : {escape(flux)}</h2>',
                f'<p class="meta">{escape(str(contrat.relative_to(RACINE)))} · '
                f'{escape(str(schema.relative_to(RACINE)))}</p>']
        for jeu, titre in (("conformes", "Jeu de donnees conforme"),
                           ("casses", "Jeu de donnees volontairement casse")):
            csv_path = RACINE / "data" / jeu / f"{flux}.csv"
            resultats = valider_fichier(contrat, schema, csv_path, maintenant=maintenant)
            total_ok += sum(1 for r in resultats if r.ok)
            total_ko += sum(1 for r in resultats if not r.ok)
            bloc.append(section_jeu(titre, resultats))
        bloc.append("</section>")
        sections.append("".join(bloc))

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rapport de conformite des data contracts ODCS</title>
<style>{STYLE}</style>
</head>
<body>
<header>
  <h1>Rapport de conformite des data contracts</h1>
  <p>Domaine Offre et Supply · Open Data Contract Standard v3 ·
     genere le {maintenant.strftime('%d/%m/%Y a %H:%M')}</p>
  <div class="resume">
    <div class="pastille"><strong>{total_ok}</strong> regles OK</div>
    <div class="pastille"><strong>{total_ko}</strong> violations detectees
      (attendues sur les jeux casses)</div>
  </div>
</header>
<main>
{''.join(sections)}
</main>
<footer>Genere par le validateur de data contracts ·
<a href="https://github.com/adh-studio/data-contracts-odcs">adh-studio/data-contracts-odcs</a></footer>
</body>
</html>
"""
    sortie = RACINE / "docs" / "index.html"
    sortie.parent.mkdir(exist_ok=True)
    sortie.write_text(html, encoding="utf-8")
    print(f"rapport genere : {sortie} ({total_ok} OK, {total_ko} KO)")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
