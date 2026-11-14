import os
import sys
import stat
import re
import platform
import time
import shutil
import glob
import json
import sqlite3
import subprocess
try:
    import winreg
except ImportError:
    winreg = None

def remove_readonly(func, path, _):
    """Gestionnaire d'erreur pour shutil.rmtree : retire l'attribut lecture seule et réessaie."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def force_rmtree(path):
    """Supprime récursivement un dossier même s'il contient des fichiers en lecture seule."""
    if os.path.exists(path):
        shutil.rmtree(path, onerror=remove_readonly)


def kill_browsers():
    """
    Identifie le système d'exploitation et force la fermeture des navigateurs web 
    les plus courants (y compris leurs processus en arrière-plan qui affichent 
    les notifications push frauduleuses et relancent les Service Workers).
    """
    system = platform.system()
    
    # Liste complète des exécutables de navigateurs et processus d'arrière-plan pour Windows
    browsers_windows = [
        "msedge.exe", "msedgewebview2.exe", "MicrosoftEdgeUpdate.exe",
        "chrome.exe", "firefox.exe", "brave.exe", "opera.exe"
    ]
    
    # Liste des noms de processus pour Linux / macOS
    browsers_unix = ["chrome", "firefox", "msedge", "brave", "opera", "Google Chrome"]

    print("[*] Fermeture forcée des navigateurs et processus d'arrière-plan...")

    if system == "Windows":
        for browser in browsers_windows:
            os.system(f'taskkill /F /IM {browser} /T >nul 2>&1')
            
    elif system in ["Linux", "Darwin"]:
        for browser in browsers_unix:
            os.system(f'killall -9 "{browser}" > /dev/null 2>&1')
            
    else:
        print("[-] Système d'exploitation non reconnu pour la fermeture forcée.")

    print("[+] Processus de navigateurs terminés.")


def get_chromium_profiles():
    """
    Retourne la liste de tous les dossiers de profils existants (Default, Profile 1, ou noms personnalisés)
    pour les navigateurs basés sur Chromium sous Windows en cherchant tous les fichiers 'Preferences'.
    """
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    app_data = os.environ.get('APPDATA', '')
    profiles = []

    if local_app_data:
        chromium_user_data = {
            "Edge": os.path.join(local_app_data, "Microsoft", "Edge", "User Data"),
            "Chrome": os.path.join(local_app_data, "Google", "Chrome", "User Data"),
            "Brave": os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "User Data"),
        }
        for browser, base_path in chromium_user_data.items():
            if os.path.exists(base_path):
                for prefs_path in glob.glob(os.path.join(base_path, "*", "Preferences")):
                    prof_dir = os.path.dirname(prefs_path)
                    if os.path.isdir(prof_dir):
                        profiles.append((browser, prof_dir))

    if app_data:
        opera_paths = {
            "Opera": os.path.join(app_data, "Opera Software", "Opera Stable"),
            "Opera GX": os.path.join(app_data, "Opera Software", "Opera GX Stable"),
        }
        for browser, path in opera_paths.items():
            if os.path.exists(path):
                profiles.append((browser, path))

    return profiles


def clean_sessions_windows():
    """
    Supprime les fichiers de session de restauration sous Windows.
    Étape cruciale pour empêcher le navigateur de relancer la page bloquante
    lorsqu'il tente de "restaurer la session après un crash".
    """
    if platform.system() != "Windows":
        print("[!] Le nettoyage automatisé dans ce script est configuré pour Windows.")
        return

    print("[*] Nettoyage des fichiers de restauration de session...")

    for browser, profile_path in get_chromium_profiles():
        for folder_name in ["Sessions", "Session Storage"]:
            session_dir = os.path.join(profile_path, folder_name)
            if os.path.exists(session_dir):
                try:
                    force_rmtree(session_dir)
                    print(f"[+] {folder_name} {browser} ({os.path.basename(profile_path)}) supprimé.")
                except Exception as e:
                    print(f"[-] Impossible de nettoyer {folder_name} pour {browser} : {e}")

    # Nettoyage spécifique pour Firefox
    app_data = os.environ.get('APPDATA', '')
    if app_data:
        firefox_profiles_path = os.path.join(app_data, "Mozilla", "Firefox", "Profiles")
        if os.path.exists(firefox_profiles_path):
            for profile in glob.glob(os.path.join(firefox_profiles_path, "*")):
                session_file = os.path.join(profile, "sessionstore.jsonlz4")
                session_backups = os.path.join(profile, "sessionstore-backups")
                
                if os.path.exists(session_file):
                    try:
                        os.remove(session_file)
                        print(f"[+] Fichier de session Firefox supprimé : {os.path.basename(profile)}")
                    except Exception as e:
                        print(f"[-] Erreur de suppression fichier Firefox : {e}")
                
                if os.path.exists(session_backups):
                    try:
                        force_rmtree(session_backups)
                        print(f"[+] Sauvegardes de session Firefox supprimées : {os.path.basename(profile)}")
                    except Exception as e:
                        print(f"[-] Erreur de suppression des backups Firefox : {e}")


def clean_scam_notifications_windows():
    """
    Éradique les fausses alertes virus (Scamware / Adware par Web Push Notifications) :
    1. Supprime les Service Workers classiques ET ceux stockés dans WebStorage (Storage Buckets d'Edge/Chrome récents).
    2. Supprime GCM Store, Notifications, IndexedDB des sites malveillants.
    3. Passe toutes les permissions de notifications existantes sur BLOQUER (setting = 2) au lieu de simplement
       les vider (ce qui empêche la synchronisation Edge/Chrome de les réactiver), et coupe le mode arrière-plan.
    """
    if platform.system() != "Windows":
        return

    print("[*] Éradication des Service Workers (y compris WebStorage) et blocage des notifications...")

    # Dossiers contenant les Service Workers, abonnements Push et bases de données des sites
    # Note : "WebStorage" est crucial sur les versions récentes d'Edge/Chrome où les Service Workers
    # sont isolés dans WebStorage/<bucket_id>/Service Worker !
    folders_to_wipe = [
        "Service Worker",
        "WebStorage",
        "GCM Store",
        "Notifications",
        "Platform Notifications",
        "IndexedDB"
    ]

    for browser, profile_path in get_chromium_profiles():
        prof_name = os.path.basename(profile_path)

        # Suppression des dossiers de Service Workers et de notifications push
        for folder in folders_to_wipe:
            target = os.path.join(profile_path, folder)
            if os.path.exists(target):
                try:
                    force_rmtree(target)
                    print(f"[+] Dossier '{folder}' purgé pour {browser} ({prof_name}).")
                except Exception as e:
                    print(f"[-] Impossible de supprimer {folder} sur {browser} ({prof_name}) : {e}")

        # Nettoyage et blocage strict dans Preferences ET Secure Preferences
        for pref_filename in ["Preferences", "Secure Preferences"]:
            prefs_file = os.path.join(profile_path, pref_filename)
            if os.path.exists(prefs_file):
                try:
                    with open(prefs_file, "r", encoding="utf-8") as f:
                        prefs_data = json.load(f)

                    modified = False

                    # 1. Supprimer la table des identifiants d'abonnements Web Push (push_messaging_application_id_map)
                    if "push_messaging_application_id_map" in prefs_data:
                        prefs_data["push_messaging_application_id_map"] = {}
                        modified = True

                    # 2. Désactiver l'exécution en arrière-plan du navigateur (empêche le Service Worker de tourner navigateur fermé)
                    if "background_mode" not in prefs_data or not isinstance(prefs_data.get("background_mode"), dict):
                        prefs_data["background_mode"] = {}
                    if prefs_data["background_mode"].get("enabled") is not False:
                        prefs_data["background_mode"]["enabled"] = False
                        modified = True

                    if "profile" in prefs_data and isinstance(prefs_data["profile"], dict):
                        prof_dict = prefs_data["profile"]

                        if "push_messaging_application_id_map" in prof_dict:
                            prof_dict["push_messaging_application_id_map"] = {}
                            modified = True

                        # 3. Forcer le blocage par défaut des notifications (2 = Bloquer)
                        if "default_content_setting_values" not in prof_dict or not isinstance(prof_dict.get("default_content_setting_values"), dict):
                            prof_dict["default_content_setting_values"] = {}
                        if prof_dict["default_content_setting_values"].get("notifications") != 2:
                            prof_dict["default_content_setting_values"]["notifications"] = 2
                            modified = True

                        # 4. Basculer chaque site autorisé dans 'notifications' sur setting = 2 (BLOQUÉ)
                        # (Plutôt que de supprimer la clé, mettre setting=2 écrase la synchronisation cloud)
                        exceptions = prof_dict.get("content_settings", {}).get("exceptions", {})
                        if isinstance(exceptions, dict):
                            if "notifications" in exceptions and isinstance(exceptions["notifications"], dict):
                                blocked_count = 0
                                for site_pattern, site_val in list(exceptions["notifications"].items()):
                                    if isinstance(site_val, dict) and site_val.get("setting") != 2:
                                        site_val["setting"] = 2
                                        blocked_count += 1
                                        modified = True
                                if blocked_count > 0:
                                    print(f"[+] {blocked_count} site(s) bloqué(s) définitivement pour les notifications dans {browser} ({prof_name} - {pref_filename}).")

                            for setting_key in [
                                "popups", "automatic_downloads", "background_sync",
                                "periodic_background_sync", "notification_interactions",
                                "notification_scheduler", "app_banner"
                            ]:
                                if setting_key in exceptions and exceptions[setting_key]:
                                    exceptions[setting_key] = {}
                                    modified = True

                        # 5. Empêcher le navigateur de proposer "Restaurer les pages" après le taskkill
                        if prof_dict.get("exit_type") != "Normal":
                            prof_dict["exit_type"] = "Normal"
                            modified = True
                        if prof_dict.get("exited_cleanly") is not True:
                            prof_dict["exited_cleanly"] = True
                            modified = True

                    # Supprimer les signatures HMAC associées dans Secure Preferences pour que Chromium accepte nos modifications
                    macs = prefs_data.get("protection", {}).get("macs", {})
                    if isinstance(macs, dict):
                        macs.pop("background_mode", None)
                        macs.pop("push_messaging_application_id_map", None)
                        prof_macs = macs.get("profile", {})
                        if isinstance(prof_macs, dict):
                            prof_macs.pop("default_content_setting_values", None)
                            prof_macs.pop("push_messaging_application_id_map", None)
                            exc_macs = prof_macs.get("content_settings", {}).get("exceptions", {})
                            if isinstance(exc_macs, dict):
                                for k in [
                                    "notifications", "popups", "automatic_downloads",
                                    "background_sync", "periodic_background_sync",
                                    "notification_interactions", "notification_scheduler", "app_banner"
                                ]:
                                    exc_macs.pop(k, None)

                    if modified:
                        with open(prefs_file, "w", encoding="utf-8") as f:
                            json.dump(prefs_data, f, ensure_ascii=False)
                        print(f"[+] Fichier {pref_filename} verrouillé contre le spam pour {browser} ({prof_name}).")

                except Exception as e:
                    print(f"[-] Impossible de modifier {pref_filename} pour {browser} ({prof_name}) : {e}")

    # Nettoyage des notifications et Service Workers pour Firefox
    app_data = os.environ.get('APPDATA', '')
    if app_data:
        firefox_profiles_path = os.path.join(app_data, "Mozilla", "Firefox", "Profiles")
        if os.path.exists(firefox_profiles_path):
            for profile in glob.glob(os.path.join(firefox_profiles_path, "*")):
                prof_name = os.path.basename(profile)

                sw_file = os.path.join(profile, "serviceworker.txt")
                if os.path.exists(sw_file):
                    try:
                        os.remove(sw_file)
                        print(f"[+] Service Workers Firefox supprimés ({prof_name}).")
                    except Exception as e:
                        print(f"[-] Erreur suppression serviceworker.txt Firefox : {e}")

                perms_db = os.path.join(profile, "permissions.sqlite")
                if os.path.exists(perms_db):
                    try:
                        conn = sqlite3.connect(perms_db)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM moz_perms WHERE type = 'desktop-notification'")
                        deleted = cursor.rowcount
                        conn.commit()
                        conn.close()
                        if deleted > 0:
                            print(f"[+] {deleted} permission(s) de notification Firefox révoquée(s) ({prof_name}).")
                    except Exception as e:
                        print(f"[-] Erreur nettoyage permissions.sqlite Firefox : {e}")


def clear_windows_toast_notifications():
    """
    Éradique les notifications Windows en cours d'affichage et empêche leur réapparition :
    1. Désactive et supprime les clés de registre Windows associées aux notifications Web Push (HKCU\\...\\Notifications\\Settings).
    2. Arrête le processus PushNotificationsLongRunningTask.exe et le service utilisateur WpnUserService_*
       (qui gardent les fausses alertes en mémoire vive et les réaffichent dès que ShellExperienceHost redémarre).
    3. Purge la base SQLite wpndatabase.db (tables Notification ET NotificationHandler/WNSPushChannel des sites web).
    4. Redémarre ShellExperienceHost.exe pour fermer immédiatement les fenêtres à l'écran.
    """
    if platform.system() != "Windows":
        return

    print("[*] Neutralisation du service de notifications Push Windows et fermeture des fenêtres...")

    # S'assurer qu'aucun navigateur ne tourne en arrière-plan
    os.system('taskkill /F /IM msedge.exe /T >nul 2>&1')
    os.system('taskkill /F /IM chrome.exe /T >nul 2>&1')

    # 1. Nettoyage du Registre Windows (HKCU\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings)
    if winreg is not None:
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"
        try:
            parent_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ | winreg.KEY_WRITE)
            subkeys_to_remove = []
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(parent_key, i)
                    if "http://" in sub.lower() or "https://" in sub.lower():
                        subkeys_to_remove.append(sub)
                    i += 1
                except OSError:
                    break

            for sub in subkeys_to_remove:
                try:
                    # Désactiver d'abord la clé au cas où Windows la relirait avant suppression
                    sub_k = winreg.OpenKey(parent_key, sub, 0, winreg.KEY_WRITE)
                    winreg.SetValueEx(sub_k, "Enabled", 0, winreg.REG_DWORD, 0)
                    winreg.CloseKey(sub_k)
                    winreg.DeleteKey(parent_key, sub)
                    print(f"[+] Clé de registre de notification supprimée : {sub}")
                except Exception:
                    pass
            winreg.CloseKey(parent_key)
        except Exception as e:
            print(f"[!] Info registre notifications : {e}")

    # 2. Tuer PushNotificationsLongRunningTask.exe et arrêter WpnUserService_* (qui garde les fenêtres en RAM !)
    os.system("taskkill /F /IM PushNotificationsLongRunningTask.exe >nul 2>&1")

    wpn_service_names = []
    wpn_pids = []
    try:
        out_svc = subprocess.check_output(
            ["sc", "queryex", "type=", "service", "state=", "all"],
            text=True, errors="ignore"
        )
        for block in out_svc.split("\n\n"):
            if "wpnuserservice_" in block.lower():
                m_name = re.search(r"SERVICE_NAME:\s*(\S+)", block)
                m_pid = re.search(r"PID\s*:\s*(\d+)", block)
                if m_name:
                    wpn_service_names.append(m_name.group(1))
                if m_pid and int(m_pid.group(1)) > 0:
                    wpn_pids.append(int(m_pid.group(1)))
    except Exception:
        pass

    for svc_name in wpn_service_names:
        os.system(f'net stop "{svc_name}" /Y >nul 2>&1')
    for pid in wpn_pids:
        os.system(f'taskkill /F /PID {pid} >nul 2>&1')

    time.sleep(0.5)

    # 3. Purge complète de wpndatabase.db pendant que WpnUserService est coupé
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    wpn_dir = os.path.join(local_app_data, "Microsoft", "Windows", "Notifications")
    wpn_db = os.path.join(wpn_dir, "wpndatabase.db")

    if local_app_data and os.path.exists(wpn_db):
        try:
            conn = sqlite3.connect(wpn_db)
            cursor = conn.cursor()

            # Vider toutes les notifications actives ou programmées
            for table in ["Notification", "NotificationData", "TransientTable", "TimedNotification"]:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                except Exception:
                    pass

            # Identifier tous les NotificationHandler liés à des sites web (Web Push)
            cursor.execute(
                "SELECT RecordId, PrimaryId FROM NotificationHandler "
                "WHERE PrimaryId LIKE '%http://%' OR PrimaryId LIKE '%https://%'"
            )
            web_handlers = cursor.fetchall()

            for record_id, primary_id in web_handlers:
                # Désactiver les bannières/toasts puis supprimer le handler web et son canal WNS
                cursor.execute("DELETE FROM HandlerSettings WHERE HandlerId = ?", (record_id,))
                cursor.execute("DELETE FROM HandlerAssets WHERE HandlerId = ?", (record_id,))
                cursor.execute("DELETE FROM WNSPushChannel WHERE HandlerId = ?", (record_id,))
                cursor.execute("DELETE FROM NotificationHandler WHERE RecordId = ?", (record_id,))
                print(f"[+] Canal Push Windows supprimé de wpndatabase.db : {primary_id}")

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Info base de notifications Windows : {e}")

        # Supprimer les fichiers d'icônes de notifications Web (ToastCollectionIcons)
        icons_dir = os.path.join(local_app_data, "Microsoft", "Windows", "Notifications", "ToastCollectionIcons")
        if os.path.exists(icons_dir):
            force_rmtree(icons_dir)

    # 4. Fermer les fenêtres de notifications affichées à l'écran en redémarrant ShellExperienceHost
    os.system("taskkill /F /IM ShellExperienceHost.exe >nul 2>&1")
    os.system("taskkill /F /IM PushNotificationsLongRunningTask.exe >nul 2>&1")

    # Relancer proprement le service utilisateur de notifications maintenant que la base est saine
    for svc_name in wpn_service_names:
        os.system(f'net start "{svc_name}" >nul 2>&1')

    print("[+] Fenêtres de notifications Windows et processus Push nettoyés.")


if __name__ == "__main__":
    print("===================================================")
    print("   Nettoyeur Anti-Scamware / Push & Browser Lock   ")
    print("===================================================")
    
    # 1. Fermeture des navigateurs et processus en arrière-plan
    kill_browsers()
    
    # Pause pour libérer les verrous de fichiers
    time.sleep(1.5)
    
    # 2. Suppression des sessions (onglets malveillants)
    clean_sessions_windows()
    
    # 3. Suppression des Service Workers (y compris WebStorage) et blocage des notifications
    clean_scam_notifications_windows()
    
    # 4. Effacement des notifications Windows affichées à l'écran
    clear_windows_toast_notifications()
    
    print("===================================================")
    print("[+] Opération terminée. Les fausses alertes et sessions ont été éradiquées.")
    print("===================================================")

