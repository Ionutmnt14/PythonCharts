# Importăm biblioteca requests pentru a face cereri HTTP
import requests

# Biblioteca io pentru a manipula imaginile în memorie
import io

# Importăm Flask și funcțiile pentru a reda pagini HTML
from flask import Flask, render_template

# Pentru a converti imaginea generată în cod base64
import base64

# Biblioteci pentru desenarea graficelor
import matplotlib.pyplot as plt
import matplotlib

# Folosim backend-ul 'Agg' pentru a desena grafice fără interfață grafică
matplotlib.use('Agg')

# Pentru conversia timestamp-urilor în date calendaristice
import matplotlib.dates as mdates
from datetime import datetime

# Seaborn pentru stiluri vizuale mai elegante în grafice
import seaborn as sns

# Pentru formatarea axei Y (ex: $1,000)
from matplotlib.ticker import FuncFormatter

# Inițializăm aplicația Flask
app = Flask(__name__)

# Clasa care gestionează datele despre criptomonede
class CryptoDataManager:
    def __init__(self, coin_symbol="BTC", currency="USD", limit=2000):
        # Setăm simbolul monedei, valuta și limita de date istorice
        self.coin_symbol = coin_symbol.upper()
        self.currency = currency.upper()
        self.limit = limit
        self.url = "https://min-api.cryptocompare.com/data/v2/histoday"
        self.data = None

    def fetch_data(self):
        # Setăm parametrii pentru API
        params = {
            "fsym": self.coin_symbol,  # moneda de bază
            "tsym": self.currency,     # moneda țintă (USD)
            "limit": self.limit        # numărul de zile înapoi
        }
        try:
            # Trimitem cererea HTTP
            response = requests.get(self.url, params=params)
            response.raise_for_status()  # ridică eroare dacă status != 200

            # Salvăm doar datele din răspuns
            self.data = response.json().get("Data", {}).get("Data", [])
            return True
        except requests.RequestException as e:
            # Afișăm eroarea și returnăm False
            print(f"Error fetching data: {e}")
            return False

    def get_prices(self):
        # Returnează o listă cu prețurile de închidere (closing prices)
        return [entry["close"] for entry in self.data] if self.data else []

    def get_timestamps(self):
        # Returnează o listă cu timestamp-urile corespunzătoare
        return [entry["time"] for entry in self.data] if self.data else []

    def get_last_price(self):
        # Returnează ultimul preț disponibil
        return self.data[-1]["close"] if self.data else None

    def get_last_timestamp(self):
        # Returnează ultimul timestamp disponibil
        return self.data[-1]["time"] if self.data else None

# Clasa pentru generarea graficelor
class Chart:
    @staticmethod
    def create_chart(dates, prices, coin_name):
        # Setăm tema întunecată pentru fundal
        plt.style.use('dark_background')
        sns.set_theme(style="darkgrid")

        # Cream figura și axa
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

        # Setăm culorile de fundal pentru figură și axă
        ax.set_facecolor('#1e293b')
        fig.patch.set_facecolor('#1e293b')

        # Umplem zona de sub grafic cu o culoare transparentă
        ax.fill_between(dates, prices, alpha=0.3, color='#00ff88')

        # Trasăm linia graficului
        ax.plot(dates, prices, linewidth=2, color='#00ff88', 
                label=f"{coin_name} Price (USD)")

        # Formatăm axa Y să afișeze dolari cu două zecimale
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'${x:,.2f}'))

        # Formatăm axa X să afișeze doar anul
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        # Setăm culoarea textului axelor
        ax.tick_params(axis='both', colors='white', labelsize=10)

        # Adăugăm o grilă subtilă
        ax.grid(True, linestyle='--', alpha=0.2, color='gray')

        # Legenda în colțul din stânga sus
        ax.legend(loc='upper left', frameon=True, facecolor='#1e293b',
                  edgecolor='gray', labelcolor='white', fontsize=10)

        # Setăm culoarea chenarului (spines)
        for spine in ax.spines.values():
            spine.set_color('gray')
            spine.set_alpha(0.3)

        # Eticheta axei Y
        ax.set_ylabel("Price (USD)", fontsize=12, labelpad=10, color='white')

        # Aranjăm bine spațiile
        plt.tight_layout()

        # Salvăm graficul în memorie ca imagine PNG
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)

        # Convertim imaginea PNG în cod base64 pentru a o afișa în HTML
        return base64.b64encode(img_buffer.getvalue()).decode()

# Inițializăm managerii pentru fiecare criptomonedă
crypto_managers = {
    'bitcoin': CryptoDataManager(coin_symbol="BTC"),
    'ethereum': CryptoDataManager(coin_symbol="ETH"),
    'dogecoin': CryptoDataManager(coin_symbol="DOGE")
}

# Ruta principală care afișează pagina de start
@app.route("/")
def home():
    return render_template("index.html")

# Ruta pentru afișarea graficului unei criptomonede
@app.route("/crypto/<coin_id>")
def crypto_graph(coin_id):
    # Verificăm dacă criptomoneda este suportată
    if coin_id not in crypto_managers:
        return "Invalid cryptocurrency", 404

    # Luăm managerul pentru moneda cerută
    manager = crypto_managers[coin_id]

    # Dacă nu reușim să obținem date, returnăm eroare
    if not manager.fetch_data():
        return "Error fetching data", 500

    # Obținem timestamp-urile și prețurile
    timestamps = manager.get_timestamps()
    prices = manager.get_prices()

    # Convertim timestamp-urile în obiecte datetime
    dates = [datetime.fromtimestamp(ts) for ts in timestamps]

    # Generăm graficul și obținem codul base64
    plot_url = Chart.create_chart(dates, prices, coin_id.title())

    # Calculăm creșterea totală a prețului
    initial_price = prices[0]
    current_price = prices[-1]
    total_growth = ((current_price - initial_price) / initial_price * 100)
    growth_sign = '+' if total_growth > 0 else ''

    # Redăm pagina HTML cu graficul și informațiile despre criptomonedă
    return render_template(
        "grafic.html",
        plot_url=plot_url,
        coin_name=coin_id.title(),
        last_price=f"{manager.get_last_price():,.2f}",
        last_timestamp=datetime.fromtimestamp(manager.get_last_timestamp()),
        total_growth=f"{growth_sign}{total_growth:,.2f}%"
    )

# Pornim serverul Flask
if __name__ == "__main__":
    app.run(debug=True, port=8080, host='0.0.0.0')
