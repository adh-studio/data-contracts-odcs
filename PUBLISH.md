# Publication

Depuis la racine du projet :

```bash
gh repo create data-contracts-odcs --public \
  --description "Data Contracts au standard ODCS v3 pour des flux d'import/distribution : validation de schema, regles qualite, SLA de fraicheur, rapport de conformite" \
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
