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
