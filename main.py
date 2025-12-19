import os
import requests
from collections import Counter

# Read API token from environment variable (do NOT hardcode secrets in code)
# Set it like:
#   Windows PowerShell:  setx BETS_API_TOKEN "your_token_here"
#   Mac/Linux:           export BETS_API_TOKEN="your_token_here"
API_TOKEN = os.getenv("BETS_API_TOKEN")
BASE_URL = "https://api.b365api.com/"

player_ids = {
    "bazuka": 1158314,
    "lucashin": 1158313,
    "jovke": 1158316,
    "kadzima": 1158065,
    "dzmn": 1158315,
    "pakapaka": 1159457,
    "tapachan": 1158895,
    "lalkoff": 1158067,
    "lucker": 1158069,
    "dzojo": 1083674,
    "chiefkeef": 1101785,
    "panteraxball": 1119893,
    "andrik": 1158454,
    "shooter": 1190790,
    "elel": 1159090,
    "ugren": 1158650
}

# Color codes for terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def require_api_token() -> bool:
    """Ensure API token exists before making requests."""
    if not API_TOKEN:
        print(f"{Colors.RED}{Colors.BOLD}Missing API token.{Colors.END}")
        print("Set environment variable BETS_API_TOKEN, then run again.")
        return False
    return True


def safe_int_input(prompt: str) -> int:
    """Safely parse integer input from the user."""
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if val <= 0:
                print(f"{Colors.RED}Please enter a number greater than 0.{Colors.END}")
                continue
            return val
        except ValueError:
            print(f"{Colors.RED}Please enter a valid whole number.{Colors.END}")


def get_player_id(name: str) -> int | None:
    """Lookup player ID by name (case-insensitive)."""
    key = name.strip().lower()
    return player_ids.get(key)


def api_get(url: str, params: dict) -> dict | None:
    """Wrapper for API GET requests with timeout + basic error handling."""
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        print(f"{Colors.RED}Request timed out. Try again.{Colors.END}")
    except requests.exceptions.HTTPError as e:
        print(f"{Colors.RED}HTTP error: {e}{Colors.END}")
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}Network error: {e}{Colors.END}")
    except ValueError:
        print(f"{Colors.RED}Failed to parse JSON response.{Colors.END}")
    return None


def get_head_to_head_games(player1, player2, target_games):
    """
    Fetch games between two players in Ebasketball Battle from BetsAPI
    """
    if not require_api_token():
        return []

    url = f"{BASE_URL}v3/events/ended"
    params = {
        "token": API_TOKEN,
        "sport_id": 18,
        "page": 1,
        "league_id": 23105,
        "team_id": player1
    }

    games = []

    while len(games) < target_games:
        response = api_get(url, params=params)
        if not response:
            break

        results = response.get("results", [])
        if not results:
            print(f"No more results found. Found {len(games)} games total.")
            break

        for game in results:
            home = game.get("home")
            away = game.get("away")

            if not home or not away:
                continue

            # time_status "3" = ended (per your original logic)
            if str(game.get("time_status")) != "3":
                continue

            h_id = str(home.get("id"))
            a_id = str(away.get("id"))
            p1 = str(player1)
            p2 = str(player2)

            if (p1 == h_id and p2 == a_id) or (p2 == h_id and p1 == a_id):
                games.append({
                    "home": home,
                    "away": away,
                    "score": game.get("ss"),
                    "id": game.get("id")
                })
                if len(games) >= target_games:
                    break

        if len(games) >= target_games:
            break

        params["page"] += 1
        print(f"Page {params['page']} - Found {len(games)}/{target_games} games so far...")

    return games


def analyze_spreads(games, player1):
    """
    Compute score spreads and find lines with 80-100% hit rate
    """
    spreads = []
    for g in games:
        try:
            if not g.get("score"):
                continue
            home_score, away_score = map(int, g["score"].split("-"))
            if str(g["home"]["id"]) == str(player1):
                spread = home_score - away_score
            else:
                spread = away_score - home_score
            spreads.append(spread)
        except Exception:
            continue

    if not spreads:
        return []

    total = len(spreads)
    largest_loss = min(spreads)
    largest_win = max(spreads)

    results = []
    for line in range(largest_loss - 1, largest_win + 1):
        counter = 0
        for j in spreads:
            if j > line + 0.5:
                counter += 1
        hit_rate = counter / total
        if hit_rate >= 0.80:
            results.append({
                "spread": -(line + 0.5),
                "hit_rate": f"{hit_rate:.2%}",
                "hit_rate_raw": hit_rate,
                "hits": counter,
                "games": total
            })

    return sorted(results, key=lambda x: -x["hit_rate_raw"])


def get_head_to_head_stats(games, player1, player2):
    """
    Calculate wins/losses and average margins
    """
    p1_wins = 0
    p2_wins = 0
    p1_margins = []

    for g in games:
        try:
            if not g.get("score"):
                continue
            home_score, away_score = map(int, g["score"].split("-"))

            if str(g["home"]["id"]) == str(player1):
                margin = home_score - away_score
            else:
                margin = away_score - home_score

            if margin > 0:
                p1_wins += 1
            else:
                p2_wins += 1

            p1_margins.append(margin)
        except Exception:
            continue

    p1_avg_margin = sum(p1_margins) / len(p1_margins) if p1_margins else 0

    return {
        "p1_wins": p1_wins,
        "p2_wins": p2_wins,
        "p1_avg_margin": p1_avg_margin,
        "p2_avg_margin": -p1_avg_margin
    }


def calculate_form(games, player1, last_n):
    """
    Calculate recent form (wins in last N games)
    """
    recent_games = games[:min(last_n, len(games))]
    wins = 0

    for g in recent_games:
        try:
            if not g.get("score"):
                continue
            home_score, away_score = map(int, g["score"].split("-"))

            if str(g["home"]["id"]) == str(player1):
                if home_score > away_score:
                    wins += 1
            else:
                if away_score > home_score:
                    wins += 1
        except Exception:
            continue

    return wins, len(recent_games)


def color_by_hit_rate(hit_rate_str):
    """
    Return colored text based on hit rate
    """
    rate = float(hit_rate_str.strip('%'))
    if rate == 100.0:
        return f"{Colors.GREEN}{Colors.BOLD}{hit_rate_str}{Colors.END}"
    elif rate >= 95.0:
        return f"{Colors.GREEN}{hit_rate_str}{Colors.END}"
    elif rate >= 90.0:
        return f"{Colors.YELLOW}{hit_rate_str}{Colors.END}"
    else:
        return hit_rate_str


def analyze_matchup():
    """
    Analyze a specific matchup between two players
    """
    print(f"\n{Colors.CYAN}{Colors.BOLD}=== MATCHUP ANALYSIS ==={Colors.END}")
    name1 = input("Enter first player name: ").strip()
    name2 = input("Enter second player name: ").strip()
    num_games = safe_int_input("How many games do you want to analyze? ")

    player1 = get_player_id(name1)
    player2 = get_player_id(name2)

    if player1 is None or player2 is None:
        print(f"{Colors.RED}Unknown player name(s). Available names:{Colors.END}")
        print(", ".join(sorted(player_ids.keys())))
        return

    games = get_head_to_head_games(player1, player2, num_games)

    if not games:
        print("No games found (or API token missing).")
        return

    print(f"\nFound {len(games)} games between {name1} and {name2}.")

    stats = get_head_to_head_stats(games, player1, player2)

    print(f"\n{Colors.BOLD}HEAD-TO-HEAD RECORD:{Colors.END}")
    print(f"{name1}: {Colors.GREEN}{stats['p1_wins']} wins{Colors.END}")
    print(f"{name2}: {Colors.GREEN}{stats['p2_wins']} wins{Colors.END}")
    print(f"\n{Colors.BOLD}AVERAGE MARGIN:{Colors.END}")
    print(f"{name1}: {stats['p1_avg_margin']:+.1f} points")
    print(f"{name2}: {stats['p2_avg_margin']:+.1f} points")

    results_p1 = analyze_spreads(games, player1)
    results_p2 = analyze_spreads(games, player2)

    print(f"\n{'=' * 60}")
    print(f"{Colors.BOLD}80-100% Hit Rate Lines for {name1.upper()}:{Colors.END}")
    print(f"{'=' * 60}")
    if results_p1:
        for r in results_p1:
            spread = r['spread']
            status = f" {Colors.GREEN}[100% GREEN]{Colors.END}" if r['hit_rate'] == "100.00%" else ""
            colored_rate = color_by_hit_rate(r['hit_rate'])
            print(f"Spread {spread:+.1f} | Hit Rate {colored_rate}{status} "
                  f"({r['hits']}/{r['games']})")
    else:
        print("No 80-100% reliable lines found.")

    print(f"\n{'=' * 60}")
    print(f"{Colors.BOLD}80-100% Hit Rate Lines for {name2.upper()}:{Colors.END}")
    print(f"{'=' * 60}")
    if results_p2:
        for r in results_p2:
            spread = r['spread']
            status = f" {Colors.GREEN}[100% GREEN]{Colors.END}" if r['hit_rate'] == "100.00%" else ""
            colored_rate = color_by_hit_rate(r['hit_rate'])
            print(f"Spread {spread:+.1f} | Hit Rate {colored_rate}{status} "
                  f"({r['hits']}/{r['games']})")
    else:
        print("No 80-100% reliable lines found.")


def analyze_form():
    """
    Analyze recent form for a matchup
    """
    print(f"\n{Colors.CYAN}{Colors.BOLD}=== FORM ANALYSIS ==={Colors.END}")
    name1 = input("Enter first player name: ").strip()
    name2 = input("Enter second player name: ").strip()
    num_games = safe_int_input("How many total games to fetch? ")

    player1 = get_player_id(name1)
    player2 = get_player_id(name2)

    if player1 is None or player2 is None:
        print(f"{Colors.RED}Unknown player name(s). Available names:{Colors.END}")
        print(", ".join(sorted(player_ids.keys())))
        return

    games = get_head_to_head_games(player1, player2, num_games)

    if not games:
        print("No games found (or API token missing).")
        return

    print(f"\nFound {len(games)} games between {name1} and {name2}.")

    max_games = len(games)
    form_periods = []

    if max_games >= 5:
        form_periods.append(5)
    if max_games >= 10:
        form_periods.append(10)
    if max_games >= 15:
        form_periods.append(15)
    if max_games >= 20:
        form_periods.append(20)
    if max_games >= 30:
        form_periods.append(30)
    if max_games >= 50:
        form_periods.append(50)

    if max_games not in form_periods:
        form_periods.append(max_games)

    print(f"\n{Colors.BOLD}RECENT FORM:{Colors.END}")
    for period in form_periods:
        p1_wins, p1_games = calculate_form(games, player1, period)
        p2_wins = p1_games - p1_wins

        p1_rate = (p1_wins / p1_games * 100) if p1_games > 0 else 0
        p2_rate = (p2_wins / p1_games * 100) if p1_games > 0 else 0

        print(f"\n{Colors.CYAN}Last {period} games:{Colors.END}")
        print(f"  {name1}: {Colors.GREEN}{p1_wins}/{p1_games}{Colors.END} wins ({p1_rate:.1f}%)")
        print(f"  {name2}: {Colors.GREEN}{p2_wins}/{p1_games}{Colors.END} wins ({p2_rate:.1f}%)")


def show_menu():
    """
    Display main menu
    """
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}E-BASKETBALL SPREAD ANALYZER{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print("\n1. Analyze Matchup (Spreads & Stats)")
    print("2. Analyze Form (Recent Performance)")
    print("3. Exit")
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.END}")


def main():
    """
    Main menu loop
    """
    while True:
        show_menu()
        choice = input("\nSelect an option (1-3): ").strip()

        if choice == "1":
            analyze_matchup()
        elif choice == "2":
            analyze_form()
        elif choice == "3":
            print(f"\n{Colors.GREEN}Thanks for using the analyzer! Goodbye.{Colors.END}")
            break
        else:
            print(f"{Colors.RED}Invalid option. Please choose 1-3.{Colors.END}")


if __name__ == "__main__":
    main()
