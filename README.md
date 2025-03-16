# BlogChain

Eine sichere und dezentralisierte Blog-Plattform basierend auf Blockchain-Technologie.

## Beschreibung

BlogChain ist eine moderne Web-Anwendung, die Blogging mit Blockchain-Technologie kombiniert. Die Plattform ermöglicht Benutzern, Beiträge zu erstellen, die in einer persönlichen Blockchain gespeichert werden, was Unveränderlichkeit und Sicherheit gewährleistet.

## Hauptfunktionen

- **Blockchain-basierte Speicherung**: Alle Beiträge werden in einer persönlichen Blockchain gesichert
- **Kryptographische Sicherheit**: Verwendung moderner Verschlüsselungsmethoden
- **Benutzerfreundliche Oberfläche**: Einfache und intuitive Benutzeroberfläche
- **Blockchain-Explorer**: Visualisierung und Überprüfung der Blockchain
- **Blockchain-Validierung**: Überprüfung der Integrität der Blockchain
- **Backup-Funktionalität**: Erstellung verschlüsselter Backups der Blockchain

## Technologien

- Python (Flask)
- JavaScript
- HTML/CSS
- SQLite
- Blockchain-Implementierung
- Kryptographische Bibliotheken

## Installation und Start

### Lokale Installation

```bash
# Repository klonen
git clone https://github.com/BEKO2210/BlogChain.git
cd BlogChain

# Virtuelle Umgebung erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Anwendung starten
python app.py
```

### Deployment mit Docker

BlogChain kann einfach mit Docker deployed werden, was eine konsistente Umgebung und einfache Installation auf jedem System ermöglicht.

#### Voraussetzungen

- Docker installiert
- Docker Compose installiert

#### Docker-Installation

```bash
# Repository klonen
git clone https://github.com/BEKO2210/BlogChain.git
cd BlogChain

# Container bauen und starten
docker-compose up -d --build

# Log-Ausgabe anzeigen (optional)
docker-compose logs -f
```

Die Anwendung ist dann unter [http://localhost:5000](http://localhost:5000) verfügbar.

#### Konfiguration anpassen

Sie können die Docker-Konfiguration anpassen, indem Sie die Umgebungsvariablen in der `docker-compose.yml` Datei ändern:

```yaml
environment:
  - FLASK_APP=app.py
  - FLASK_ENV=production
  - HOST=0.0.0.0
  - PORT=5000
  - SECRET_KEY=ihr_geheimer_schluessel
```

#### Datenvolumes

Die Anwendung speichert ihre Daten in Docker-Volumes, die auch bei Neustart des Containers erhalten bleiben:

- `blogchain_data`: Enthält Benutzerprofile, Blockchain-Daten und Backups
- `blogchain_logs`: Enthält Anwendungslogs

## Nutzung

Nach dem Start der Anwendung kann über [http://localhost:5000](http://localhost:5000) auf die Plattform zugegriffen werden. Neue Benutzer können sich registrieren und sofort mit dem Erstellen von Beiträgen beginnen.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.







#BlogChain

A secure and decentralized blog platform based on blockchain technology.

##Description

BlogChain is a modern web application that combines blogging with blockchain technology. The platform allows users to create posts that are stored in a personal blockchain, ensuring immutability and security.

##Main Features

Blockchain-Based Storage: All posts are securely stored in a personal blockchain

Cryptographic Security: Uses modern encryption methods

User-Friendly Interface: Simple and intuitive user experience

Blockchain Explorer: Visualization and verification of the blockchain

Blockchain Validation: Ensures the integrity of the blockchain

Backup Functionality: Creates encrypted backups of the blockchain


##Technologies

Python (Flask)

JavaScript

HTML/CSS

SQLite

Blockchain Implementation

Cryptographic Libraries


##Installation and Startup

Local Installation
```bash
# Clone the repository  
git clone https://github.com/BEKO2210/BlogChain.git  
cd BlogChain  

# Create and activate a virtual environment  
python -m venv venv  
source venv/bin/activate  # On Windows: venv\Scripts\activate  

# Install dependencies  
pip install -r requirements.txt  

# Start the application  
python app.py
```
Deployment with Docker

BlogChain can be easily deployed using Docker, ensuring a consistent environment and simple installation on any system.

Prerequisites

Docker installed

Docker Compose installed


Docker Installation
```bash
# Clone the repository  
git clone https://github.com/BEKO2210/BlogChain.git  
cd BlogChain  

# Build and start the container  
docker-compose up -d --build  

# View logs (optional)  
docker-compose logs -f
```
The application will then be available at http://localhost:5000.

Configuration

You can adjust the Docker configuration by modifying environment variables in the docker-compose.yml file:

```bash
environment:
  - FLASK_APP=app.py
  - FLASK_ENV=production
  - HOST=0.0.0.0
  - PORT=5000
  - SECRET_KEY=your_secret_key
```

Data Volumes

The application stores its data in Docker volumes, which persist even after container restarts:

blogchain_data: Stores user profiles, blockchain data, and backups

blogchain_logs: Stores application logs


Usage

After starting the application, the platform can be accessed via http://localhost:5000. New users can register and start creating posts immediately.

License

This project is licensed under the MIT License.


