import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import plotly.graph_objects as go
from dash import Dash, dcc, html
from datetime import datetime
import threading
import time
import webbrowser

import stock_data as sd
import alg as alg
import lstm_model as lm

result_label = None
dash_running = False
prices = None

lstm_model_obj = None
lstm_scalar = None
lstm_look_back = None

def display_result(result_text):
    global result_label
    if result_label is None:
        result_label = ctk.CTkLabel(app, text=result_text, font=("Arial", 12), wraplength=500, justify="left")
        result_label.grid(row=5, column=0, columnspan=5, pady=(10,5), padx=10, sticky="w")
    else:
        result_label.configure(text=result_text)

def open_browser():
    try:
        time.sleep(1.5)
        webbrowser.open_new("http://127.0.0.1:8050/")
    except Exception as e:
        print(f"Error opening browser: {e}")

def run_dash_app(ticker, x_dates, price):
    dash_app = Dash(__name__)

    fig = go.Figure(data=[
        go.Scatter(
            x=x_dates,
            y=price,
            mode='lines',
            name=ticker,
            line=dict(width=2)
        )
    ])

    fig.update_layout(
        title={
            'text': f"Stock Price Trend for {ticker}",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 35, 'color': 'white'}
        },
        xaxis_title="Date",
        yaxis_title="Closing Price",
        xaxis=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', color='white'),
        yaxis=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', color='white'),
        font=dict(family="Sans-serif, Arial", size=20, color="white"),
        paper_bgcolor='rgb(17,17,17)',
        plot_bgcolor='rgb(17,17,17)',
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode='x unified',
        template='plotly_dark'
    )

    dash_app.layout = html.Div([
        dcc.Graph(id='stock-graph', responsive=True, figure=fig)
    ])

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    dash_app.run(debug=True, use_reloader=False)

def process_input():
    global prices
    ticker = ticker_entry.get().strip()
    start_date = start_date_entry.get().strip()
    end_date = end_date_entry.get().strip()

    try:
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

        prices = sd.fetch_yahoo_finance_stock_data(ticker, start_date_dt, end_date_dt)

        if prices.empty:
            CTkMessagebox(title="Error", message="No data found for the ticker and date range", icon="cancel")
            return None

        price_list = prices.squeeze().astype(float).tolist()
        x_dates = prices.index.tolist()

        if not price_list or not x_dates:
            CTkMessagebox(title="Error", message="No data after processing. Check ticker and date range.", icon="cancel")
            return None

        global lstm_model_obj, lstm_scalar, lstm_look_back
        lstm_model_obj, lstm_scalar, lstm_look_back = lm.train_lstm_model(prices)

        return {"ticker": ticker, "x_dates": x_dates, "price_list": price_list}
    except ValueError:
        CTkMessagebox(title="Error", message="Invalid date format. Use YYYY-MM-DD.", icon="cancel")
        prices = None
        return None
    except Exception as e:
        CTkMessagebox(title="Error", message=f"An error occurred: {e}", icon="cancel")
        prices = None
        return None

def predict_price():
    global lstm_model_obj, lstm_scalar, lstm_look_back, prices

    if lstm_model_obj is None or lstm_scalar is None or lstm_look_back is None:
        CTkMessagebox(title="Error", message="LSTM model not trained. Generate graph first.", icon="cancel")
        return

    try:
        if prices is None or len(prices) == 0:
            CTkMessagebox(title="Error", message="No data available. Generate graph first.", icon="cancel")
            return

        if len(prices) < lstm_look_back:
            CTkMessagebox(title="Error", message="Not enough data to make a prediction.", icon="cancel")
            return

        last_sequence = prices[-lstm_look_back:].values
        predicted_price = lm.predict_lstm_price(lstm_model_obj, lstm_scalar, last_sequence, lstm_look_back)

        if predicted_price is not None:
            result_text = f"Predicted next price: ${predicted_price:.2f}"
            display_result(result_text)
        else:
            CTkMessagebox(title="Prediction Failed", message="Prediction failed. Please try again.", icon="cancel")

    except Exception as e:
        CTkMessagebox(title="Error", message=f"An error occurred: {e}", icon="cancel")

def calculate_and_display(algorithm_name):
    ticker = ticker_entry.get()
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()

    if not ticker or not start_date or not end_date:
        CTkMessagebox(title="Error", message="Please enter all fields!", icon="cancel")
        return

    input_data = process_input()
    if not input_data:
        return

    price_list = input_data["price_list"]
    x_dates = input_data["x_dates"]

    if algorithm_name == "greedy":
        profit, buy_date, sell_date = alg.max_profit_with_dates(price_list, x_dates)
    elif algorithm_name == "dp":
        profit, buy_date, sell_date = alg.max_profit_dynamic_programming(price_list, x_dates)
    else:
        print("Invalid algorithm name")
        return

    if buy_date and sell_date:
        result_text = f"{algorithm_name.upper()} Profit: ${profit:.2f}\nBuy: {buy_date.strftime('%Y-%m-%d')}\nSell: {sell_date.strftime('%Y-%m-%d')}"
    else:
        result_text = f"{algorithm_name.upper()}: No profitable trade found."

    display_result(result_text)

def generate_graph():
    ticker = ticker_entry.get()
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()

    if not ticker or not start_date or not end_date:
        CTkMessagebox(title="Error", message="Please enter all fields!", icon="cancel")
        return

    input_data = process_input()
    if not input_data:
        return

    ticker = input_data["ticker"]
    x_dates = input_data["x_dates"]
    price_list = input_data["price_list"]

    global dash_running
    if not dash_running:
        dash_thread = threading.Thread(target=run_dash_app, args=(ticker, x_dates, price_list), daemon=True)
        dash_thread.name = "DashThread"
        dash_thread.start()
        dash_running = True
    else:
        open_browser()

app = ctk.CTk()
app.title("Stock Market Predictor")
ctk.set_appearance_mode("dark")

window_width = 600
window_height = 500
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()

x = (screen_width / 2) - (window_width / 2)
y = (screen_height / 2) - (window_height / 2)

app.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')

ctk.CTkLabel(master=app, text="Stock Ticker:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
ticker_entry = ctk.CTkEntry(master=app, placeholder_text="e.g., AAPL", width=200, corner_radius=6)
ticker_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(master=app, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
start_date_entry = ctk.CTkEntry(master=app, placeholder_text="YYYY-MM-DD")
start_date_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(master=app, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
end_date_entry = ctk.CTkEntry(master=app, placeholder_text="YYYY-MM-DD")
end_date_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(master=app, text="Predict Date (YYYY-MM-DD):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
predict_date_entry = ctk.CTkEntry(master=app, placeholder_text="YYYY-MM-DD")
predict_date_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

run_btn = ctk.CTkButton(master=app, text="Graph", corner_radius=5, command=generate_graph)
run_btn.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

dp_btn = ctk.CTkButton(master=app, text="Dynamic Programming", corner_radius=5, command=lambda: calculate_and_display("dp"))
dp_btn.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

greedy_btn = ctk.CTkButton(master=app, text="Greedy Algorithm", corner_radius=5, command=lambda: calculate_and_display("greedy"))
greedy_btn.grid(row=4, column=2, padx=10, pady=5, sticky="ew")

predict_btn = ctk.CTkButton(master=app, text="Predict", corner_radius=5, command=predict_price)
predict_btn.grid(row=4, column=3, padx=10, pady=5, sticky="ew")

app.grid_columnconfigure(1, weight=1)

app.mainloop()
