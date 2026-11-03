# AI Data Analyst Agent

Un agent d'analyse de données qui permet de poser des questions en langage naturel sur des ventes et d'obtenir des réponses chiffrées, des analyses et des graphiques. L'application utilise un modèle Groq pour comprendre la question et générer des requêtes SQL exécutées sur une base DuckDB locale.

> **Projet de démonstration** : la base fournie contient des données synthétiques, pas des données réelles d'entreprise.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Comment fonctionne le projet](#comment-fonctionne-le-projet)
- [Technologies utilisées](#technologies-utilisées)
- [Données de démonstration](#données-de-démonstration)
- [Installation](#installation)
- [Lancement](#lancement)
- [Exemples de questions](#exemples-de-questions)
- [Tests](#tests)
- [Structure du projet](#structure-du-projet)
- [Dépannage](#dépannage)
- [Sécurité et limites](#sécurité-et-limites)
- [Licence et attribution](#licence-et-attribution)

## Fonctionnalités

- Questions en langage naturel sur les ventes, produits et clients.
- Découverte du schéma de la base puis génération et exécution de requêtes SQL.
- Classements et comparaisons de chiffre d'affaires.
- Statistiques descriptives : total, moyenne, médiane, minimum, maximum et tendance.
- Détection simple de valeurs atypiques à partir d'un seuil en écarts-types.
- Graphiques en barres, courbes, secteurs et nuages de points.
- Historique de conversation permettant de poser des questions de suivi.
- Choix entre deux moteurs d'agent : boucle manuelle et LangGraph.
- Affichage facultatif des outils appelés par l'agent.
- Chargement de plusieurs fichiers CSV, Excel (`.xlsx`) et JSON comme tables temporaires.
- Questions suggérées automatiquement à partir des colonnes et types de données détectés.

## Comment fonctionne le projet

1. L'utilisateur pose une question depuis l'interface Streamlit.
2. L'agent demande au modèle Groq de déterminer les étapes nécessaires.
3. L'agent peut découvrir les tables et colonnes, puis construire et exécuter une requête `SELECT` sur DuckDB.
4. Les résultats sont résumés; des statistiques et un graphique peuvent être produits à partir du résultat SQL.
5. L'agent formule une réponse en langage naturel et l'interface affiche les graphiques générés.

```text
Question
   ↓
Interface Streamlit
   ↓
Agent manuel ou LangGraph
   ↓
Outils SQL, statistiques et graphiques
   ↓
Base locale DuckDB
   ↕
Modèle Groq (gpt-oss-120b)
```

Dans la barre latérale de l'application, choisissez **LangGraph** ou **Manuel** et le dataset à interroger. L'option « Afficher les outils appelés » permet de consulter les appels effectués par l'agent.

## Technologies utilisées

- **Python** : langage de programmation.
- **Streamlit** : interface web interactive.
- **Groq** et **gpt-oss-120b** : modèle de langage utilisé pour l'analyse des questions.
- **DuckDB** : base de données embarquée stockée localement.
- **LangGraph** et **LangChain** : orchestration alternative de l'agent.
- **Matplotlib** : génération des graphiques.

## Données de démonstration

Le fichier `data/sales.duckdb` contient une base DuckDB avec trois tables :

| Table | Contenu principal |
|---|---|
| `sales` | Transactions : date, produit, client, quantité et chiffre d'affaires |
| `products` | Nom, catégorie et prix unitaire des produits |
| `customers` | Nom, pays et segment (`Retail`, `Wholesale`, `VIP`) |

Les données sont synthétiques et créées par `src/data/setup_db.py`. Le script définit des ventes du **1er janvier 2023 au 6 octobre 2026** environ, avec des produits et clients fictifs. Le fichier de base est déjà fourni dans le projet; il n'est normalement pas nécessaire de le générer à nouveau.

> **Attention** : lancer `python src/data/setup_db.py` recrée les tables de la base de démonstration. Ne l'exécutez pas sur une base contenant des données que vous souhaitez conserver.

### Utiliser ses propres fichiers

1. Dans la barre latérale de l'application, chargez un ou plusieurs fichiers **CSV**, **Excel `.xlsx`** ou **JSON**.
2. Chaque fichier devient une table DuckDB. Si un classeur Excel contient plusieurs feuilles, chaque feuille est chargée séparément.
3. Choisissez **Mon dataset** dans la liste des sources de données. Vous pouvez revenir aux **Données de démonstration** à tout moment.
4. Consultez les tables et colonnes détectées, puis cliquez sur une question suggérée ou écrivez la vôtre.

Les noms des tables sont dérivés des noms de fichiers et des feuilles. Le contenu doit être tabulaire, avec une ligne d'en-tête pour les CSV et des objets/lignes structurés pour les JSON. Les fichiers importés sont chargés dans une base DuckDB en mémoire, propres à la session Streamlit : ils ne remplacent pas `data/sales.duckdb` et sont perdus à la fermeture de la session ou de l'application. Pour conserver des données entre les sessions, chargez-les à nouveau.

Les exemples de questions sont construits à partir des colonnes détectées. Vous pouvez notamment demander :

- « Combien de lignes contient cette table ? »
- « Quel est le total et la moyenne de cette mesure ? »
- « Compare cette mesure par catégorie. »
- « Comment cette valeur évolue-t-elle au fil du temps ? »
- « Quelles sont les valeurs les plus fréquentes de cette colonne ? »

## Installation

### Prérequis

- Python **3.12 recommandé**. Le dépôt ne déclare pas de plage de versions Python officiellement testées; les dépendances peuvent ne pas être compatibles avec les versions les plus récentes.
- Git, si vous souhaitez cloner le dépôt.
- Une clé API Groq valide, nécessaire pour interroger le modèle.
- Un accès Internet pour les appels à l'API Groq.

### 1. Ouvrir le dossier du projet

Si le projet est déjà téléchargé, ouvrez un terminal à sa racine — le dossier contenant `requirements.txt` — et passez directement à l'étape suivante.

Pour cloner le dépôt, utilisez son URL Git officielle :

```bash
git clone <URL_DU_DEPOT>
cd <NOM_DU_DOSSIER>
```

Remplacez les valeurs entre chevrons par l'URL et le nom réels du dépôt.

### 2. Créer et activer un environnement virtuel

**Windows — PowerShell :**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows — Git Bash :**

```bash
py -3.12 -m venv .venv
source .venv/Scripts/activate
```

**macOS ou Linux :**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Si la commande `py -3.12` échoue, installez Python 3.12 puis ouvrez un nouveau terminal. Dans Git Bash, ne lancez pas `Activate.ps1` : ce script est réservé à PowerShell.

### 3. Installer les dépendances

Avec l'environnement virtuel activé :

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configurer la clé API Groq

À la racine du projet, créez un fichier nommé `.env` et ajoutez-y votre clé :

```text
GROQ_API_KEY=votre_cle_api_groq
```

Vous pouvez copier `.env.example` vers `.env`, puis remplacer la valeur d'exemple par votre clé. Créez ou gérez cette clé depuis [console.groq.com/keys](https://console.groq.com/keys). Ne publiez jamais votre clé et ne la collez pas dans le code ou dans une capture d'écran. Le fichier `.env` et les secrets Streamlit locaux sont ignorés par Git.

Pour un déploiement sur Streamlit Community Cloud, ouvrez **App settings → Secrets** et ajoutez :

```toml
GROQ_API_KEY = "votre_cle_api_groq"
```

Le client Groq lit cette valeur depuis les secrets Streamlit en ligne et depuis `.env` en local.

## Lancement

Depuis la racine du projet, avec l'environnement virtuel activé et le fichier `.env` configuré :

```bash
streamlit run src/ui/app.py
```

À la première exécution, Streamlit peut proposer de saisir une adresse e-mail pour recevoir des communications. Cette saisie est facultative : appuyez sur **Entrée** pour continuer sans la fournir.

Ouvrez ensuite [http://localhost:8501](http://localhost:8501) dans votre navigateur. Gardez le terminal ouvert tant que l'application est utilisée. Pour l'arrêter, revenez dans le terminal et faites `Ctrl+C`.

## Exemples de questions

- Quels sont les trois produits qui ont généré le plus de chiffre d'affaires en 2024 ?
- Quelle a été l'évolution mensuelle du chiffre d'affaires en 2024 ?
- Compare le chiffre d'affaires de 2023 et 2024 par catégorie.
- Quels sont les clients du segment VIP qui ont le plus dépensé ?
- Y a-t-il des anomalies dans les ventes mensuelles ?
- Génère un graphique des ventes par pays.

Les réponses dépendent des données présentes dans la base. Le chiffre d'affaires correspond à la colonne `revenue` des transactions.

## Tests

Les tests sont des scripts Python individuels. Depuis la racine du projet et avec l'environnement activé :

```bash
python tests/test_tools.py
```

Ce test vérifie les outils de base liés à DuckDB sans appeler le modèle. Les scripts `test_llm.py`, `test_agent.py`, `test_langgraph.py`, `test_memory.py`, `test_analysis.py`, `test_plot.py` et `test_self_healing.py` exercent différentes fonctions du modèle ou de l'agent et nécessitent une configuration Groq valide lorsqu'ils font appel au LLM.

## Structure du projet

```text
.
├── data/
│   └── sales.duckdb          # Base DuckDB de démonstration
├── outputs/                  # Graphiques générés
├── src/
│   ├── agent/
│   │   ├── graph.py          # Agent orchestré avec LangGraph
│   │   └── loop.py           # Boucle d'agent manuelle
│   ├── data/
│   │   ├── setup_db.py       # Génération de la base synthétique
│   │   └── user_datasets.py  # Import des fichiers personnalisés
│   ├── llm/
│   │   ├── client.py         # Clients API Groq
│   │   └── prompts.py        # Instructions du data analyst
│   ├── tools/
│   │   ├── sql_tools.py      # Lecture des tables et requêtes SQL
│   │   ├── analysis_tools.py # Statistiques et détection d'anomalies
│   │   └── plot_tools.py     # Création des graphiques
│   └── ui/
│       └── app.py            # Interface Streamlit
├── tests/                    # Scripts de test
├── .env                      # Clé API locale, non versionnée
└── requirements.txt          # Dépendances Python
```

## Dépannage

### Erreur `Invalid API Key` (401)

- Vérifiez que la clé provient bien de Groq et qu'elle est active.
- Vérifiez que le fichier `.env` se trouve à la racine du projet et contient `GROQ_API_KEY=...`.
- Si `GROQ_API_KEY` est déjà définie dans votre terminal, elle peut prendre priorité sur la valeur du fichier `.env`. Dans Git Bash, vous pouvez supprimer cette variable pour la session avec `unset GROQ_API_KEY`.
- Arrêtez puis relancez Streamlit après toute modification de la clé.
- Ne transmettez pas votre clé dans une demande d'aide.

### Erreur de compilation de `zstandard` ou demande de compilateur C++

Une version de Python très récente peut ne pas avoir de paquet précompilé compatible avec toutes les dépendances. Essayez Python 3.12 en créant un nouvel environnement virtuel, puis réinstallez les dépendances dans celui-ci. Si l'erreur persiste, consultez les instructions d'installation de Microsoft C++ Build Tools.

### L'application ne trouve pas la base

Lancez Streamlit depuis la racine du projet, afin que les chemins relatifs comme `outputs/` pointent au bon endroit. Vérifiez que `data/sales.duckdb` existe. Vous pouvez recréer la base avec `python src/data/setup_db.py`, en gardant à l'esprit que cette opération remplace les tables présentes dans ce fichier.

## Sécurité et limites

- La clé API doit rester secrète. Vérifiez que `.env` n'est pas suivi par Git avant toute publication.
- Les questions, le contexte de conversation et les informations nécessaires à la réponse sont envoyés au service Groq pour générer le résultat. N'utilisez pas de données confidentielles sans avoir vérifié les règles de confidentialité et les conditions du service.
- Avec un fichier importé, les données sont lues localement, mais le schéma et les résultats SQL nécessaires à la réponse peuvent être transmis au modèle Groq. Évitez les données personnelles ou confidentielles si vous n'êtes pas autorisé à les envoyer à ce service.
- La base de démonstration est locale; les questions SQL sont exécutées sur DuckDB.
- Les résultats générés par un modèle peuvent être inexacts. Vérifiez les chiffres et les requêtes avant de vous en servir pour prendre une décision.
- Ce projet est un prototype pédagogique, pas un système de reporting certifié ou une solution de production prête à l'emploi.

## Licence et attribution

Aucun fichier `LICENSE` n'est actuellement fourni dans ce dépôt. Avant de republier ou redistribuer le projet, vérifiez la licence annoncée dans le dépôt Git d'origine et respectez ses conditions. Un badge de licence dans un ancien README ne remplace pas le texte de licence. La propriété du code original n'est pas transférée par le téléchargement ou la modification du projet.

---

Projet de démonstration d'analyse de données conversationnelle avec Python, DuckDB, Groq et Streamlit.
