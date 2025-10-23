# utils.py
from colorama import Fore, Style, init as color_init

color_init(autoreset=True)

ALIASES = {
    "ls": "list",
    "rm": "remove",
    "add": "add",
    "del": "remove",
    "login": "login",
    "register": "register",
    "help": "help",
    "exit": "exit",
}

def ok(msg):   print(Fore.GREEN + "✔ " + msg)
def err(msg):  print(Fore.RED   + "✘ " + msg)
def info(msg): print(Fore.YELLOW+ "• " + msg)

def prompt(user: str | None) -> str:
    name = user or "guest"
    return Fore.CYAN + f"{name}> " + Style.RESET_ALL
