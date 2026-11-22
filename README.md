# 🤖 MimiBot — L’assistante IA de Noémie

MimiBot est un chatbot basé sur une architecture RAG (Retrieval-Augmented Generation), conçu pour me présenter, mon parcours, mes compétences et mes projets de manière interactive.

L’objectif est simple : permettre à un recruteur ou un visiteur de poser des questions naturelles et d’obtenir des réponses pertinentes, contextualisées et fiables.

---

## ✨ Aperçu

Mimi est une assistante conversationnelle qui :
- répond aux questions sur Moi (profil, projets, compétences)
- utilise une base de connaissances personnalisée (documents markdown)
- s’appuie sur un système RAG pour générer des réponses contextualisées
- garde un historique de conversation anonyme pour améliorer la pertinence

---

## 🧠 Architecture

Le projet repose sur plusieurs briques :

### Backend (FastAPI)
- API `/ask_mimi` pour interroger le bot 
- gestion de l’historique conversationnel
- construction dynamique du prompt

### RAG (Retrieval-Augmented Generation)
- embeddings via OpenRouter :contentReference
- stockage dans PostgreSQL + pgvector
- recherche par similarité vectorielle

### Pipeline d’ingestion
- lecture des fichiers `.md`
- découpage en chunks
- génération des embeddings
- insertion en base 

### Frontend (React + Vite)
- interface conversationnelle moderne
- gestion d’un session_id
- affichage dynamique des messages 

### Déploiement
- Docker (front + back)
- CI/CD avec GitHub Actions
- déploiement sur Azure Web Apps

---

## 🚀 Version 1 — Ce qui a été fait

La première version de MimiBot permettait :

- poser une question → réponse via LLM
- récupérer du contexte depuis une base vectorielle
- structurer un prompt avec contexte + question
- déployer une app complète (front + back + DB)

👉 Objectif atteint : **un chatbot fonctionnel basé sur du RAG**

---

## ⚠️ Problèmes rencontrés

Comme tout projet réel, la V1 a révélé plusieurs limites :

### 🔹 Pertinence des réponses
- trop dépendant du top 3 chunks
- manque de filtrage sémantique
- réponses parfois génériques

### 🔹 Manque de contexte global
- difficulté à répondre à des questions larges  
  (ex : “quels projets a-t-elle fait ?”)

### 🔹 Absence d’inférence
- le bot ne déduisait pas les compétences à partir des projets

### 🔹 Historique mal exploité
- pas de lien entre les questions successives

---

## 🔧 Améliorations apportées

Suite à ces constats, plusieurs améliorations ont été mises en place :

### ✅ Amélioration du retrieval
- ajout d’un seuil de distance sémantique
- augmentation du nombre de chunks analysés
- ajout d’une étape de reformulation de la question utilisateur par un LLM afin d’améliorer la qualité du retrieval

### ✅ Ajout de l’historique conversationnel
- stockage des échanges en base
- réinjection dans le prompt

### ✅ Meilleure structuration des données
- création de documents markdown plus riches
- organisation par thématiques (présentation, projets, etc.)

### ✅ Pipeline d’ingestion optimisé
- création d'un agent qui crée insert les document dans la base de données

---

## 🧪 État actuel

MimiBot est aujourd’hui :
- fonctionnel
- déployé
- en amélioration continue

Certaines limites subsistent (compréhension globale, inférence), mais le projet démontre déjà :

👉 capacité à concevoir une architecture IA complète  
👉 capacité à déployer une application réelle  
👉 capacité à analyser et améliorer un système existant  

---

## 📌 Améliorations futures

- amélioration de la capacité du bot à déduire des compétences à partir des projets décrits
- amélioration du ranking des chunks
- ajout de mémoire long terme (résumés)
- enrichissement du dataset
- ajout d’un système de feedback utilisateur pour collecter des retours sur la pertinence des პასუხes
- implémentation d’un cache sémantique des questions/réponses permettant de détecter les requêtes similaires et d’éviter des appels inutiles au LLM

---

## 🔗 Liens

- 💼 LinkedIn : https://www.linkedin.com/in/noemie-majerus-devia  
- 💻 GitHub : https://github.com/NoemIADev  

---

## 🧩 À propos

MimiBot est un projet personnel conçu et développé de manière autonome.

L’idée est née d’une réflexion simple : comment présenter efficacement un profil technique à travers une expérience interactive, plutôt qu’un CV statique ?

Ce projet s’inscrit dans une démarche plus large autour des applications basées sur les LLM, notamment sur les problématiques de compréhension, de mémoire et de contextualisation.

Au-delà de l’aspect technique, MimiBot reflète une volonté de concevoir des outils utiles, accessibles et orientés utilisateur.


## Déploiement du backend sur AWS

Le workflow `.github/workflows/aws-backend.yml` remplace les workflows Azure
(déploiement front/back et ping). Leur suppression ne supprime pas les applications
Azure existantes. Le frontend n'est plus déployé automatiquement par ce dépôt.

La cible choisie est **AWS App Runner avec une image privée Amazon ECR**.
Le workflow s'exécute sur un push dans `main` touchant `app/` ou le workflow,
et peut être lancé manuellement depuis GitHub Actions sur `main`.
Il construit l'image avec le contexte `app/`, teste `GET /` sans accès réseau,
publie un tag unique, met à jour App Runner, attend le résultat de l'opération
et vérifie `GET /` en HTTPS. Il ne lance ni migration SQL ni ingestion ni appel IA.
Ce contrôle de santé ne constitue pas un test RAG de bout en bout.

Les dépendances directes Python sont fixées dans `app/requirements.txt` et utilisées
par le Dockerfile. Les dépendances transitives ne sont pas verrouillées.

### Configuration GitHub à effectuer avant le premier lancement

Dans **Settings > Secrets and variables > Actions > Variables**, définir :

| Variable | Valeur attendue |
| --- | --- |
| `AWS_REGION` | Région du dépôt ECR et du service App Runner |
| `AWS_ROLE_ARN` | ARN du rôle IAM assumé par GitHub Actions via OIDC |
| `ECR_REPOSITORY` | Nom du dépôt ECR privé, sans le registre ni le tag |
| `APP_RUNNER_SERVICE_ARN` | ARN du service App Runner existant |

Le rôle GitHub doit faire confiance au fournisseur OIDC GitHub, avec l'audience
`sts.amazonaws.com` et le sujet `repo:OWNER/REPO:ref:refs/heads/main`.
Limiter ses permissions au dépôt et au service concernés : authentification ECR,
upload d'images (`GetAuthorizationToken`, `BatchCheckLayerAvailability`,
`InitiateLayerUpload`, `UploadLayerPart`, `CompleteLayerUpload`, `PutImage`),
et App Runner (`DescribeService`, `UpdateService`, `ListOperations`).
Prévoir `iam:PassRole` limité aux rôles App Runner si requis par la mise à jour.
Aucune clé AWS permanente n'est stockée dans le workflow.

### Ressources AWS préalables

Le dépôt ECR privé et un service App Runner basé sur une image ECR doivent déjà
exister dans le même compte et la même région. Le service doit être `RUNNING`.
Pour amorcer un nouveau service, construire et publier une première image depuis
une machine équipée de Docker, puis créer le service App Runner avec cette image.
Le workflow assure ensuite les mises à jour ; il ne crée pas l'infrastructure.

Configurer le port **8000**, un accès public HTTPS et un contrôle HTTP sur `/`.
Le rôle d'accès ECR d'App Runner doit pouvoir lire le dépôt. Son rôle d'instance
doit pouvoir lire les secrets utilisés. Autoriser les connexions sortantes vers
Neon et OpenRouter. Désactiver le déploiement automatique App Runner pour laisser
GitHub Actions piloter les mises à jour (le workflow impose également ce réglage).

Configurer dans App Runner, en utilisant Secrets Manager pour les secrets :

- `DATABASE_URL` : URL Neon poolée avec TLS.
- `OPENROUTER_API_KEY` : clé du fournisseur existant.
- `OPENROUTER_BASE_URL`, `OPENROUTER_LLM_MODEL`, `OPENROUTER_EMBEDDING_MODEL` : valeurs actuelles.
- `OPENROUTER_EMBEDDING_DIMENSIONS=1536`.
- `ALLOWED_ORIGINS` : origine exacte du frontend, sans chemin.

Le workflow conserve ces variables et références de secrets lors des mises à jour.
Il n'embarque pas le `.env` local. Au basculement du frontend, sa configuration
`VITE_API_URL` devra viser `https://<adresse-backend>/ask_mimi`, puis le frontend
devra être reconstruit. Ce basculement n'est pas effectué par le workflow backend.

## Configuration Neon du backend

Le backend FastAPI conserve psycopg2, les prompts et les mod?les OpenRouter existants.
Le projet Neon est `little-salad-68218879`, branche `production`, organisation
`org-small-butterfly-12202345`. `neon.ts` configure uniquement PostgreSQL.
Le package npm ? la racine sert aux outils Neon et relaie le build du frontend.

Apr?s `neon login`, ex?cuter `neon deploy` depuis la racine. Le CLI r?cup?re
`DATABASE_URL` (pool?e) et `DATABASE_URL_UNPOOLED` (directe) dans `.env`, ou
`.env.local` si `.env` n'existe pas. Garder les param?tres TLS des URL Neon.
Ne jamais copier ces secrets dans `.env.example` ou dans le frontend.
Les variables syst?me sont prioritaires, puis `.env.local`, puis `.env`.

Pour cette base, configurer `OPENROUTER_EMBEDDING_DIMENSIONS=1536` : le mod?le
existant renvoie sinon 4096 dimensions, incompatibles avec `VECTOR(1536)`.
Ce r?glage demande la dimension au fournisseur sans changer le mod?le ni tronquer
localement les vecteurs. Sans cette variable, le comportement pr?c?dent demeure.
Les autres variables OpenRouter restent n?cessaires (voir `.env.example`).

V?rifications manuelles depuis la racine (Python avec les d?pendances du Dockerfile) :

```sh
python scripts/check_neon.py
python scripts/check_neon.py --rag
npm run build
python -m uvicorn main:app --app-dir app --host 127.0.0.1 --port 8000
```

Le contr?le PostgreSQL et le contr?le RAG ne modifient aucune donn?e. `--rag`
appelle le fournisseur d'embeddings. Pour initialiser explicitement une base,
`python scripts/check_neon.py --apply-schema` applique le fichier `create.sql`
avec l'URL directe, dans une transaction. Il active pgvector et cr?e uniquement
les tables absentes ; il ne migre pas les colonnes de tables d?j? pr?sentes.
Aucune ingestion n'est d?clench?e par ces commandes ou au d?marrage de l'API.

Validation du 22 novembre 2026 : connexion TLS r?ussie, pgvector 0.8.7,
tables documents/chunks/qa_history et colonnes vector(1536) v?rifi?es ; build
Vite r?ussi ; POST /ask_mimi HTTP 200 et historique relu depuis Neon.
La session `neon-smoke-test-2026-11-22` est conserv?e dans qa_history.
Documents et chunks ?taient vides : la pertinence documentaire du RAG ne peut
pas ?tre valid?e avant une ingestion d?cid?e s?par?ment.
