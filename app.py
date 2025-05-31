# Importăm biblioteca requests pentru a face cereri HTTP
import requests

# Biblioteca io pentru a manipula imaginile în memorie (ca un fișier temporar în RAM)
import io

# Importăm Flask și funcțiile pentru a reda pagini HTML
from flask import Flask, render_template # Flask este framework-ul web, render_template încarcă fișiere HTML

# Pentru a converti imaginea generată în cod base64 (text care reprezintă date binare)
import base64

# Biblioteci pentru desenarea graficelor
import matplotlib.pyplot as plt # Pyplot este interfața principală pentru crearea graficelor
import matplotlib # Biblioteca Matplotlib principală

# Folosim backend-ul 'Agg' pentru a desena grafice fără interfață grafică (necesar pentru servere)
matplotlib.use('Agg') # 'Agg' este un backend care nu necesită un server X sau un display

# Pentru conversia timestamp-urilor (numere) în date calendaristice lizibile
import matplotlib.dates as mdates # Modul pentru formatarea datelor pe axele graficului
from datetime import datetime # Clasa pentru lucrul cu date și timp

# Seaborn pentru stiluri vizuale mai elegante în grafice, bazat pe Matplotlib
import seaborn as sns

# Pentru formatarea axei Y (ex: $1,000) cu funcții personalizate
from matplotlib.ticker import FuncFormatter

# Inițializăm aplicația Flask; __name__ ajută Flask să localizeze resursele (template-uri, fișiere statice)
app = Flask(__name__)

# Clasa care gestionează datele despre criptomonede
class CryptoDataManager:
    # Constructorul clasei, se apelează la crearea unui nou obiect CryptoDataManager
    def __init__(self, coin_symbol="BTC", currency="USD", limit=2000):
        # Setăm simbolul monedei (ex: BTC), convertit la majuscule
        self.coin_symbol = coin_symbol.upper()
        # Setăm valuta (ex: USD), convertită la majuscule
        self.currency = currency.upper()
        # Setăm limita de zile pentru datele istorice
        self.limit = limit
        # URL-ul API-ului CryptoCompare pentru date istorice zilnice
        self.url = "https://min-api.cryptocompare.com/data/v2/histoday"
        # Inițializăm atributul 'data' unde vom stoca datele primite; None la început
        self.data = None

    # Metodă pentru a prelua datele de la API
    def fetch_data(self):
        # Setăm parametrii pentru cererea API
        params = {
            "fsym": self.coin_symbol,  # moneda de bază (ex: BTC)
            "tsym": self.currency,     # moneda țintă (ex: USD)
            "limit": self.limit        # numărul de zile înapoi pentru care se cer date
        }
        try:
            # Trimitem cererea HTTP GET către URL-ul API cu parametrii specificați
            response = requests.get(self.url, params=params)
            # Verificăm dacă răspunsul HTTP are un cod de eroare (ex: 404, 500)
            # Dacă da, ridică o excepție HTTPError
            response.raise_for_status()

            # Parsăm răspunsul JSON și extragem datele relevante
            # Răspunsul JSON are o structură, iar datele sunt în response_json["Data"]["Data"]
            # .get() este folosit pentru a evita KeyError dacă o cheie lipsește
            self.data = response.json().get("Data", {}).get("Data", [])
            return True # Returnăm True dacă datele au fost preluate cu succes
        except requests.RequestException as e: # Prindem orice excepție legată de cererea HTTP
            # Afișăm eroarea în consolă
            print(f"Error fetching data: {e}")
            return False # Returnăm False dacă a apărut o eroare

    # Metodă pentru a returna o listă cu prețurile de închidere (closing prices)
    def get_prices(self):
        # Folosim o list comprehension pentru a extrage valoarea 'close' din fiecare intrare din self.data
        # Verificăm dacă self.data nu este None (are date) înainte de a încerca extragerea
        return [entry["close"] for entry in self.data] if self.data else []

    # Metodă pentru a returna o listă cu timestamp-urile corespunzătoare fiecărui preț
    def get_timestamps(self):
        # Similar cu get_prices, extragem valoarea 'time' (timestamp Unix)
        return [entry["time"] for entry in self.data] if self.data else []

    # Metodă pentru a returna ultimul preț disponibil din listă
    def get_last_price(self):
        # self.data[-1] accesează ultimul element din listă, apoi ["close"] accesează prețul de închidere
        return self.data[-1]["close"] if self.data else None

    # Metodă pentru a returna ultimul timestamp disponibil
    def get_last_timestamp(self):
        # self.data[-1] accesează ultimul element, apoi ["time"] accesează timestamp-ul
        return self.data[-1]["time"] if self.data else None

# Clasa pentru generarea graficelor
class Chart:
    # Metodă statică: poate fi apelată direct pe clasă (Chart.create_chart) fără a crea un obiect Chart
    @staticmethod
    def create_chart(dates, prices, coin_name):
        # Setăm tema întunecată pentru fundalul graficului folosind stilurile Matplotlib
        plt.style.use('dark_background')
        # Setăm o temă Seaborn pentru un aspect mai plăcut, cu un grid întunecat
        sns.set_theme(style="darkgrid")

        # Cream figura (containerul principal) și axa (zona unde se desenează graficul)
        # figsize setează dimensiunea figurii în inch, dpi setează rezoluția (dots per inch)
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

        # Setăm culoarea de fundal pentru axă (zona de desenare)
        ax.set_facecolor('#1e293b') # Un albastru-gri închis
        # Setăm culoarea de fundal pentru întreaga figură
        fig.patch.set_facecolor('#1e293b')

        # Umplem zona de sub graficul liniei cu o culoare semi-transparentă
        # alpha controlează transparența (0=transparent, 1=opac)
        ax.fill_between(dates, prices, alpha=0.3, color='#00ff88') # Un verde deschis

        # Trasăm linia graficului (prețurile în funcție de date)
        # linewidth setează grosimea liniei, color setează culoarea
        # label este textul care va apărea în legendă pentru această linie
        ax.plot(dates, prices, linewidth=2, color='#00ff88',
                label=f"{coin_name} Price (USD)")

        # Formatăm axa Y să afișeze valorile ca dolari cu două zecimale (ex: $1,234.56)
        # FuncFormatter aplică o funcție lambda pentru a formata fiecare etichetă de pe axa Y
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'${x:,.2f}'))

        # Formatăm axa X să afișeze doar anul din datele calendaristice
        # mdates.DateFormatter('%Y') specifică formatul 'Anul' (ex: 2023)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        # Setăm culoarea textului etichetelor de pe ambele axe (X și Y) la alb și dimensiunea fontului
        ax.tick_params(axis='both', colors='white', labelsize=10)

        # Adăugăm o grilă subtilă pe grafic pentru lizibilitate
        # linestyle face liniile întrerupte, alpha le face semi-transparente
        ax.grid(True, linestyle='--', alpha=0.2, color='gray')

        # Adăugăm legenda graficului în colțul din stânga sus
        # frameon desenează un chenar în jurul legendei
        # facecolor, edgecolor, labelcolor stilizează legenda
        ax.legend(loc='upper left', frameon=True, facecolor='#1e293b',
                  edgecolor='gray', labelcolor='white', fontsize=10)

        # Setăm culoarea și transparența chenarului (marginilor) graficului
        for spine in ax.spines.values(): # Iterăm prin cele 4 margini (sus, jos, stânga, dreapta)
            spine.set_color('gray') # Culoarea marginii
            spine.set_alpha(0.3) # Transparența marginii

        # Setăm eticheta axei Y, cu dimensiunea fontului, spațiul față de axă și culoarea textului
        ax.set_ylabel("Price (USD)", fontsize=12, labelpad=10, color='white')

        # Aranjăm elementele graficului pentru a nu se suprapune (ajustează automat spațiile)
        plt.tight_layout()

        # Salvăm graficul într-un buffer în memorie ca imagine PNG
        img_buffer = io.BytesIO() # Cream un buffer binar în memorie
        # plt.savefig salvează figura; format='png', dpi pentru rezoluție, bbox_inches='tight' elimină spațiul alb în exces
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0) # Resetăm cursorul bufferului la început pentru a putea citi conținutul
        plt.close(fig) # Închidem figura Matplotlib pentru a elibera memoria (foarte important pe servere!)

        # Convertim imaginea PNG din buffer în cod base64 (șir de caractere)
        # .getvalue() ia conținutul binar al bufferului
        # base64.b64encode() îl transformă în base64 (bytes)
        # .decode() transformă bytes în string UTF-8, care poate fi inclus în HTML
        return base64.b64encode(img_buffer.getvalue()).decode()

# Inițializăm managerii pentru fiecare criptomonedă pe care o suportăm
# Cheile (ex: 'bitcoin') vor fi folosite în URL-uri
crypto_managers = {
    'bitcoin': CryptoDataManager(coin_symbol="BTC"), # Manager pentru Bitcoin
    'ethereum': CryptoDataManager(coin_symbol="ETH"), # Manager pentru Ethereum
    'dogecoin': CryptoDataManager(coin_symbol="DOGE") # Manager pentru Dogecoin
}

# Ruta principală a aplicației (ex: http://localhost:8080/)
@app.route("/")
def home():
    # Redăm (trimitem către browser) fișierul HTML numit 'index.html'
    # Acest fișier trebuie să existe într-un folder numit 'templates' în același director cu app.py
    return render_template("index.html")

# Ruta pentru afișarea graficului unei criptomonede specifice
# <coin_id> este o variabilă în URL (ex: /crypto/bitcoin)
@app.route("/crypto/<coin_id>")
def crypto_graph(coin_id): # coin_id va primi valoarea din URL (ex: "bitcoin")
    # Verificăm dacă criptomoneda cerută este în lista noastră de manageri suportați
    if coin_id not in crypto_managers:
        return "Invalid cryptocurrency", 404 # Returnăm eroare 404 (Not Found) dacă nu este suportată

    # Luăm managerul de date corespunzător pentru moneda cerută din dicționar
    manager = crypto_managers[coin_id]

    # Încercăm să preluăm datele de la API folosind managerul
    if not manager.fetch_data(): # Dacă fetch_data() returnează False (a apărut o eroare)
        return "Error fetching data", 500 # Returnăm eroare 500 (Internal Server Error)

    # Obținem timestamp-urile și prețurile de la manager
    timestamps = manager.get_timestamps()
    prices = manager.get_prices()

    # Verificăm dacă avem date valide pentru a crea graficul
    if not timestamps or not prices:
        return "Not enough data to generate chart", 500

    # Convertim timestamp-urile (numere) în obiecte datetime (mai ușor de folosit de Matplotlib)
    dates = [datetime.fromtimestamp(ts) for ts in timestamps]

    # Generăm graficul folosind clasa Chart și metoda create_chart
    # coin_id.title() capitalizează numele monedei (ex: "bitcoin" -> "Bitcoin")
    plot_url = Chart.create_chart(dates, prices, coin_id.title())

    # Calculăm creșterea totală a prețului pe perioada afișată
    initial_price = prices[0] # Primul preț din serie
    current_price = prices[-1] # Ultimul preț din serie
    # Formula pentru procentul de creștere/scădere
    total_growth = ((current_price - initial_price) / initial_price * 100)
    # Adăugăm semnul '+' dacă creșterea este pozitivă, pentru afișare
    growth_sign = '+' if total_growth > 0 else ''

    # Redăm pagina HTML 'grafic.html', trimițându-i datele necesare
    # Aceste variabile vor fi accesibile în interiorul fișierului grafic.html (folosind sintaxa Jinja2, ex: {{ coin_name }})
    return render_template(
        "grafic.html",
        plot_url=plot_url, # Imaginea graficului codificată în base64
        coin_name=coin_id.title(), # Numele monedei
        last_price=f"{manager.get_last_price():,.2f}", # Ultimul preț, formatat
        last_timestamp=datetime.fromtimestamp(manager.get_last_timestamp()), # Ultimul timestamp, ca obiect datetime
        total_growth=f"{growth_sign}{total_growth:,.2f}%" # Creșterea totală, formatată
    )

# Blocul care pornește serverul Flask dacă scriptul este executat direct
# (nu dacă este importat ca modul în alt script)
if __name__ == "__main__":
    app.run(debug=True, port=8080, host='0.0.0.0')