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

result_label = None
dash_running = False

def display_result(result_text):
    global result_label
    if result_label is None:
        result_label = ctk.CTkLabel(app, text=result_text, font=("Arial", 12))
        result_label.grid(row=4, column=0, columnspan=3, pady=10)
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

    #creating the figure first to apply customizations
    fig = go.Figure(data=[
        go.Scatter(
            x = x_dates,
            y = price,
            mode = 'lines',
            name = ticker,
            line=dict(color='rgb(178, 194, 219)', width=2)
        )
    ])

    #updating layout for better appearance
    fig.update_layout(
        title={
            'text': f"Stock Price Trend for {ticker}",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font' : {'size': 35, 'color': 'white'}
            },

            xaxis_title="Date",
            yaxis_title="Closing Price",
            xaxis = dict(
                showgrid = True,
                gridcolor='rgba(100, 100, 100, 0.5)', #to make grid lines lighter
                color = 'white'
            ),

            yaxis=dict(
            showgrid=True,
            gridcolor='rgba(100, 100, 100, 0.5)',
            color='white' #axis text color
            ),

            font=dict(
                family="Sans-serif, Arial",
                size=20,
                color="white" #default font color
            ),


            paper_bgcolor='rgb(17,17,17)', #match dark theme background
            plot_bgcolor='rgb(17,17,17)',  #match dark theme background
            margin=dict(l=40, r=40, t=60, b=40), #adjusting margins
            hovermode='x unified', #improved hover information display
            template='plotly_dark', #applying a pre-defined dark theme        
        
    )

    dash_app.layout = html.Div([
        dcc.Graph(
            
            id='stock-graph',
            responsive = True,
            figure= fig,
        )
    ])

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    

    dash_app.run(debug=True, use_reloader=False)

def process_input():
    ticker = ticker_entry.get()
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()
    try:
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

        prices = sd.fetch_yahoo_finance_stock_data(ticker, start_date_dt, end_date_dt)

        if prices.empty:
            CTkMessagebox(title="Error", message="No data found for the ticker and date range", icon="cancel")
            return None  # Indicate no data
        
        price_list = prices.squeeze().astype(float).tolist()
        x_dates = prices.index.tolist()

        return {"ticker": ticker, "x_dates": x_dates, "price_list": price_list}  # Return a dictionary
    except ValueError:
        CTkMessagebox(title="Error", message="Invalid date format. Use YYYY-MM-DD.", icon="cancel")
        return None
    except Exception as e:
        CTkMessagebox(title="Error", message=f"An error occurred: {e}", icon="cancel")
        return None

def calculate_and_display(algorithm_name):
    ticker = ticker_entry.get()
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()

    if not ticker or not start_date or not end_date:
        CTkMessagebox(title="Error", message="Please enter all fields!", icon="cancel")
        return

    input_data = process_input()
    if not input_data:
        return  # Exit if process_input failed

    price_list = input_data["price_list"] #list of prices
    x_dates = input_data["x_dates"] #list of dates
    
    if algorithm_name == "greedy":
        profit, buy_date, sell_date = alg.max_profit_with_dates(price_list, x_dates)

        if buy_date and sell_date:
            result_text = f"Greedy Profit: ${profit:.2f} per share\nBuy Date: {buy_date.strftime('%Y-%m-%d')}\nSell Date: {sell_date.strftime('%Y-%m-%d')}"
        else:
            result_text = "Greedy: No profitable trade found."

    elif algorithm_name == "dp":
        profit, buy_date, sell_date = alg.max_profit_dynamic_programming(price_list, x_dates)
        
        if buy_date and sell_date:
            result_text = f"DP Profit: ${profit:.2f} per share\nBuy Date: {buy_date.strftime('%Y-%m-%d')}\nSell Date: {sell_date.strftime('%Y-%m-%d')}"
        else:
            result_text = "DP: No profitable trade found."

    else:
        print("Invalid algorithm name")
        return
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
        return  # Exit if process_input failed

    ticker = input_data["ticker"]
    x_dates = input_data["x_dates"]
    price_list = input_data["price_list"]

    global dash_running  # Use the global flag
    if not dash_running:
        dash_thread = threading.Thread(target=run_dash_app, args=(ticker, x_dates, price_list), daemon=True)
        dash_thread.name = "DashThread"  # Set the thread name
        dash_thread.start()
        dash_running = True  # Set the flag to True
    else:
        open_browser()

#building gui
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
ticker_entry = ctk.CTkEntry(master=app, placeholder_text="e.g., AAPL")
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
run_btn.grid(row=4, column=0, padx=10, pady=10)

dp_btn = ctk.CTkButton(master=app, text="Dynamic Programming", corner_radius=5, command=lambda: calculate_and_display("dp"))
dp_btn.grid(row=4, column=1, padx=10, pady=10)

greedy_btn = ctk.CTkButton(master=app, text="Greedy Algorithm", corner_radius=5, command=lambda: calculate_and_display("greedy"))
greedy_btn.grid(row=4, column=2, padx=10, pady=10)

predict_btn = ctk.CTkButton(master=app, text="Predict", corner_radius=5)
predict_btn.grid(row=4, column=3, padx=10, pady=10)

app.grid_columnconfigure(1, weight=1)

app.mainloop()