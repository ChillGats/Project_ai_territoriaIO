# 📓 Journal de Développement (Devlog)

Bienvenue dans le Devlog de notre projet de clone de *Territorial.io* avec IA ! Je documenterai ici toutes nos avancées, nos choix d'architecture et les problèmes rencontrés.

## [2026-09-27] - Phase 1 : Initialisation & Moteur Core

### 🏗️ Architecture Initiale
Création d'un projet structuré professionnellement :
- Séparation du code source dans `src/` (actuellement dans `main.py`).
- Utilisation de **Git** pour le versioning et le déploiement sur GitHub.
- Rédaction de la documentation de base (`README.md`, `DEVLOG.md`).

### 🛠️ Résolution de Problèmes (Troubleshooting)
- **Problème d'installation Pygame** : L'utilisateur utilise une version de Python très récente (3.14) où `distutils` a été retiré. Pygame classique (`pygame 2.6.1`) crashe à la compilation, car il n'y a pas encore de fichiers binaires pré-compilés (wheels) pour cette version de Python, l'obligeant à compiler depuis le code source.
- **Solution** : Passage sur `pygame-ce` (Community Edition) dans `requirements.txt`. C'est un fork de pygame officiel, beaucoup plus actif, qui règle souvent ces problèmes de compatibilité avec les nouvelles versions de Python.

### 🧠 Implémentation de l'IA (DQN)
- Mise en place d'un **Deep Q-Network** avec PyTorch.
- **Espace d'Observation** : Grille normalisée + Ressources des joueurs.
- **Espace d'Action** : 5 actions (Attendre, Haut, Droite, Bas, Gauche).
- **Récompense** : Différentiel de territoire entre l'agent et le bot ennemi.
- L'entraînement a été encapsulé dans une boucle visualisable via Pygame.

### 🎯 Prochaines étapes
- Lancer un premier test d'entraînement pour vérifier que l'apprentissage du réseau de neurones converge vers une stratégie gagnante.
- Modulariser `main.py` (séparer le moteur, l'environnement et l'agent dans des fichiers distincts).
