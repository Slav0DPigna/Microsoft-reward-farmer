import argparse
import json
import logging
import logging.handlers as handlers
import os
import os.path
import random
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Event, Thread

from src import Browser, DailySet, Login, MorePromotions, PunchCards, Searches
from src.constants import VERSION
from src.loggingColoredFormatter import ColoredFormatter
from src.notifier import Notifier

POINTS_COUNTER = 0


def main():
    setupLogging()
    args = argumentParser()
    if args.add:
        add_account(args.add_account[0], args.add_account[1])
        return
    notifier = Notifier(args)
    loadedAccounts = setupAccounts()
    delete_sessions_folder()
    for currentAccount in loadedAccounts:
        can_continue = True
        if "@" not in currentAccount["username"]:
            logging.error("Email " + currentAccount["username"] + " not valid")
            can_continue = False
        if can_continue:
            try:
                executeBot(currentAccount, notifier, args)
            except Exception as e:
                logging.exception(f"{e.__class__.__name__}: {e}")


def setupLogging():
    format = "%(asctime)s [%(levelname)s] %(message)s"
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(ColoredFormatter(format))

    (Path(__file__).resolve().parent / "src/logs").mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                "src/logs/activity.log",
                when="midnight",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            ),
            terminalHandler,
        ],
    )
    # try:
    #    shutil.rmtree("src//sessions")
    #    logging.info("[INFO] Folder and contents successfully deleted")
    # except:
    #    logging.info("[INFO] Sessions folder not existing")
    #    pass


def argumentParser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Microsoft Rewards Farmer")
    parser.add_argument(
        "-v", "--visible", action="store_true", help="Optional: Visible browser"
    )
    parser.add_argument(
        "-l", "--lang", type=str, default=None, help="Optional: Language (ex: en)"
    )
    parser.add_argument(
        "-g", "--geo", type=str, default=None, help="Optional: Geolocation (ex: US)"
    )
    parser.add_argument(
        "-p",
        "--proxy",
        type=str,
        default=None,
        help="Optional: Global Proxy (ex: http://user:pass@host:port)",
    )
    parser.add_argument(
        "-t",
        "--telegram",
        metavar=("TOKEN", "CHAT_ID"),
        nargs=2,
        type=str,
        default=None,
        help="Optional: Telegram Bot Token and Chat ID (ex: 123456789:ABCdefGhIjKlmNoPQRsTUVwxyZ 123456789)",
    )
    parser.add_argument(
        "-d",
        "--discord",
        type=str,
        default=None,
        help="Optional: Discord Webhook URL (ex: https://discord.com/api/webhooks/123456789/ABCdefGhIjKlmNoPQRsTUVwxyZ)",
    )
    parser.add_argument(
        "-a",
        "--add",
        metavar=("EMAIL", "PASSWD"),
        nargs=2,
        type=str,
        default=None,
        help="Optional: Add account on json account file",
    )
    return parser.parse_args()


def add_account(email: str, passwd: str):
    path = "accounts.json"
    if not os.path.exists(path):
        path = "_internal/accounts.json"
    print(path)
    with open(path, "r") as file:
        if email in file.read():
            logging.error("Account already added")
            return
    if "@" in email:
        with open(path, "r") as file:
            data = json.load(file)
        data.append({"username": email, "password": passwd})
        with open(path, "w") as file:
            json.dump(data, file, indent=2)
        logging.info("Account successfully added")
    else:
        logging.error("Invalid email")


def bannerDisplay():
    farmerBanner = """
          _____                    _____            _____                    _____                   _______         
         /\    \                  /\    \          /\    \                  /\    \                 /::\    \        
        /::\    \                /::\____\        /::\    \                /::\____\               /::::\    \       
       /::::\    \              /:::/    /       /::::\    \              /:::/    /              /::::::\    \      
      /::::::\    \            /:::/    /       /::::::\    \            /:::/    /              /::::::::\    \     
     /:::/\:::\    \          /:::/    /       /:::/\:::\    \          /:::/    /              /:::/~~\:::\    \    
    /:::/__\:::\    \        /:::/    /       /:::/__\:::\    \        /:::/____/              /:::/    \:::\    \   
    \:::\   \:::\    \      /:::/    /       /::::\   \:::\    \       |::|    |              /:::/    / \:::\    \  
  ___\:::\   \:::\    \    /:::/    /       /::::::\   \:::\    \      |::|    |     _____   /:::/____/   \:::\____\ 
 /\   \:::\   \:::\    \  /:::/    /       /:::/\:::\   \:::\    \     |::|    |    /\    \ |:::|    |     |:::|    |
/::\   \:::\   \:::\____\/:::/____/       /:::/  \:::\   \:::\____\    |::|    |   /::\____\|:::|____|     |:::|    |
\:::\   \:::\   \::/    /\:::\    \       \::/    \:::\  /:::/    /    |::|    |  /:::/    / \:::\    \   /:::/    / 
 \:::\   \:::\   \/____/  \:::\    \       \/____/ \:::\/:::/    /     |::|    | /:::/    /   \:::\    \ /:::/    /  
  \:::\   \:::\    \       \:::\    \               \::::::/    /      |::|____|/:::/    /     \:::\    /:::/    /   
   \:::\   \:::\____\       \:::\    \               \::::/    /       |:::::::::::/    /       \:::\__/:::/    /    
    \:::\  /:::/    /        \:::\    \              /:::/    /        \::::::::::/____/         \::::::::/    /     
     \:::\/:::/    /          \:::\    \            /:::/    /          ~~~~~~~~~~                \::::::/    /      
      \::::::/    /            \:::\    \          /:::/    /                                      \::::/    /       
       \::::/    /              \:::\____\        /:::/    /                                        \::/____/        
        \::/    /                \::/    /        \::/    /                                          ~~              
         \/____/                  \/____/          \/____/                                                           
                                                                                                                     
"""
    logging.info(farmerBanner)
    logging.info(f"        by Slav0 (@Slav0DPigna)               version {VERSION}\n")


def setupAccounts() -> dict:
    accountPath = Path(__file__).resolve().parent / "accounts.json"
    if not accountPath.exists():
        accountPath.write_text(
            json.dumps(
                [{"username": "Your Email", "password": "Your Password"}], indent=4
            ),
            encoding="utf-8",
        )
        noAccountsNotice = """
    [ACCOUNT] Accounts credential file "accounts.json" not found.
    [ACCOUNT] A new file has been created, please edit with your credentials and save.
    """
        logging.warning(noAccountsNotice)
        exit()
    loadedAccounts = json.loads(accountPath.read_text(encoding="utf-8"))
    # random.shuffle(loadedAccounts)
    return loadedAccounts


def executeBot(currentAccount, notifier: Notifier, args: argparse.Namespace):
    current_data = datetime.now().strftime("%d-%m-%Y")
    account_email = currentAccount["username"]
    if not os.path.exists("src/seen_account.txt"):  # verifico che questo file esiste
        open("src/seen_account.txt", "x")  # se non esiste lo creo
        logging.warning("I create a seen_account file")
    with open("src/seen_account.txt", "r+") as file:
        content = file.read()
        if (
            account_email not in content
        ):  # se la email non é nel file eseguo la pipeline
            logging.info(
                f'********************{currentAccount.get("username", "")}********************'
            )
            with Browser(
                mobile=False, account=currentAccount, args=args
            ) as desktopBrowser:
                accountPointsCounter = Login(desktopBrowser).login()
                startingPoints = accountPointsCounter
                logging.info(
                    f"[POINTS] You have {desktopBrowser.utils.formatNumber(accountPointsCounter)} points on your account !"
                )
                DailySet(desktopBrowser).completeDailySet()
                PunchCards(desktopBrowser).completePunchCards()
                MorePromotions(desktopBrowser).completeMorePromotions()
                (
                    remainingSearches,
                    remainingSearchesM,
                ) = desktopBrowser.utils.getRemainingSearches()
                logging.info("Desktop search remaining " + str(remainingSearches))
                logging.info("Mobile search remaining " + str(remainingSearchesM))
                if remainingSearches != 0:
                    accountPointsCounter = Searches(desktopBrowser).bingSearches(
                        remainingSearches
                    )
                if remainingSearchesM != 0:
                    desktopBrowser.closeBrowser()
                    with Browser(
                        mobile=True, account=currentAccount, args=args
                    ) as mobileBrowser:
                        accountPointsCounter = Login(mobileBrowser).login()
                        accountPointsCounter = Searches(mobileBrowser).bingSearches(
                            remainingSearchesM
                        )

                logging.info(
                    f"[POINTS] You have earned {desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints)} points today !"
                )
                logging.info(
                    f"[POINTS] You are now at {desktopBrowser.utils.formatNumber(accountPointsCounter)} points !"
                )

                notifier.send(
                    "\n".join(
                        [
                            "Microsoft Rewards Farmer",
                            f"Account: {currentAccount.get('username', '')}",
                            f"Points earned today: {desktopBrowser.utils.formatNumber(accountPointsCounter - startingPoints)}",
                            f"Total points: {desktopBrowser.utils.formatNumber(accountPointsCounter)}",
                        ]
                    )
                )
                if (
                    current_data not in content
                ):  # se la data non é quella odierna cancello il contenuto del file, scivo la data
                    file.seek(0)
                    file.truncate()
                    file.write(current_data + "\n")
                    logging.warning("I wrote today's date")
                    # aspetto che il file venga scritto altrimenti si rischia di trovare gli account dei giorni precedenti
                    content = file.read()
                file.write(account_email + "\n")
                logging.warning("Account " + account_email + " added to file")
                try:
                    desktopBrowser.closeBrowser()
                    mobileBrowser.closeBrowser()
                except:
                    pass
        else:
            logging.warning("The account " + account_email + " is alredy seen")


def delete_sessions_folder():
    path = Path(__file__).parent / "src//sessions"
    try:
        shutil.rmtree(path)
        logging.info(
            f"Directory '{path}' and it's contents have been successfully deleted."
        )
    except Exception as e:
        logging.error(f"An error occurred while deleting the directory session: {e}")


if __name__ == "__main__":
    main()
    delete_sessions_folder()
    quit()
