import customtkinter as ctk
from customtkinter import *
from CTkMessagebox import CTkMessagebox
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

import stock_data as sd
import alg as alg


def display_result(result_text):
    result_label = ctk.CTkLabel(app, text=result_text, font=("Arial", 12))
    result_label.grid(row=4, column=0, columnspan=2)

def perform_analysis():
    ticker = ticker_entry.get()
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()

    if(not ticker or not start_date or not end_date):
        CTkMessagebox(title="Error", message="Please enter all fields!", icon="cancel")
        return
    try:
        #converting start and end date to datetime objects
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        #fetch stock data
        prices = sd.fetch_yahoo_finance_stock_data(ticker, start_date, end_date)
            
        if prices.empty:
            CTkMessagebox(title="Error", message="No data found for the ticker and date range", icon="cancel")
            return
        
        #converting pandas series to a list of floats
        price = prices.squeeze().astype(float).tolist()
        
        #debugging print statements
        print(prices)
        print(type(prices))

        #calculating profits
        greedy_profit = float(alg.max_profit_greedy_algorithm(price))
        dp_profit = float(alg.max_profit_dynamic_proigramming(price))

        #displaying results
        display_result(f"Greedy Profit: ${greedy_profit:.2f}\nDP Profit: ${dp_profit:.2f}")
        
        #create an interactice plotly figure
        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(go.Scatter(x=prices.index, y = prices.values, mode='lines', name=ticker, line=dict(color='blue')))
        fig.update_layout(title=f"Stock Price Trend for {ticker}", xaxis_title="Date", yaxis_title="Closing Price")
        fig.show()

    except Exception as e:
        CTkMessagebox(title="Error", message=str(e), icon="cancel")

#creating window and declaring specifications
app = CTk()
app.geometry("500x400")
app.title("Stock Market Predictor")
set_appearance_mode("dark")

#labels and entry fields
ctk.CTkLabel(master=app, text="Stock Ticker").grid(row=0,column=0)
ticker_entry = CTkEntry(master=app, placeholder_text="Ticker")
ticker_entry.grid(row=0, column = 0)

ctk.CTkLabel(master=app, text="Start Date (YYYY-MM-DD):").grid(row=1,column=0)
start_date_entry = CTkEntry(master=app, placeholder_text="Start Date")
start_date_entry.grid(row=1, column = 1)

ctk.CTkLabel(master=app, text="End Date (YYYY-MM-DD):").grid(row=2,column=0)
end_date_entry = CTkEntry(master=app, placeholder_text="End Date")
end_date_entry.grid(row=2, column = 1)

#run analysis button
run_btn = CTkButton(master=app, text="Run", corner_radius=32, fg_color="#515357", hover_color="#202121", command=perform_analysis)
run_btn.grid(row=3, column=0, columnspan = 2)
#run_btn.place(relx=0.5, rely=0.5, anchor="center")

#RUN GUI
app.mainloop()