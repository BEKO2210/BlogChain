# BlockJournal

BlockJournal ist eine dezentrale Social-Media-Plattform, die Blockchain-Technologie nutzt, um Benutzerdaten sicher und privat zu halten. Die Anwendung ermöglicht es Benutzern, Beiträge zu erstellen, Profile zu verwalten und die Blockchain-Daten einzusehen.

## Funktionen

- **Benutzerverwaltung**: Registrierung, Anmeldung und Profilverwaltung
- **Beiträge erstellen**: Teilen Sie Gedanken und Inhalte mit anderen Benutzern
- **Blockchain-Unterstützung**: Alle Daten werden in einer lokalen Blockchain gespeichert
- **Verschlüsselung**: Sichere Speicherung von Benutzerdaten und Schlüsseln
- **Responsive Design**: Funktioniert auf verschiedenen Geräten und Bildschirmgrößen

## Installation

1. Stellen Sie sicher, dass Python 3.8 oder höher installiert ist
2. Klonen Sie das Repository oder entpacken Sie die Dateien in ein Verzeichnis Ihrer Wahl
3. Navigieren Sie zum Projektverzeichnis:

```bash
cd pfad/zu/BlockJournal
```

1. Installieren Sie die erforderlichen Abhängigkeiten:

```bash
pip install -r requirements.txt
```

## Starten der Anwendung

1. Navigieren Sie zum Projektverzeichnis:

```bash
cd pfad/zu/BlockJournal
```

1. Starten Sie die Anwendung:

```bash
python app.py
```

1. Öffnen Sie einen Webbrowser und gehen Sie zu:

```bash
http://localhost:5000
```

## Erste Schritte

1. **Registrieren**: Erstellen Sie ein neues Konto auf der Registrierungsseite
2. **Anmelden**: Melden Sie sich mit Ihren Zugangsdaten an
3. **Profil verwalten**: Passen Sie Ihr Profil auf der Einstellungsseite an
4. **Beiträge erstellen**: Teilen Sie Inhalte über die "Neuen Beitrag erstellen"-Funktion
5. **Blockchain-Info**: Sehen Sie sich Details zu den Blockchain-Blöcken an

## Abhängigkeiten

Die Anwendung verwendet die folgenden Hauptbibliotheken:

- Flask: Web-Framework für die Anwendung
- PyNaCl: Kryptographische Operationen
- Pycryptodome: Verschlüsselungsfunktionen
- Colorlog: Farbiges Logging

## Fehlerbehebung

### Verschlüsselungsfehler

Wenn Sie einen Fehler wie `nacl.exceptions.TypeError: SecretBox must be created from 32 bytes` erhalten, wurde die Verschlüsselungsfunktion verbessert, um dieses Problem zu vermeiden. Sie können dies beheben, indem Sie:

1. Einen neuen Benutzer erstellen
2. Die Anwendung neu starten
3. Sich mit den neuen Anmeldedaten anmelden

### Fehlende Vorlagen

Wenn eine Fehlermeldung wegen fehlender Vorlagen erscheint, stellen Sie sicher, dass alle erforderlichen Dateien im Verzeichnis `app/templates` vorhanden sind.

## Datenschutz und Sicherheit

BlockJournal speichert alle Daten lokal auf Ihrem Gerät. Es werden keine Daten an externe Server gesendet. Die Blockchain-Daten werden mit Ihrem persönlichen Schlüssel verschlüsselt, der aus Ihrem Passwort abgeleitet wird.

## Entwickelt mit ❤️ für Dezentralisierung und Privatsphäre
#   B l o g C h a i n  
 