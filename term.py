import os
import sys
import json
import time
import random
import socket
import platform
import secrets
import string
import ast
import operator
import subprocess
import base64
import hashlib
import shutil
import threading
import cowsay
import psutil
import pyperclip

from pathlib import Path
from datetime import datetime
from getpass import getpass

from cryptography.fernet import Fernet, InvalidToken

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box
from pyfiglet import figlet_format


# =========================================================
# CONFIGURATION
# =========================================================

VERSION = "5.0"

DATA_DIR = Path.home() / ".dark_terminal"

VAULT_FILE = DATA_DIR / "vault.json"
NOTES_FILE = DATA_DIR / "notes.json"
LOG_FILE = DATA_DIR / "activity.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

console = Console()

vault = []
notes = []
logs = []

fernet = None
salt_storage = None

THEMES = {
    "1": ("green", "VERT MATRIX"),
    "2": ("red", "RED HACKER"),
    "3": ("cyan", "CYBER BLUE"),
    "4": ("magenta", "PURPLE NIGHT"),
    "5": ("yellow", "GOLD SYSTEM")
}

THEME = "green"


# =========================================================
# UTILITAIRES
# =========================================================

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nAppuie sur Entrée pour continuer...")


def log(message):
    global logs

    entry = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "message": message
    }

    logs.append(entry)

    logs = logs[-1000:]

    try:
        LOG_FILE.write_text(
            json.dumps(logs, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )
    except OSError:
        pass


def load_logs():
    global logs

    if LOG_FILE.exists():
        try:
            logs = json.loads(
                LOG_FILE.read_text(encoding="utf-8")
            )
        except (ValueError, OSError):
            logs = []


def panel(content, title="DARK TERMINAL"):
    console.print(
        Panel(
            content,
            title=f"[bold {THEME}]{title}[/bold {THEME}]",
            border_style=THEME,
            box=box.ROUNDED
        )
    )


def banner():
    title = figlet_format("DARK NET", font="slant")

    console.print(
        Panel(
            f"[bold {THEME}]{title}[/bold {THEME}]\n"
            f"[cyan]ULTIMATE CYBERPUNK TERMINAL V{VERSION}[/cyan]\n"
            f"[dim]SYSTEM ONLINE[/dim]",
            border_style=THEME,
            box=box.DOUBLE
        )
    )


def loading(message, duration=1.5):
    with Progress(
        TextColumn(f"[bold {THEME}]{{task.description}}"),
        BarColumn(bar_width=35),
        TextColumn("[cyan]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:

        task = progress.add_task(message, total=100)

        while not progress.finished:
            progress.update(
                task,
                advance=random.randint(4, 12)
            )
            time.sleep(duration / 15)


def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


# =========================================================
# COFFRE DE MOTS DE PASSE CHIFFRE
# COMPATIBLE AVEC LA VERSION V4
# =========================================================

def derive_key(password, salt):

    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        600000,
        dklen=32
    )

    return base64.urlsafe_b64encode(key)


def save_vault():

    global vault, fernet

    encrypted = fernet.encrypt(
        json.dumps(vault, ensure_ascii=False).encode("utf-8")
    )

    data = {
        "salt": salt_storage.hex(),
        "data": encrypted.decode()
    }

    VAULT_FILE.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )

    try:
        VAULT_FILE.chmod(0o600)
    except OSError:
        pass


def unlock_vault():

    global vault, fernet, salt_storage

    clear()
    banner()

    if not VAULT_FILE.exists():

        panel(
            "[bold green]CRÉATION DU COFFRE SÉCURISÉ[/bold green]\n"
            "[cyan]Choisis ton mot de passe maître.[/cyan]"
        )

        while True:

            password = getpass("Mot de passe maître : ")

            if len(password) < 12:
                console.print(
                    "[red]Minimum 12 caractères.[/red]"
                )
                continue

            confirmation = getpass("Confirme : ")

            if password != confirmation:
                console.print("[red]Les mots de passe diffèrent.[/red]")
                continue

            break

        salt_storage = secrets.token_bytes(16)

        fernet = Fernet(
            derive_key(password, salt_storage)
        )

        vault = []

        save_vault()

        console.print("[bold green]COFFRE CRÉÉ ![/bold green]")

        time.sleep(1)

        return True

    data = json.loads(
        VAULT_FILE.read_text(encoding="utf-8")
    )

    salt_storage = bytes.fromhex(data["salt"])

    for attempt in range(3):

        password = getpass("Mot de passe maître : ")

        candidate = Fernet(
            derive_key(password, salt_storage)
        )

        try:

            decrypted = candidate.decrypt(
                data["data"].encode()
            )

            vault = json.loads(decrypted.decode())

            fernet = candidate

            console.print(
                "[bold green]COFFRE DÉVERROUILLÉ ![/bold green]"
            )

            time.sleep(1)

            return True

        except InvalidToken:

            console.print(
                "[bold red]Mot de passe incorrect ![/bold red]"
            )

    return False


# =========================================================
# GENERATEUR DE MOTS DE PASSE
# =========================================================

def generate_password():

    clear()

    panel(
        "[bold green]SECURE PASSWORD GENERATOR[/bold green]"
    )

    length = IntPrompt.ask(
        "Longueur",
        default=24
    )

    if not 8 <= length <= 128:
        console.print("[red]Longueur invalide.[/red]")
        return

    letters = string.ascii_letters
    digits = string.digits
    symbols = "!@#$%^&*()-_=+"

    password_chars = [
        secrets.choice(letters),
        secrets.choice(digits),
        secrets.choice(symbols)
    ]

    alphabet = letters + digits + symbols

    password_chars.extend(
        secrets.choice(alphabet)
        for _ in range(length - 3)
    )

    secrets.SystemRandom().shuffle(password_chars)

    password = "".join(password_chars)

    console.print(
        Panel(
            f"[bold green]{password}[/bold green]",
            title="PASSWORD GENERATED",
            border_style="green"
        )
    )

    if Confirm.ask("Enregistrer ce mot de passe ?"):

        label = Prompt.ask("Libellé")

        if not label.strip():
            label = "Sans libellé"

        entry = {
            "id": secrets.token_hex(8),
            "label": label,
            "password": password,
            "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }

        vault.append(entry)
        save_vault()

        console.print(
            "[bold green]Mot de passe sauvegardé ![/bold green]"
        )

        log(f"Mot de passe créé : {label}")


# =========================================================
# HISTORIQUE DES MOTS DE PASSE
# =========================================================

def password_history():

    clear()

    table = Table(
        title="PASSWORD HISTORY",
        box=box.ROUNDED,
        border_style=THEME
    )

    table.add_column("N°", style="yellow")
    table.add_column("LIBELLÉ", style="cyan")
    table.add_column("MOT DE PASSE", style="green")
    table.add_column("DATE", style="dim")

    for i, entry in enumerate(vault, 1):

        masked = "*" * min(
            len(entry["password"]),
            25
        )

        table.add_row(
            str(i),
            entry["label"],
            masked,
            entry["date"]
        )

    console.print(table)

    console.print(
        f"\n[bold green]Total : {len(vault)} mots de passe[/bold green]"
    )


def select_password():

    if not vault:
        console.print("[yellow]Coffre vide.[/yellow]")
        return None

    password_history()

    choice = IntPrompt.ask("Numéro")

    if not 1 <= choice <= len(vault):
        console.print("[red]Numéro invalide.[/red]")
        return None

    return choice - 1


def reveal_password():

    clear()

    index = select_password()

    if index is None:
        return

    entry = vault[index]

    panel(
        f"[cyan]Libellé :[/cyan] {entry['label']}\n"
        f"[green]Mot de passe :[/green] {entry['password']}\n"
        f"[dim]Date : {entry['date']}[/dim]",
        "PASSWORD DETAILS"
    )

    log(f"Mot de passe consulté : {entry['label']}")


def copy_password():

    clear()

    index = select_password()

    if index is None:
        return

    try:

        pyperclip.copy(
            vault[index]["password"]
        )

        console.print(
            "[bold green]Mot de passe copié ![/bold green]"
        )

        log("Mot de passe copié")

    except Exception:

        console.print(
            "[red]Presse-papiers indisponible.[/red]"
        )


def edit_password():

    clear()

    index = select_password()

    if index is None:
        return

    entry = vault[index]

    console.print(
        f"[cyan]Libellé actuel : {entry['label']}[/cyan]"
    )

    new_label = Prompt.ask(
        "Nouveau libellé",
        default=entry["label"]
    )

    if new_label.strip():
        entry["label"] = new_label

    if Confirm.ask("Modifier également le mot de passe ?"):

        new_password = getpass("Nouveau mot de passe : ")

        if new_password:
            entry["password"] = new_password

    save_vault()

    console.print("[green]Modification enregistrée ![/green]")

    log("Mot de passe modifié")


def search_password():

    clear()

    query = Prompt.ask(
        "Recherche par libellé"
    ).lower()

    results = [
        entry for entry in vault
        if query in entry["label"].lower()
    ]

    table = Table(title="SEARCH RESULTS")

    table.add_column("LIBELLÉ", style="cyan")
    table.add_column("DATE", style="dim")

    for entry in results:

        table.add_row(
            entry["label"],
            entry["date"]
        )

    console.print(table)

    if not results:
        console.print("[yellow]Aucun résultat.[/yellow]")


def delete_password():

    clear()

    index = select_password()

    if index is None:
        return

    label = vault[index]["label"]

    if Confirm.ask(f"Supprimer {label} ?"):

        vault.pop(index)

        save_vault()

        console.print("[green]Mot de passe supprimé.[/green]")

        log(f"Mot de passe supprimé : {label}")


def clear_vault():

    if Confirm.ask(
        "[bold red]Supprimer TOUT le coffre ?[/bold red]",
        default=False
    ):

        vault.clear()

        save_vault()

        console.print("[green]Coffre vidé.[/green]")

        log("Coffre vidé")


def password_manager():

    while True:

        clear()

        panel(
            "[green]1.[/] Générer un mot de passe\n"
            "[green]2.[/] Historique\n"
            "[green]3.[/] Afficher un mot de passe\n"
            "[green]4.[/] Copier un mot de passe\n"
            "[green]5.[/] Rechercher\n"
            "[green]6.[/] Modifier un mot de passe\n"
            "[green]7.[/] Supprimer un mot de passe\n"
            "[red]8.[/] Vider le coffre\n"
            "[yellow]0.[/] Retour",
            "PASSWORD MANAGER"
        )

        choice = Prompt.ask("PASSWORD >")

        actions = {
            "1": generate_password,
            "2": password_history,
            "3": reveal_password,
            "4": copy_password,
            "5": search_password,
            "6": edit_password,
            "7": delete_password,
            "8": clear_vault
        }

        if choice == "0":
            break

        action = actions.get(choice)

        if action:
            action()
            pause()
        else:
            console.print("[red]Choix invalide.[/red]")


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():

    clear()

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(Path.home()))

    battery = psutil.sensors_battery()

    uptime = time.time() - psutil.boot_time()

    table = Table(
        title="SYSTEM DASHBOARD",
        border_style=THEME
    )

    table.add_column("INFORMATION", style="cyan")
    table.add_column("VALEUR", style="green")

    table.add_row("Machine", socket.gethostname())
    table.add_row("Utilisateur", os.getenv("USER", "Inconnu"))
    table.add_row("OS", platform.system())
    table.add_row("Version", platform.release())
    table.add_row("Python", platform.python_version())
    table.add_row("CPU", platform.processor() or "Non renseigné")
    table.add_row("Cœurs CPU", str(psutil.cpu_count()))
    table.add_row("CPU utilisé", f"{psutil.cpu_percent(interval=1)}%")
    table.add_row("RAM totale", f"{memory.total / 1024**3:.2f} GB")
    table.add_row("RAM utilisée", f"{memory.percent}%")
    table.add_row("Disque utilisé", f"{disk.percent}%")
    table.add_row("Mots de passe", str(len(vault)))
    table.add_row("Temps allumé", f"{uptime / 3600:.1f} heures")

    if battery:
        table.add_row("Batterie", f"{battery.percent}%")

    console.print(table)

    log("Dashboard consulté")


# =========================================================
# MONITEUR CPU / RAM
# =========================================================

def monitor():

    clear()

    panel(
        "[bold green]LIVE SYSTEM MONITOR[/bold green]\n"
        "[dim]CTRL+C pour arrêter[/dim]"
    )

    try:

        while True:

            clear()

            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage(str(Path.home()))

            table = Table(
                title="LIVE MONITOR",
                border_style=THEME
            )

            table.add_column("RESSOURCE", style="cyan")
            table.add_column("UTILISATION", style="green")

            table.add_row("CPU", f"{cpu}%")
            table.add_row("RAM", f"{ram.percent}%")
            table.add_row("DISQUE", f"{disk.percent}%")

            console.print(table)

            time.sleep(1)

    except KeyboardInterrupt:
        pass

    log("Moniteur utilisé")


# =========================================================
# GESTION DES PROCESSUS
# =========================================================

def process_manager():

    clear()

    table = Table(
        title="RUNNING PROCESSES",
        border_style=THEME
    )

    table.add_column("PID", style="yellow")
    table.add_column("NOM", style="cyan")
    table.add_column("RAM", style="green")

    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "memory_info"]
    ):

        try:

            info = process.info

            memory = info["memory_info"]

            ram = memory.rss / 1024**2 if memory else 0

            processes.append(
                (info["pid"], info["name"], ram)
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(
        key=lambda x: x[2],
        reverse=True
    )

    for pid, name, ram in processes[:30]:

        table.add_row(
            str(pid),
            str(name)[:35],
            f"{ram:.1f} MB"
        )

    console.print(table)

    console.print(
        "[dim]Affichage des 30 processus consommant le plus de RAM.[/dim]"
    )

    log("Liste des processus consultée")


# =========================================================
# INFORMATIONS RESEAU
# =========================================================

def network_info():

    clear()

    hostname = socket.gethostname()

    try:
        local_ip = socket.gethostbyname(hostname)
    except OSError:
        local_ip = "Indisponible"

    stats = psutil.net_io_counters()

    table = Table(
        title="NETWORK INFORMATION",
        border_style=THEME
    )

    table.add_column("INFORMATION", style="cyan")
    table.add_column("VALEUR", style="green")

    table.add_row("Hostname", hostname)
    table.add_row("IP locale", local_ip)

    table.add_row(
        "Données envoyées",
        f"{stats.bytes_sent / 1024**2:.2f} MB"
    )

    table.add_row(
        "Données reçues",
        f"{stats.bytes_recv / 1024**2:.2f} MB"
    )

    for interface, addresses in psutil.net_if_addrs().items():

        for address in addresses:

            if address.family == socket.AF_INET:

                table.add_row(
                    interface,
                    address.address
                )

    console.print(table)

    log("Informations réseau consultées")


# =========================================================
# EXPLORATEUR DE FICHIERS
# =========================================================

def file_explorer():

    current = Path.home()

    while True:

        clear()

        panel(
            f"[cyan]{current}[/cyan]",
            "FILE EXPLORER"
        )

        try:

            items = sorted(
                current.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower())
            )

        except (PermissionError, OSError) as error:

            console.print(f"[red]{error}[/red]")

            current = current.parent

            continue

        table = Table(box=box.SIMPLE)

        table.add_column("N°", style="yellow")
        table.add_column("TYPE", style="cyan")
        table.add_column("NOM", style="green")
        table.add_column("TAILLE", style="dim")

        for i, item in enumerate(items[:100], 1):

            try:

                kind = "DOSSIER" if item.is_dir() else "FICHIER"

                size = (
                    "-"
                    if item.is_dir()
                    else f"{item.stat().st_size / 1024:.1f} KB"
                )

                table.add_row(
                    str(i),
                    kind,
                    item.name,
                    size
                )

            except OSError:
                continue

        console.print(table)

        choice = Prompt.ask(
            "Numéro | .. pour remonter | q pour quitter"
        )

        if choice.lower() == "q":
            break

        if choice == "..":
            current = current.parent
            continue

        try:

            selected = items[int(choice) - 1]

            if selected.is_dir():
                current = selected
            else:
                console.print(
                    f"[yellow]Fichier sélectionné : {selected}[/yellow]"
                )

        except (ValueError, IndexError):
            console.print("[red]Choix invalide.[/red]")

        pause()

    log("Explorateur utilisé")


# =========================================================
# RECHERCHE DE FICHIERS
# =========================================================

def file_search():

    clear()

    root = Path(
        Prompt.ask(
            "Dossier à explorer",
            default=str(Path.home())
        )
    ).expanduser()

    query = Prompt.ask("Nom ou partie du nom")

    if not root.is_dir():
        console.print("[red]Dossier invalide.[/red]")
        return

    results = []

    console.print("[yellow]Recherche en cours...[/yellow]")

    def walk_error(error):
        console.print(f"[dim]Accès ignoré : {error}[/dim]")

    for directory, dirs, files in os.walk(
        root,
        onerror=walk_error
    ):

        dirs[:] = [
            d for d in dirs
            if d not in {".git", "__pycache__", "node_modules"}
        ]

        for name in files:

            if query.lower() in name.lower():

                results.append(
                    Path(directory) / name
                )

                if len(results) >= 100:
                    break

        if len(results) >= 100:
            break

    table = Table(title="SEARCH RESULTS")

    table.add_column("FICHIER", style="green")

    for result in results:
        table.add_row(str(result))

    console.print(table)

    console.print(
        f"[cyan]{len(results)} résultat(s)[/cyan]"
    )

    log("Recherche de fichiers effectuée")


# =========================================================
# CALCULATRICE SECURISEE
# =========================================================

def calculator():

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos
    }

    def calculate(node):

        if isinstance(node, ast.Expression):
            return calculate(node.body)

        if isinstance(node, ast.Constant):

            if type(node.value) in (int, float):
                return node.value

        if isinstance(node, ast.BinOp):

            if type(node.op) not in operators:
                raise ValueError("Opération interdite")

            left = calculate(node.left)
            right = calculate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exposant trop grand")

            result = operators[type(node.op)](left, right)

            if abs(result) > 10**100:
                raise ValueError("Résultat trop grand")

            return result

        if isinstance(node, ast.UnaryOp):

            if type(node.op) in operators:

                return operators[type(node.op)](
                    calculate(node.operand)
                )

        raise ValueError("Expression invalide")

    clear()

    panel(
        "Exemples : 10+5 | 20*3 | 100/4\n"
        "Tape q pour quitter.",
        "CALCULATOR"
    )

    while True:

        expression = input("CALCUL > ")

        if expression.lower() == "q":
            break

        try:

            tree = ast.parse(
                expression,
                mode="eval"
            )

            result = calculate(tree)

            console.print(
                f"[bold green]RÉSULTAT : {result}[/bold green]"
            )

        except Exception:

            console.print(
                "[red]Expression invalide.[/red]"
            )


# =========================================================
# NOTES PERSONNELLES
# =========================================================

def load_notes():

    global notes

    if NOTES_FILE.exists():

        try:

            notes = json.loads(
                NOTES_FILE.read_text(encoding="utf-8")
            )

        except (ValueError, OSError):
            notes = []


def save_notes():

    NOTES_FILE.write_text(
        json.dumps(
            notes,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    try:
        NOTES_FILE.chmod(0o600)
    except OSError:
        pass


def create_note():

    clear()

    title = Prompt.ask("Titre de la note")

    console.print(
        "[cyan]Écris ta note. Termine par une ligne contenant FIN.[/cyan]"
    )

    lines = []

    while True:

        line = input()

        if line == "FIN":
            break

        lines.append(line)

    note = {
        "title": title,
        "content": "\n".join(lines),
        "date": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    notes.append(note)

    save_notes()

    console.print("[green]Note enregistrée ![/green]")

    log(f"Note créée : {title}")


def show_notes():

    clear()

    if not notes:
        console.print("[yellow]Aucune note.[/yellow]")
        return

    table = Table(title="PERSONAL NOTES")

    table.add_column("N°", style="yellow")
    table.add_column("TITRE", style="cyan")
    table.add_column("DATE", style="dim")

    for i, note in enumerate(notes, 1):

        table.add_row(
            str(i),
            note["title"],
            note["date"]
        )

    console.print(table)

    choice = IntPrompt.ask("Numéro à consulter")

    if not 1 <= choice <= len(notes):
        return

    note = notes[choice - 1]

    panel(
        note["content"],
        note["title"]
    )


def delete_note():

    if not notes:
        console.print("[yellow]Aucune note.[/yellow]")
        return

    show_notes()

    choice = IntPrompt.ask("Numéro à supprimer")

    if 1 <= choice <= len(notes):

        if Confirm.ask("Confirmer la suppression ?"):

            notes.pop(choice - 1)

            save_notes()

            console.print("[green]Note supprimée.[/green]")


def notes_manager():

    while True:

        clear()

        panel(
            "[green]1.[/] Créer une note\n"
            "[green]2.[/] Consulter les notes\n"
            "[red]3.[/] Supprimer une note\n"
            "[yellow]0.[/] Retour",
            "NOTES MANAGER"
        )

        choice = Prompt.ask("NOTES >")

        if choice == "0":
            break

        elif choice == "1":
            create_note()

        elif choice == "2":
            show_notes()

        elif choice == "3":
            delete_note()

        else:
            console.print("[red]Choix invalide.[/red]")

        pause()


# =========================================================
# MATRIX
# =========================================================

def matrix():

    clear()

    panel(
        "[bold green]MATRIX ACTIVATED[/bold green]\n"
        "[dim]CTRL+C pour arrêter[/dim]"
    )

    try:

        while True:

            line = "".join(
                random.choice("010101ABCDEF")
                for _ in range(80)
            )

            console.print(
                line,
                style="green",
                highlight=False
            )

            time.sleep(0.05)

    except KeyboardInterrupt:
        console.print("\n[yellow]Matrix arrêtée.[/yellow]")

    log("Mode Matrix utilisé")


# =========================================================
# SIMULATION HACKER
# =========================================================

def hacker_simulation():

    clear()

    panel(
        "[bold red]HACKING SIMULATION[/bold red]\n"
        "[dim]Simulation locale sans intrusion réelle.[/dim]"
    )

    operations = [
        "Initialisation du système",
        "Chargement des modules",
        "Analyse fictive des données",
        "Décryptage simulé",
        "Vérification des accès",
        "Finalisation"
    ]

    for operation in operations:
        loading(operation)

    panel(
        "[bold green]ACCESS GRANTED[/bold green]\n"
        "[cyan]SYSTEM STATUS : ONLINE[/cyan]"
    )

    log("Simulation hacker terminée")


# =========================================================
# MINI-JEU
# =========================================================

def mini_game():

    clear()

    secret = random.randint(1, 100)
    attempts = 0

    panel(
        "[bold green]GUESS THE NUMBER[/bold green]\n"
        "Trouve un nombre entre 1 et 100."
    )

    while True:

        guess = IntPrompt.ask("Ton nombre")

        attempts += 1

        if guess < secret:
            console.print("[yellow]Plus grand ![/yellow]")

        elif guess > secret:
            console.print("[yellow]Plus petit ![/yellow]")

        else:

            console.print(
                f"[bold green]BRAVO ! {attempts} essais ![/bold green]"
            )

            break

    log("Mini-jeu terminé")


def reaction_game():

    clear()

    panel(
        "[bold green]REACTION TEST[/bold green]\n"
        "Appuie sur Entrée dès que GO apparaît."
    )

    time.sleep(random.uniform(2, 5))

    start = time.perf_counter()

    console.print("[bold green]GO !!![/bold green]")

    input()

    elapsed = time.perf_counter() - start

    console.print(
        f"[bold cyan]Ton temps : {elapsed:.3f} secondes[/bold cyan]"
    )

    if elapsed < 0.25:
        console.print("[green]Réflexes incroyables ![/green]")

    elif elapsed < 0.5:
        console.print("[yellow]Pas mal ![/yellow]")

    else:
        console.print("[red]Tu peux faire mieux ![/red]")

    log("Test de réflexes effectué")


# =========================================================
# CHRONOMETRE
# =========================================================

def stopwatch():

    clear()

    panel(
        "[bold green]STOPWATCH[/bold green]\n"
        "Appuie sur Entrée pour démarrer."
    )

    input()

    start = time.perf_counter()

    console.print("[green]Chronomètre démarré ![/green]")

    input("Appuie sur Entrée pour arrêter...")

    elapsed = time.perf_counter() - start

    console.print(
        f"[bold cyan]Temps : {elapsed:.3f} secondes[/bold cyan]"
    )


# =========================================================
# COMPTE A REBOURS
# =========================================================

def countdown():

    clear()

    seconds = IntPrompt.ask(
        "Durée en secondes",
        default=10
    )

    if not 1 <= seconds <= 3600:
        console.print("[red]Choisis entre 1 et 3600 secondes.[/red]")
        return

    try:

        for i in range(seconds, 0, -1):

            console.print(
                f"\r[bold green]{i} secondes restantes...[/bold green]",
                end=""
            )

            time.sleep(1)

        console.print("\n[bold red]TEMPS ÉCOULÉ ![/bold red]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Compte à rebours annulé.[/yellow]")


# =========================================================
# COWSAY
# =========================================================

def cow_message():

    clear()

    message = Prompt.ask(
        "Que doit dire la vache ?",
        default="Hello hacker!"
    )

    cowsay.cow(message)

    log("Cowsay utilisé")


# =========================================================
# THEMES
# =========================================================

def change_theme():

    global THEME

    clear()

    panel(
        "[green]1.[/] Vert Matrix\n"
        "[red]2.[/] Rouge Hacker\n"
        "[cyan]3.[/] Bleu Cyber\n"
        "[magenta]4.[/] Violet Night\n"
        "[yellow]5.[/] Gold System",
        "THEME SELECTOR"
    )

    choice = Prompt.ask("Choisis un thème")

    if choice in THEMES:

        THEME = THEMES[choice][0]

        console.print(
            f"[bold {THEME}]Thème modifié : {THEMES[choice][1]}[/bold {THEME}]"
        )

        log(f"Thème changé : {THEMES[choice][1]}")


# =========================================================
# JOURNAL D'ACTIVITE
# =========================================================

def activity_logs():

    clear()

    table = Table(
        title="ACTIVITY HISTORY",
        border_style=THEME
    )

    table.add_column("DATE", style="cyan")
    table.add_column("ACTIVITÉ", style="green")

    for entry in logs[-100:]:

        table.add_row(
            entry["date"],
            entry["message"]
        )

    console.print(table)

    console.print(
        f"[dim]Total : {len(logs)} événements[/dim]"
    )


# =========================================================
# EXTINCTION
# =========================================================

def shutdown_computer():

    clear()

    panel(
        "[bold red]SYSTEM SHUTDOWN[/bold red]\n\n"
        "[yellow]Cette opération va éteindre ton ordinateur.[/yellow]\n"
        "[dim]Sauvegarde tes fichiers avant de continuer.[/dim]"
    )

    if platform.system() != "Linux":

        console.print(
            "[red]Cette fonction est prévue pour Linux uniquement.[/red]"
        )

        return

    if not shutil.which("systemctl"):

        console.print(
            "[red]systemctl est introuvable.[/red]"
        )

        return

    if not Confirm.ask(
        "[bold red]Veux-tu vraiment éteindre ton ordinateur ?[/bold red]",
        default=False
    ):
        return

    if not Confirm.ask(
        "[bold red]DERNIÈRE CONFIRMATION : extinction immédiate ?[/bold red]",
        default=False
    ):
        return

    console.print("[yellow]Demande d'extinction envoyée...[/yellow]")

    try:

        result = subprocess.run(
            ["systemctl", "poweroff"],
            timeout=5,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            console.print(
                "[red]Extinction refusée par le système.[/red]"
            )

            console.print(
                "[yellow]Une autorisation administrateur peut être nécessaire.[/yellow]"
            )

    except subprocess.TimeoutExpired:
        console.print(
            "[green]La demande d'extinction a été transmise.[/green]"
        )

    except Exception as error:

        console.print(
            f"[red]Erreur : {error}[/red]"
        )


# =========================================================
# MENU PRINCIPAL
# =========================================================

def menu():

    actions = {
        "1": dashboard,
        "2": monitor,
        "3": process_manager,
        "4": network_info,
        "5": password_manager,
        "6": file_explorer,
        "7": file_search,
        "8": calculator,
        "9": notes_manager,
        "10": matrix,
        "11": hacker_simulation,
        "12": mini_game,
        "13": reaction_game,
        "14": stopwatch,
        "15": countdown,
        "16": cow_message,
        "17": change_theme,
        "18": activity_logs,
        "19": shutdown_computer
    }

    while True:

        clear()

        banner()

        memory = psutil.virtual_memory()

        console.print(
            f"[{THEME}]CPU : {psutil.cpu_percent()}% "
            f"| RAM : {memory.percent}% "
            f"| PASSWORDS : {len(vault)} "
            f"| NOTES : {len(notes)}[/{THEME}]"
        )

        panel(
            "[green]1.[/] Dashboard système\n"
            "[green]2.[/] Moniteur CPU / RAM en direct\n"
            "[green]3.[/] Gestionnaire de processus\n"
            "[green]4.[/] Informations réseau\n"
            "[green]5.[/] Password Manager 🔐\n"
            "[green]6.[/] Explorateur de fichiers\n"
            "[green]7.[/] Recherche de fichiers\n"
            "[green]8.[/] Calculatrice\n"
            "[green]9.[/] Notes personnelles\n"
            "[green]10.[/] Matrix Mode\n"
            "[green]11.[/] Hacker Simulation\n"
            "[green]12.[/] Mini-jeu\n"
            "[green]13.[/] Test de réflexes\n"
            "[green]14.[/] Chronomètre\n"
            "[green]15.[/] Compte à rebours\n"
            "[green]16.[/] Cowsay\n"
            "[green]17.[/] Changer de thème\n"
            "[green]18.[/] Historique d'activité\n"
            "[bold red]19.[/] Éteindre le PC 🔌\n"
            "[bold red]0.[/] Quitter",
            "MAIN MENU"
        )

        choice = Prompt.ask(
            f"[bold {THEME}]DARK NET >[/bold {THEME}]"
        )

        if choice == "0":

            console.print(
                "[bold red]DARK TERMINAL SHUTDOWN...[/bold red]"
            )

            log("Fermeture du programme")

            break

        action = actions.get(choice)

        if action:

            try:

                action()

            except KeyboardInterrupt:

                console.print(
                    "\n[yellow]Opération interrompue.[/yellow]"
                )

            except Exception as error:

                console.print(
                    f"\n[red]Erreur : {error}[/red]"
                )

                log(f"Erreur : {error}")

            if choice != "19":
                pause()

        else:

            console.print("[red]Commande inconnue ![/red]")

            time.sleep(1)


# =========================================================
# DEMARRAGE
# =========================================================

if __name__ == "__main__":

    try:

        load_logs()
        load_notes()

        if unlock_vault():

            log("Connexion à DARK TERMINAL V5")

            menu()

        else:

            console.print(
                "[bold red]ACCÈS REFUSÉ[/bold red]"
            )

    except KeyboardInterrupt:

        console.print(
            "\n[bold red]TERMINAL CLOSED[/bold red]"
        )

    except Exception as error:

        console.print(
            f"\n[bold red]ERREUR FATALE : {error}[/bold red]"
        )

    finally:

        console.print(
            "[dim]Merci d'avoir utilisé DARK TERMINAL V5.[/dim]"
        )
