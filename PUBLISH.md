# Publication

Depuis la racine du projet :

```bash
gh repo create data-contracts-odcs --public \
  --description "Data Contracts ODCS v3 executables pour 3 flux Offre et Supply : schema, regles qualite, SLA fraicheur et completude, validateur Python et rapport de conformite" \
  --source . --push
```

Activer GitHub Pages sur docs/ :

```bash
gh api repos/adh-studio/data-contracts-odcs/pages \
  -X POST -f "source[branch]=main" -f "source[path]=/docs"
```

Verifier :

- CI : https://github.com/adh-studio/data-contracts-odcs/actions
- Pages (quelques minutes apres le premier build) : https://adh-studio.github.io/data-contracts-odcs/
