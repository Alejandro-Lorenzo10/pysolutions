# utils.py
from colorama import Fore, Style, init as color_init

color_init(autoreset=True)

# Command aliases used by the client
ALIASES = {
    "ls": "list",
    "rm": "remove",
    "del": "remove",
    "add": "add",
    "login": "login",
    "register": "register",
    "help": "help",
    "exit": "exit",
}

def ok(msg: str):
    print(Fore.GREEN + "✔ " + str(msg))

def err(msg):
    # Be robust if msg is None
    if msg is None:
        msg = "Unknown error"
    print(Fore.RED + "✘ " + str(msg))

def info(msg: str):
    print(Fore.YELLOW + "• " + str(msg))

def prompt(user: str | None) -> str:
    name = user or "guest"
    return Fore.CYAN + f"{name}> " + Style.RESET_ALL
