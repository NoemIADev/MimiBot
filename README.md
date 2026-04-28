# 🤖 MimiBot — L’assistante IA de Noémie

MimiBot est un chatbot basé sur une architecture RAG (Retrieval-Augmented Generation), conçu pour me présenter, mon parcours, mes compétences et mes projets de manière interactive.

L’objectif est simple : permettre à un recruteur ou un visiteur de poser des questions naturelles et d’obtenir des réponses pertinentes, contextualisées et fiables.

---

## ✨ Aperçu

Mimi est une assistante conversationnelle qui :
- répond aux questions sur Noémie (profil, projets, compétences)
- utilise une base de connaissances personnalisée (documents markdown)
- s’appuie sur un système RAG pour générer des réponses contextualisées
- garde un historique de conversation pour améliorer la pertinence

---

## 🧠 Architecture

Le projet repose sur plusieurs briques :

### Backend (FastAPI)
- API `/ask_mimi` pour interroger le bot 
- gestion de l’historique conversationnel
- construction dynamique du prompt

### RAG (Retrieval-Augmented Generation)
- embeddings via Azure OpenAI :contentReference
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
