# Prédiction des pièces défectueuses sur une ligne de production (Bosch)

Projet de session du cours **8INF700 – Forage de données** (UQAC, automne 2026).

Le jeu de données [Bosch Production Line Performance](https://www.kaggle.com/c/bosch-production-line-performance) décrit
**1 183 747 pièces** et plus de **4 000 variables** mesurées le long de 4 lignes et 52 stations. Seulement **0,58 %** des
pièces sont défectueuses. L'objectif : repérer les pièces à risque et comprendre où et quand les défauts apparaissent.

Le projet suit la démarche **CRISP-DM** et utilise **PySpark** pour traiter tout le jeu de données sur un ordinateur
portable (7,6 Go de mémoire).

![Application interactive – vue d'ensemble](images/app_vue_ensemble.png)

## Ce que fait le projet

1. **Big Data** – conversion des fichiers CSV (7,2 Go) au format Parquet (environ 1,2 Go) avec Spark.
2. **Exploration** – taux de défauts par station, par parcours et par période de production.
3. **Préparation** – reconstruction du parcours et du temps de passage de chaque pièce ; 4 266 colonnes ramenées à 827
   variables, puis à 150.
4. **Modélisation** – régression logistique, forêt aléatoire et GBT (Spark MLlib), avec gestion du déséquilibre
   (sous-échantillonnage) et réglage du seuil de décision.
5. **Méthodes non supervisées** – K-means (familles de parcours) et FP-Growth (combinaisons de stations à risque).
6. **Visualisation** – tableau de bord Power BI et application web interactive (Streamlit).

## Principaux résultats

| Indicateur | Valeur |
|---|---|
| Meilleur modèle | GBT entraîné sur un échantillon rééquilibré de 335 040 pièces |
| MCC sur le jeu de test (177 318 pièces) | **0,284** |
| Précision / rappel | 71,2 % / 11,5 % |
| Défauts détectés / fausses alertes | 116 / 47 |
| Station la plus à risque | S32 : 4,51 % de défauts (7,8 fois la moyenne) |
| Parcours le plus à risque | S24 + S26 + S32 : 8,50 % de défauts (lift de 14,6) |

Autre constat : les défauts arrivent **par séries** dans le temps. Les variables liées à l'ordre de passage des pièces
font partie des plus utiles au modèle.

**Limites** : le rappel reste faible, car environ 9 défauts sur 10 ne laissent aucune trace dans les mesures fournies.
Les variables sont anonymisées : on sait où se trouve un problème, pas pourquoi il se produit.

## Technologies

Python 3.10 · PySpark 4.2 · Spark MLlib · Parquet · Jupyter · Java 17 · Ubuntu (WSL2) · Power BI · Streamlit · Plotly · pandas

## Organisation du dépôt

```
├── notebooks/            # carnets Jupyter (01_conversion_parquet.ipynb … 04_modelisation.ipynb)
├── app_bosch.py          # application web interactive (Streamlit)
├── requirements.txt      # bibliothèques de l'application
├── bosch_export/         # résultats exportés par Spark (fichiers CSV lus par l'application)
├── powerbi/              # tableau de bord Power BI (.pbix)
├── rapport/              # rapport complet du projet (PDF)
└── images/               # captures d'écran
```

Les données brutes de Kaggle ne sont pas incluses (plusieurs Go, et soumises aux règles de la compétition). Elles se
téléchargent avec l'API Kaggle :

```bash
kaggle competitions download -c bosch-production-line-performance
```

## Lancer l'application interactive

L'application lit seulement les fichiers CSV de `bosch_export/` : il n'est pas nécessaire d'installer Spark.

```bash
pip install -r requirements.txt
streamlit run app_bosch.py
```

Elle s'ouvre dans le navigateur (http://localhost:8501) et propose cinq pages : vue d'ensemble, stations, parcours à
risque, modèle et seuil d'alerte, recherche d'une pièce.

![Application interactive – choix du seuil](images/app_modele_seuil.png)

## Auteur

**Vamoussa Diabate** – baccalauréat en sciences des données et intelligence d'affaires, UQAC.
