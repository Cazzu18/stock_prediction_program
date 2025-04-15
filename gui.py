import customtkinter as ctk
from customtkinter import *
from CTkMessagebox import CTkMessagebox
import plotly.graph_objects as go
from dash import Dash, dcc, html
from datetime import datetime
import threading
import time
import webbrowser

import stock_data as sd
import alg as alg


def display_result(result_text):
    app.after(0, lambda: result_label.configure(text=result_text))


result_label = None

def open_browser():
    try:
        time.sleep(1.5)
        webbrowser.open_new("http://127.0.0.1:8050/")
    except Exception as e:
        print(f"Error opening browser: {e}")
        

def run_dash_app(ticker, x_dates, price):
    dash_app = Dash(__name__)

    #create the figure first to apply customizations
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
                showgrid = True, #because 
                gridcolor='rgba(100, 100, 100, 0.5)', # to make grid lines lighter
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
            template='plotly_dark', # Apply a pre-defined dark theme        
        
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


def perform_analysis():
    global result_label
    ticker = ticker_entry.get()
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()

    if not ticker or not start_date or not end_date:
        CTkMessagebox(title="Error", message="Please enter all fields!", icon="cancel")
        return
    try:
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

        prices = sd.fetch_yahoo_finance_stock_data(ticker, start_date_dt, end_date_dt)

        if prices.empty:
            CTkMessagebox(title="Error", message="No data found for the ticker and date range", icon="cancel")
            return

        price_list = prices.squeeze().astype(float).tolist()

        greedy_profit = float(alg.max_profit_greedy_algorithm(price_list))
        dp_profit = float(alg.max_profit_dynamic_proigramming(price_list))

        result_text = f"Greedy Profit: ${greedy_profit:.2f}\nDP Profit: ${dp_profit:.2f}"
        if result_label is None:
            result_label = ctk.CTkLabel(app, text=result_text, font=("Arial", 12))
            result_label.grid(row=4, column=0, columnspan=2, pady=10)
        else:
            result_label.configure(text=result_text)

        x_dates = prices.index.tolist()
        

        #checking if a dash thread is already running
        dash_running = False
        for t in threading.enumerate():
            if hasattr(t, 'name') and t.name == 'DashThread':
                dash_running = True
                break

        if not dash_running:
            dash_thread = threading.Thread(target=run_dash_app, args=(ticker, x_dates, price_list), daemon=True)
            dash_thread.start()
        else:
            open_browser()

    except Exception as e:
        CTkMessagebox(title="Error", message=str(e), icon="cancel")


app = CTk()
app.title("Stock Market Predictor")
set_appearance_mode("dark")

window_width = 600
window_height = 500
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()

x = (screen_width / 2) - (window_width / 2)
y = (screen_height / 2) - (window_height / 2)

app.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')

ctk.CTkLabel(master=app, text="Stock Ticker:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
ticker_entry = CTkEntry(master=app, placeholder_text="e.g., AAPL")
ticker_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(master=app, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
start_date_entry = CTkEntry(master=app, placeholder_text="YYYY-MM-DD")
start_date_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(master=app, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
end_date_entry = CTkEntry(master=app, placeholder_text="YYYY-MM-DD")
end_date_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

run_btn = CTkButton(master=app, text="Run Analysis & Show Plot", corner_radius=5, command=perform_analysis)
run_btn.grid(row=3, column=0, columnspan=2, pady=20)

app.grid_columnconfigure(1, weight=1)

app.mainloop()