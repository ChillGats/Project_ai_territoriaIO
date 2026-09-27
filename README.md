# Territorial.io AI Clone

Un clone simplifié du jeu *Territorial.io* implémenté en Python, utilisant NumPy pour le moteur de jeu, Pygame pour le rendu, et intégrant un agent d'Intelligence Artificielle basé sur le **Deep Q-Learning** (via PyTorch).

## 🚀 Fonctionnalités

- **Moteur de jeu NumPy** : Logique de la carte et de l'expansion vectorisée pour de meilleures performances.
- **Rendu Pygame** : Visualisation en temps réel de l'environnement de jeu.
- **IA Deep Q-Network (DQN)** : Un agent qui apprend à jouer de manière autonome.
- **Bot Ennemi** : Un adversaire au comportement aléatoire servant de benchmark d'entraînement.

## 🛠️ Installation

Le projet nécessite Python 3.10 ou supérieur.

```bash
# 1. Cloner le repository
git clone https://github.com/ChillGats/Project_ai_territoriaIO.git
cd Project_ai_territoriaIO

# 2. Créer un environnement virtuel (optionnel mais recommandé)
python -m venv .venv
source .venv/bin/activate  # Sous Windows : .venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt
```
*(Note : Nous utilisons `pygame-ce`, la Community Edition de Pygame, pour une meilleure compatibilité avec les nouvelles versions de Python).*

## 🎮 Lancement

Pour démarrer l'entraînement de l'IA avec affichage graphique :

```bash
python src/main.py
```

## 📂 Structure du projet

- `src/` : Code source du projet
  - `main.py` : Moteur de jeu, environnement Gym et Agent IA.
- `docs/` : Documentation et suivi de projet
  - `DEVLOG.md` : Journal de développement.
- `requirements.txt` : Dépendances Python.
