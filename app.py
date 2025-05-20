import requests
import json
import io
from flask import Flask, render_template
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
from datetime import datetime
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Initialize Flask app
app = Flask(__name__)

class CryptoDataManager:
    def __init__(self, coin_symbol="BTC", currency="USD", limit=2000):
        self.coin_symbol = coin_symbol.upper()
        self.currency = currency.upper()
        self.limit = limit
        self.url = "https://min-api.cryptocompare.com/data/v2/histoday"
        self.data = None

    def fetch_data(self):
        params = {
            "fsym": self.coin_symbol,
            "tsym": self.currency,
            "limit": self.limit
        }
        try:
            response = requests.get(self.url, params=params)
            response.raise_for_status()
            self.data = response.json().get("Data", {}).get("Data", [])
            return True
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            return False

    def get_prices(self):
        return [entry["close"] for entry in self.data] if self.data else []

    def get_timestamps(self):
        return [entry["time"] for entry in self.data] if self.data else []

    def get_last_price(self):
        return self.data[-1]["close"] if self.data else None

    def get_last_timestamp(self):
        return self.data[-1]["time"] if self.data else None

class Chart:
    @staticmethod
    def create_chart(dates, prices, coin_name):
        plt.style.use('dark_background')
        sns.set_theme(style="darkgrid")
        
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        
        # Style the plot
        ax.set_facecolor('#1e293b')
        fig.patch.set_facecolor('#1e293b')
        
        # Plot data
        ax.fill_between(dates, prices, alpha=0.3, color='#00ff88')
        ax.plot(dates, prices, linewidth=2, color='#00ff88', 
                label=f"{coin_name} Price (USD)")
        
        # Format axes
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'${x:,.2f}'))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.tick_params(axis='both', colors='white', labelsize=10)
        
        # Style elements
        ax.grid(True, linestyle='--', alpha=0.2, color='gray')
        ax.legend(loc='upper left', frameon=True, facecolor='#1e293b',
                 edgecolor='gray', labelcolor='white', fontsize=10)
        
        # Style spines
        for spine in ax.spines.values():
            spine.set_color('gray')
            spine.set_alpha(0.3)

        # Labels
        ax.set_ylabel("Price (USD)", fontsize=12, labelpad=10, color='white')

        plt.tight_layout()
        
        # Save to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        return base64.b64encode(img_buffer.getvalue()).decode()

# Initialize crypto managers
crypto_managers = {
    'bitcoin': CryptoDataManager(coin_symbol="BTC"),
    'ethereum': CryptoDataManager(coin_symbol="ETH"),
    'dogecoin': CryptoDataManager(coin_symbol="DOGE")
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/crypto/<coin_id>")
def crypto_graph(coin_id):
    if coin_id not in crypto_managers:
        return "Invalid cryptocurrency", 404
    
    manager = crypto_managers[coin_id]
    if not manager.fetch_data():
        return "Error fetching data", 500

    # Get data
    timestamps = manager.get_timestamps()
    prices = manager.get_prices()
    dates = [datetime.fromtimestamp(ts) for ts in timestamps]

    # Generate chart
    plot_url = Chart.create_chart(dates, prices, coin_id.title())

    # Calculate statistics
    initial_price = prices[0]
    current_price = prices[-1]
    total_growth = ((current_price - initial_price) / initial_price * 100)
    growth_sign = '+' if total_growth > 0 else ''
    
    return render_template(
        "grafic.html",
        plot_url=plot_url,
        coin_name=coin_id.title(),
        last_price=f"{manager.get_last_price():,.2f}",
        last_timestamp=datetime.fromtimestamp(manager.get_last_timestamp()),
        total_growth=f"{growth_sign}{total_growth:,.2f}%"
    )

if __name__ == "__main__":
    app.run(debug=True, port=8080, host='0.0.0.0')