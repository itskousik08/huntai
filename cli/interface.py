"""
HuntAI CLI Interface - Hacker-style Terminal UI
"""

import os
import sys
import time
import threading
from datetime import datetime

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORAMA = True
except ImportError:
    COLORAMA = False

# Color shortcuts
def c(color, text):
    if not COLORAMA:
        return text
    colors = {
        'red': Fore.RED, 'green': Fore.GREEN, 'yellow': Fore.YELLOW,
        'blue': Fore.BLUE, 'cyan': Fore.CYAN, 'magenta': Fore.MAGENTA,
        'white': Fore.WHITE, 'bright_green': Fore.GREEN + Style.BRIGHT,
        'bright_cyan': Fore.CYAN + Style.BRIGHT, 'bright_yellow': Fore.YELLOW + Style.BRIGHT,
        'bright_red': Fore.RED + Style.BRIGHT, 'bright_white': Fore.WHITE + Style.BRIGHT,
        'dim': Style.DIM, 'reset': Style.RESET_ALL,
    }
    return colors.get(color, '') + str(text) + Style.RESET_ALL


BANNER = r"""
  ██╗  ██╗██╗   ██╗███╗   ██╗████████╗ █████╗ ██╗
  ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔══██╗██║
  ███████║██║   ██║██╔██╗ ██║   ██║   ███████║██║
  ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══██║██║
  ██║  ██║╚██████╔╝██║ ╚████║   ██║   ██║  ██║██║
  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝
"""

TAGLINE = "  [ LOCAL AI LEAD GENERATION & OUTREACH AGENT ]"
VERSION = "  v1.0.0 | Powered by Ollama + glm-4:cloud"


MAIN_MENU = [
    ("01", "Start HuntAI",              "Launch automated lead generation"),
    ("02", "Setup / Onboarding",        "Configure your profile & targets"),
    ("03", "Configure Email",           "SMTP & outreach settings"),
    ("04", "Lead Scraping Settings",    "Define scraping parameters"),
    ("05", "Launch Dashboard",          "Open web dashboard (localhost:3000)"),
    ("06", "View History",              "Browse past campaigns & leads"),
    ("07", "System Status",             "Check AI, Ollama & scraper status"),
    ("EX", "Exit",                      "Quit HuntAI"),
]


class HuntAICLI:
    def __init__(self, config):
        self.config = config
        self.running = True

    def clear(self):
        os.system('clear' if os.name != 'nt' else 'cls')

    def print_banner(self):
        self.clear()
        print(c('bright_green', BANNER))
        print(c('bright_cyan', TAGLINE))
        print(c('dim', VERSION))
        print()
        # Status bar
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._check_status_inline()
        print(c('dim', f"  ─────────────────────────────────────────────────────"))
        print(f"  {c('dim', 'TIME:')} {c('yellow', now)}")
        print(c('dim', f"  ─────────────────────────────────────────────────────"))
        print()

    def _check_status_inline(self):
        ollama_ok = self._ping_ollama()
        db_ok = self._ping_db()
        cfg_ok = self.config.is_configured()

        ollama_str = c('bright_green', '● OLLAMA') if ollama_ok else c('bright_red', '○ OLLAMA')
        db_str = c('bright_green', '● DATABASE') if db_ok else c('bright_red', '○ DATABASE')
        cfg_str = c('bright_green', '● CONFIGURED') if cfg_ok else c('bright_yellow', '○ SETUP NEEDED')

        print(f"  {ollama_str}  {db_str}  {cfg_str}")

    def _ping_ollama(self):
        try:
            import httpx
            r = httpx.get("http://localhost:11434/api/tags", timeout=2)
            return r.status_code == 200
        except:
            return False

    def _ping_db(self):
        try:
            from database.db import get_db
            conn = get_db()
            conn.execute("SELECT 1")
            return True
        except:
            return False

    def print_menu(self):
        print(c('bright_cyan', "  ╔══════════════════════════════════════════════════╗"))
        print(c('bright_cyan', "  ║") + c('bright_white', "              MAIN MENU — SELECT OPTION           ") + c('bright_cyan', "║"))
        print(c('bright_cyan', "  ╠══════════════════════════════════════════════════╣"))
        for key, title, desc in MAIN_MENU:
            key_str = c('bright_yellow', f"  [{key}]")
            title_str = c('bright_white', f" {title:<28}")
            desc_str = c('dim', f" {desc}")
            print(c('bright_cyan', "  ║") + f"{key_str}{title_str}{desc_str}")
        print(c('bright_cyan', "  ╚══════════════════════════════════════════════════╝"))
        print()

    def prompt(self):
        try:
            return input(c('bright_green', "  huntai") + c('dim', "@") + c('cyan', "local") + c('bright_green', " ➜ ") + c('bright_white', "")).strip().upper()
        except (EOFError, KeyboardInterrupt):
            return "EX"

    def spinner(self, message, duration=2):
        frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        end_time = time.time() + duration
        i = 0
        while time.time() < end_time:
            sys.stdout.write(f"\r  {c('bright_cyan', frames[i % len(frames)])} {c('yellow', message)}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

    def print_section(self, title):
        print()
        print(c('bright_cyan', f"  ┌─── {title} {'─' * (48 - len(title))}┐"))
        print()

    def print_end_section(self):
        print()
        print(c('bright_cyan', "  └" + "─" * 52 + "┘"))
        print()

    def run(self):
        """Main run loop."""
        # Show boot sequence
        self._boot_sequence()

        # Check if first run
        if not self.config.is_configured():
            self.print_banner()
            print(c('bright_yellow', "  ⚡ First run detected! Starting onboarding wizard..."))
            time.sleep(1.5)
            self.do_onboarding()

        while self.running:
            self.print_banner()
            self.print_menu()
            choice = self.prompt()

            actions = {
                "01": self.start_huntai,
                "02": self.do_onboarding,
                "03": self.configure_email,
                "04": self.scraping_settings,
                "05": self.launch_dashboard,
                "06": self.view_history,
                "07": self.system_status,
                "EX": self.exit_app,
            }

            action = actions.get(choice)
            if action:
                action()
            else:
                print(c('bright_red', "\n  ✗ Invalid option. Please select from the menu."))
                time.sleep(1)

    def _boot_sequence(self):
        """Animated boot sequence."""
        self.clear()
        lines = [
            ("bright_green", "  Initializing HuntAI..."),
            ("cyan",         "  Loading AI modules..."),
            ("yellow",       "  Connecting to Ollama (glm-4:cloud)..."),
            ("cyan",         "  Starting database engine..."),
            ("bright_green", "  System ready."),
        ]
        print(c('bright_green', BANNER))
        print()
        for color, line in lines:
            print(c(color, line))
            time.sleep(0.25)
        time.sleep(0.5)

    def start_huntai(self):
        """Start the main HuntAI agent."""
        self.print_banner()
        self.print_section("START HUNTAI AGENT")

        if not self.config.is_configured():
            print(c('bright_red', "  ✗ HuntAI is not configured. Run Setup first [02]."))
            input(c('dim', "\n  Press Enter to return..."))
            return

        print(c('bright_white', "  Configure this hunt:"))
        print()

        campaign_name = input(c('cyan', "  Campaign name: ")).strip() or "Default Campaign"
        lead_count = input(c('cyan', "  How many leads to find? [10]: ")).strip() or "10"
        try:
            lead_count = int(lead_count)
        except:
            lead_count = 10

        print()
        print(c('bright_yellow', "  Target filters (press Enter to use saved defaults):"))
        industry = input(c('cyan', f"  Industry [{self.config.get('target_industry', 'any')}]: ")).strip()
        location = input(c('cyan', f"  Location [{self.config.get('target_location', 'any')}]: ")).strip()
        company_size = input(c('cyan', f"  Company size (startup/small/enterprise/any) [{self.config.get('ideal_client_size', 'any')}]: ")).strip()

        if not industry:
            industry = self.config.get('target_industry', '')
        if not location:
            location = self.config.get('target_location', '')
        if not company_size:
            company_size = self.config.get('ideal_client_size', 'any')

        print()
        print(c('bright_green', "  Starting HuntAI agent..."))
        print(c('dim', f"  Campaign: {campaign_name} | Leads: {lead_count} | Industry: {industry}"))
        print()

        # Launch background worker
        try:
            from background_worker.worker import BackgroundWorker
            worker = BackgroundWorker(self.config)
            worker.start_campaign(
                name=campaign_name,
                lead_count=lead_count,
                industry=industry,
                location=location,
                company_size=company_size,
            )
            print(c('bright_green', f"  ✓ Campaign '{campaign_name}' started!"))
            print(c('cyan', "  ✓ Background worker is running"))
            print(c('cyan', "  ✓ Open the dashboard to monitor: http://localhost:3000"))
        except Exception as e:
            print(c('bright_red', f"  ✗ Error starting campaign: {e}"))

        input(c('dim', "\n  Press Enter to return..."))

    def do_onboarding(self):
        """Run the onboarding setup wizard."""
        self.print_banner()
        self.print_section("SETUP & ONBOARDING WIZARD")

        print(c('bright_white', "  Welcome to HuntAI Setup!"))
        print(c('dim',  "  Answer the following questions to configure your agent."))
        print(c('dim',  "  Press Enter to skip optional fields."))
        print()

        questions = [
            ("user_name",           "Your Name",                              True,  ""),
            ("company_name",        "Company Name",                           True,  ""),
            ("company_website",     "Company Website (https://...)",          False, ""),
            ("service_description", "What service does your company provide", True,  ""),
            ("target_customer",     "Target customer type (B2B/B2C/Both)",    True,  "B2B"),
            ("target_industry",     "Target industry (e.g. SaaS, Retail)",    True,  ""),
            ("target_location",     "Target country/location",                True,  ""),
            ("ideal_client_size",   "Ideal client size (startup/small/enterprise/any)", True, "small"),
            ("email_address",       "Your outreach email address",            True,  ""),
            ("email_password",      "Email App Password (hidden)",            True,  "password"),
            ("notification_email",  "Notification email (where HuntAI sends updates)", True, ""),
            ("apify_api_key",       "Apify API Key",                          True,  "password"),
        ]

        data = {}
        for key, label, required, default in questions:
            while True:
                prompt = f"  {c('bright_cyan', label)}"
                if default and default != "password":
                    prompt += c('dim', f" [{default}]")
                prompt += c('bright_white', ": ")

                if default == "password":
                    import getpass
                    val = getpass.getpass(prompt=prompt)
                else:
                    val = input(prompt).strip()

                if not val and default and default != "password":
                    val = default
                if not val and required:
                    print(c('bright_red', f"  ✗ '{label}' is required."))
                    continue
                data[key] = val
                break

        print()
        self.spinner("Saving configuration...", 1.5)
        self.config.save_all(data)
        print(c('bright_green', "  ✓ Configuration saved successfully!"))
        print(c('bright_green', "  ✓ HuntAI is ready to hunt."))

        input(c('dim', "\n  Press Enter to continue..."))

    def configure_email(self):
        """Configure email settings."""
        self.print_banner()
        self.print_section("EMAIL CONFIGURATION")

        print(c('bright_white', "  SMTP Email Settings"))
        print()

        smtp_host = input(c('cyan', f"  SMTP Host [{self.config.get('smtp_host', 'smtp.gmail.com')}]: ")).strip() or self.config.get('smtp_host', 'smtp.gmail.com')
        smtp_port = input(c('cyan', f"  SMTP Port [{self.config.get('smtp_port', '587')}]: ")).strip() or self.config.get('smtp_port', '587')
        email = input(c('cyan', f"  Email Address [{self.config.get('email_address', '')}]: ")).strip() or self.config.get('email_address', '')

        import getpass
        password = getpass.getpass(prompt=c('cyan', "  App Password (hidden): "))

        print()
        print(c('bright_white', "  Email Sending Rules"))
        daily_limit = input(c('cyan', "  Max emails per day [50]: ")).strip() or "50"
        delay_between = input(c('cyan', "  Delay between emails in seconds [30]: ")).strip() or "30"
        warmup_mode = input(c('cyan', "  Enable warmup mode? (yes/no) [no]: ")).strip().lower() or "no"

        updates = {
            'smtp_host': smtp_host,
            'smtp_port': smtp_port,
            'email_address': email,
            'email_password': password,
            'daily_email_limit': daily_limit,
            'email_delay_seconds': delay_between,
            'email_warmup_mode': warmup_mode,
        }
        self.config.save_all(updates)
        print(c('bright_green', "\n  ✓ Email configuration saved!"))

        # Test connection
        test = input(c('cyan', "\n  Test email connection? (yes/no) [yes]: ")).strip().lower()
        if test != 'no':
            self.spinner("Testing SMTP connection...", 2)
            try:
                from email_engine.sender import test_smtp
                ok, msg = test_smtp(smtp_host, int(smtp_port), email, password)
                if ok:
                    print(c('bright_green', "  ✓ SMTP connection successful!"))
                else:
                    print(c('bright_red', f"  ✗ Connection failed: {msg}"))
            except Exception as e:
                print(c('bright_red', f"  ✗ Test failed: {e}"))

        input(c('dim', "\n  Press Enter to return..."))

    def scraping_settings(self):
        """Configure lead scraping settings."""
        self.print_banner()
        self.print_section("LEAD SCRAPING SETTINGS")

        print(c('bright_white', "  Configure lead scraping sources & parameters"))
        print()

        apify_key = self.config.get('apify_api_key', '')
        if not apify_key:
            import getpass
            apify_key = getpass.getpass(prompt=c('cyan', "  Apify API Key: "))
            self.config.save('apify_api_key', apify_key)

        print(c('bright_white', "\n  Active Scraping Sources:"))
        sources = [
            ("scrape_google_maps",   "Google Maps Businesses"),
            ("scrape_startup_dirs",  "Startup Directories"),
            ("scrape_company_dbs",   "Open Company Databases"),
            ("scrape_linkedin_meta", "LinkedIn (metadata only)"),
        ]
        source_updates = {}
        for key, label in sources:
            current = self.config.get(key, 'yes')
            val = input(c('cyan', f"  Enable {label}? (yes/no) [{current}]: ")).strip().lower() or current
            source_updates[key] = val

        print(c('bright_white', "\n  AI Lead Scoring:"))
        min_score = input(c('cyan', "  Minimum lead score to contact (1-10) [6]: ")).strip() or "6"
        source_updates['min_lead_score'] = min_score

        self.config.save_all(source_updates)
        print(c('bright_green', "\n  ✓ Scraping settings saved!"))
        input(c('dim', "\n  Press Enter to return..."))

    def launch_dashboard(self):
        """Launch the web dashboard."""
        self.print_banner()
        self.print_section("WEB DASHBOARD")

        print(c('bright_white', "  Starting HuntAI Dashboard server..."))
        print()

        try:
            import subprocess
            import httpx
            # Check if already running
            try:
                r = httpx.get("http://localhost:3000", timeout=2)
                print(c('bright_green', "  ✓ Dashboard already running at http://localhost:3000"))
            except:
                # Start FastAPI server
                subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "dashboard.api:app",
                     "--host", "0.0.0.0", "--port", "3000", "--reload"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=str(Path(__file__).parent.parent),
                )
                self.spinner("Starting dashboard server...", 3)
                print(c('bright_green', "  ✓ Dashboard started at http://localhost:3000"))

            print(c('cyan', "\n  Open in browser: http://localhost:3000"))
            print(c('dim',  "  The dashboard runs in the background."))

            # Try to open browser
            try:
                import webbrowser
                webbrowser.open("http://localhost:3000")
                print(c('bright_green', "  ✓ Browser opened"))
            except:
                pass

        except Exception as e:
            print(c('bright_red', f"  ✗ Error: {e}"))

        input(c('dim', "\n  Press Enter to return..."))

    def view_history(self):
        """View campaign history and leads."""
        self.print_banner()
        self.print_section("CAMPAIGN HISTORY")

        try:
            from database.db import get_db
            conn = get_db()

            campaigns = conn.execute(
                "SELECT id, name, status, leads_found, emails_sent, replies, created_at FROM campaigns ORDER BY created_at DESC LIMIT 10"
            ).fetchall()

            if not campaigns:
                print(c('dim', "  No campaigns found. Start your first hunt with [01]."))
            else:
                print(c('bright_white', f"  {'ID':<5} {'Campaign':<25} {'Status':<12} {'Leads':<8} {'Emails':<8} {'Replies':<8} {'Date'}"))
                print(c('dim', "  " + "─" * 80))
                for row in campaigns:
                    cid, name, status, leads, emails, replies, created = row
                    status_color = 'bright_green' if status == 'completed' else 'bright_yellow' if status == 'running' else 'dim'
                    print(f"  {c('cyan', str(cid)+''):<5} {name:<25} {c(status_color, status):<12} "
                          f"{c('bright_green', str(leads)):<8} {c('yellow', str(emails)):<8} {c('magenta', str(replies)):<8} {c('dim', str(created)[:10])}")

            print()
            print(c('bright_white', "  Recent Leads:"))
            leads = conn.execute(
                "SELECT company_name, email, industry, location, lead_score FROM leads ORDER BY created_at DESC LIMIT 5"
            ).fetchall()

            if leads:
                print(c('bright_white', f"  {'Company':<25} {'Email':<30} {'Industry':<15} {'Location':<15} {'Score'}"))
                print(c('dim', "  " + "─" * 90))
                for row in leads:
                    company, email, industry, location, score = row
                    score_color = 'bright_green' if score >= 7 else 'yellow' if score >= 5 else 'dim'
                    print(f"  {company:<25} {email:<30} {industry:<15} {location:<15} {c(score_color, str(score))}")
            else:
                print(c('dim', "  No leads yet."))

        except Exception as e:
            print(c('bright_red', f"  ✗ Error loading history: {e}"))

        print()
        export = input(c('cyan', "  Export leads to CSV? (yes/no) [no]: ")).strip().lower()
        if export == 'yes':
            self._export_csv()

        input(c('dim', "\n  Press Enter to return..."))

    def _export_csv(self):
        try:
            from database.db import get_db
            import csv
            conn = get_db()
            leads = conn.execute("SELECT * FROM leads").fetchall()
            cols = [d[0] for d in conn.execute("SELECT * FROM leads LIMIT 1").description] if leads else []
            filename = f"huntai_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(cols)
                w.writerows(leads)
            print(c('bright_green', f"  ✓ Exported to {filename}"))
        except Exception as e:
            print(c('bright_red', f"  ✗ Export failed: {e}"))

    def system_status(self):
        """Show system status."""
        self.print_banner()
        self.print_section("SYSTEM STATUS")

        checks = [
            ("Ollama Service",      self._ping_ollama),
            ("Database",            self._ping_db),
            ("Configuration",       self.config.is_configured),
        ]

        for label, fn in checks:
            self.spinner(f"Checking {label}...", 0.5)
            ok = fn()
            icon = c('bright_green', "✓") if ok else c('bright_red', "✗")
            status = c('bright_green', "ONLINE") if ok else c('bright_red', "OFFLINE")
            print(f"  {icon} {label:<25} {status}")

        # Check Ollama model
        print()
        print(c('bright_white', "  Ollama Models:"))
        try:
            import httpx
            r = httpx.get("http://localhost:11434/api/tags", timeout=3)
            models = r.json().get('models', [])
            if models:
                for m in models:
                    name = m.get('name', 'unknown')
                    size = m.get('size', 0)
                    size_gb = f"{size / 1e9:.1f}GB" if size else "?"
                    icon = c('bright_green', "✓") if 'glm' in name else c('dim', "·")
                    print(f"  {icon} {name:<35} {c('dim', size_gb)}")
            else:
                print(c('dim', "  No models found. Run: ollama pull glm-4:cloud"))
        except:
            print(c('dim', "  Cannot reach Ollama"))

        # Database stats
        print()
        print(c('bright_white', "  Database Statistics:"))
        try:
            from database.db import get_db
            conn = get_db()
            lead_count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            campaign_count = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
            email_count = conn.execute("SELECT COUNT(*) FROM email_log").fetchone()[0]
            print(f"  {c('cyan', '·')} Leads:     {c('bright_green', str(lead_count))}")
            print(f"  {c('cyan', '·')} Campaigns: {c('bright_green', str(campaign_count))}")
            print(f"  {c('cyan', '·')} Emails:    {c('bright_green', str(email_count))}")
        except Exception as e:
            print(c('dim', f"  Database not initialized yet"))

        input(c('dim', "\n  Press Enter to return..."))

    def exit_app(self):
        """Exit the application."""
        self.clear()
        print(c('bright_green', BANNER))
        print()
        print(c('bright_cyan', "  Thanks for using HuntAI. Hunt smart, hunt ethical."))
        print(c('dim', "  Background workers continue running if started."))
        print()
        self.running = False
