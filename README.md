# Dashboard — Traitement des dossiers administratifs

Application Streamlit répondant aux six questions de l'exercice avec pandas et matplotlib.

## Fichiers
- `app.py` : application
- `requirements.txt` : dépendances
- `04_Finance_Administration_Juridique(1).xlsx` : données Excel (à placer à côté de `app.py` pour lancement local)

## Lancement local
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```
Si le classeur n'est pas dans le même dossier, importez-le via le téléverseur Excel dans la barre latérale.

## Publication sur Streamlit Community Cloud
1. Créez un dépôt GitHub et ajoutez `app.py`, `requirements.txt` et le classeur Excel.
2. Ouvrez https://share.streamlit.io/ et connectez votre compte GitHub.
3. Choisissez le dépôt, la branche et `app.py`, puis cliquez sur Deploy.
4. Le classeur doit être inclus dans le dépôt ou importé par l'utilisateur dans l'application.

## Méthodologie
- Retard = durée réelle strictement supérieure à l'objectif, uniquement pour les dossiers clôturés.
- Les durées et coûts absents des dossiers en cours restent manquants.
- Les filtres ville, service, type et période s'appliquent à toutes les réponses.
- L'écart entre dossiers complets/incomplets est descriptif et ne démontre pas une causalité.
