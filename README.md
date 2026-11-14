# 🛡️ WebBrowserCleanup — Anti-Scamware, Web Push & Browser Lock

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?logo=windows)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-None%20(Stdlib%20Only)-success)
![License](https://img.shields.io/badge/License-MIT-green)

🌍 **[🇫🇷 Version Française](#-version-française)** | **[🇬🇧 English Version](#-english-version)**

---

# 🇫🇷 Version Française

**WebBrowserCleanup** est un utilitaire léger, sans aucune dépendance externe, conçu pour débloquer instantanément un PC victime de **Browser Lock** (pages pièges en plein écran) et éradiquer les **fausses alertes de virus (Scamware / Scareware par notifications Web Push)** qui persistent sous Windows même lorsque le navigateur est fermé.

## 🚨 Quel problème résout cet outil ?

Lorsqu'un utilisateur clique accidentellement sur *« Autoriser »* sur un site piégé, deux phénomènes se produisent :
1. **Browser Lock (Verrouillage de session)** : Une page malveillante bloque le focus du navigateur et se relance automatiquement à chaque redémarrage grâce à la restauration de session après crash.
2. **Scamware par Web Push (Fausses alertes Windows Defender / McAfee / Norton)** : Le site enregistre un **Service Worker** en arrière-plan (dans `Service Worker` et `WebStorage`) ainsi qu'un **canal Windows Push Notification (`WNS`)** dans `wpndatabase.db` et dans le Registre Windows. Résultat : même navigateur fermé, le service système `WpnUserService` et `PushNotificationsLongRunningTask.exe` bombardent l'écran de fausses fenêtres d'alerte virus qui réapparaissent dès qu'on les ferme.

## ✨ Fonctionnalités

- **Arrêt forcé des navigateurs et processus d'arrière-plan** (`msedge.exe`, `msedgewebview2.exe`, `chrome.exe`, `firefox.exe`, `brave.exe`, `opera.exe`).
- **Suppression des sessions corrompues** (`Sessions`, `Session Storage`, `sessionstore.jsonlz4`) sur **tous les profils utilisateurs** (`Default`, `Profile 1`, etc.) pour empêcher la réouverture des onglets pièges.
- **Destruction complète des Service Workers** :
  - Purge des dossiers `Service Worker`, `WebStorage` (*Storage Buckets* des versions récentes d'Edge/Chrome), `GCM Store`, `Notifications`, `Platform Notifications` et `IndexedDB`.
  - Suppression de `serviceworker.txt` et révocation des permissions `desktop-notification` dans `permissions.sqlite` sur Firefox.
- **Verrouillage des préférences Chromium (`Preferences` & `Secure Preferences`)** :
  - Bascule tous les sites autorisés sur **`setting = 2` (Bloqué)** afin que la synchronisation cloud du navigateur ne puisse pas réactiver les notifications frauduleuses.
  - Désactive l'exécution en arrière-plan (`background_mode.enabled = false`) et réinitialise l'état de fermeture (`exit_type = "Normal"`) pour supprimer la bannière *« Restaurer les pages »*.
- **Neutralisation du cache Windows Push Notification (`WNS`)** :
  - Supprime les clés de registre Web Push sous `HKCU\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings`.
  - Redémarre proprement `WpnUserService_*` et `PushNotificationsLongRunningTask.exe` pour vider les fausses alertes maintenues en mémoire vive (RAM).
  - Nettoie la base SQLite `%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db` (`Notification`, `NotificationHandler`, `HandlerSettings`, `HandlerAssets`, `WNSPushChannel`) et rafraîchit `ShellExperienceHost.exe` pour fermer immédiatement les fenêtres à l'écran.

## 🚀 Utilisation rapide

### Option 1 — Exécutable autonome (`.exe` / itch.io / GitHub Releases)
1. Téléchargez **`WebBrowserCleanup.exe`** (ou l'archive `.zip`).
2. Double-cliquez sur **`WebBrowserCleanup.exe`** (ou **`Lancer_Nettoyage.bat`**).
3. Vos navigateurs vont se fermer et les fausses alertes disparaîtront en quelques secondes.

### Option 2 — Avec Python (Code source)
Aucune bibliothèque tierce (`pip`) n'est requise (utilise uniquement la bibliothèque standard Python) :

```powershell
python Cleanup.py
```

Pour une exécution silencieuse / automatisée sans pause finale :
```powershell
python Cleanup.py --no-pause
```

## 📦 Compilation en `.exe` (pour GitHub Releases & itch.io)

Un script de build clé en main est fourni pour générer l'exécutable Windows autonome (`WebBrowserCleanup.exe`) et créer l'archive `.zip` prête à être publiée sur **itch.io** et **GitHub** :

```powershell
.\build_release.bat
```

Le script génère :
- `dist\WebBrowserCleanup.exe` : exécutable unique portable.
- `dist\WebBrowserCleanup_Windows.zip` : archive contenant l'exécutable, le manifeste `.itch.toml`, le `README.md` et la `LICENSE`.

## 🌐 Navigateurs supportés

| Navigateur | Sessions | Service Workers & WebStorage | Permissions Push |
| :--- | :---: | :---: | :---: |
| **Microsoft Edge** | ✅ | ✅ | ✅ (+ Canaux WNS Windows) |
| **Google Chrome** | ✅ | ✅ | ✅ |
| **Brave Browser** | ✅ | ✅ | ✅ |
| **Opera / Opera GX** | ✅ | ✅ | ✅ |
| **Mozilla Firefox** | ✅ | ✅ | ✅ (`permissions.sqlite`) |

---

# 🇬🇧 English Version

**WebBrowserCleanup** is a lightweight, zero-dependency utility designed to instantly unlock a PC stuck in a **Browser Lock** (fullscreen tech-support scam traps) and completely eradicate **fake virus alerts (Web Push Notification Scamware / Scareware)** that persist on Windows even when the browser is closed.

## 🚨 What problem does this tool solve?

When a user accidentally clicks *"Allow"* on a deceptive website, two things happen:
1. **Browser Lock (Session Hijacking)**: A malicious webpage traps the browser focus and automatically reopens on every browser restart via crash session recovery.
2. **Web Push Scamware (Fake Windows Defender / McAfee / Norton Popups)**: The website registers a background **Service Worker** (inside `Service Worker` and `WebStorage` buckets) along with a native **Windows Push Notification (`WNS`) channel** in `wpndatabase.db` and the Windows Registry. As a result, even with the browser completely closed, the Windows `WpnUserService` service and `PushNotificationsLongRunningTask.exe` flood the desktop with fake virus alerts that immediately respawn as soon as they are dismissed.

## ✨ Key Features

- **Force-kills browsers and background processes** (`msedge.exe`, `msedgewebview2.exe`, `chrome.exe`, `firefox.exe`, `brave.exe`, `opera.exe`).
- **Wipes corrupted crash sessions** (`Sessions`, `Session Storage`, `sessionstore.jsonlz4`) across **all user profiles** (`Default`, `Profile 1`, custom profiles) to prevent scam tabs from reopening.
- **Complete Service Worker eradication**:
  - Purges `Service Worker`, `WebStorage` (modern Edge/Chrome *Storage Buckets*), `GCM Store`, `Notifications`, `Platform Notifications`, and `IndexedDB` folders.
  - Removes `serviceworker.txt` and revokes `desktop-notification` permissions inside `permissions.sqlite` for Mozilla Firefox.
- **Hardens Chromium preferences (`Preferences` & `Secure Preferences`)**:
  - Switches all existing notification permissions to **`setting = 2` (Blocked)** rather than merely deleting them, preventing cloud sync from restoring malicious permissions.
  - Disables background execution (`background_mode.enabled = false`) and resets crash flags (`exit_type = "Normal"`) to suppress the *"Restore pages?"* prompt.
- **Neutralizes the Windows Push Notification (`WNS`) cache**:
  - Removes Web Push registry keys under `HKCU\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings`.
  - Cleanly stops and restarts `WpnUserService_*` and `PushNotificationsLongRunningTask.exe` to flush fake alerts held in RAM.
  - Purges the Windows SQLite notification database `%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db` (`Notification`, `NotificationHandler`, `HandlerSettings`, `HandlerAssets`, `WNSPushChannel`) and refreshes `ShellExperienceHost.exe` to immediately close on-screen popup banners.

## 🚀 Quick Start

### Option 1 — Standalone Executable (`.exe` / itch.io / GitHub Releases)
1. Download **`WebBrowserCleanup.exe`** (or the `.zip` archive).
2. Double-click **`WebBrowserCleanup.exe`** (or **`Lancer_Nettoyage.bat`**).
3. Your browsers will close and all fake virus notifications will disappear within seconds.

### Option 2 — From Python Source
No third-party `pip` packages are required (uses Python's standard library only):

```powershell
python Cleanup.py
```

For silent/automated execution without the final prompt:
```powershell
python Cleanup.py --no-pause
```

## 📦 Building the `.exe` Release (for GitHub Releases & itch.io)

Run the included build script to compile the standalone Windows executable (`WebBrowserCleanup.exe`) and package the ready-to-upload `.zip` archive for **itch.io** and **GitHub**:

```powershell
.\build_release.bat
```

Output files:
- `dist\WebBrowserCleanup.exe`: Single-file portable executable.
- `dist\WebBrowserCleanup_Windows.zip`: Release archive containing the executable, `.itch.toml` manifest, `README.md`, and `LICENSE`.

## 🌐 Supported Browsers

| Browser | Session Recovery Cleanup | Service Workers & WebStorage | Push Permissions |
| :--- | :---: | :---: | :---: |
| **Microsoft Edge** | ✅ | ✅ | ✅ (+ Windows WNS Channels) |
| **Google Chrome** | ✅ | ✅ | ✅ |
| **Brave Browser** | ✅ | ✅ | ✅ |
| **Opera / Opera GX** | ✅ | ✅ | ✅ |
| **Mozilla Firefox** | ✅ | ✅ | ✅ (`permissions.sqlite`) |

---

## 📄 License / Licence

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
