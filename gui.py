import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import plotly.graph_objects as go
from dash import Dash, dcc, html
from datetime import datetime
import threading
import time
import webbrowser
from PIL import Image
import stock_data as sd
import alg as alg
import lstm_model as lm

#global variables
result_label = None
dash_running = False
prices = None #storing historical data

lstm_model_obj = None #to store the trained LSTM model
lstm_scalar = None #to store the MinMaxScaler object
lstm_look_back = None #to store the look_back value

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

    #creating the figure first to apply customizations
    fig = go.Figure(data=[
        go.Scatter(
            x = x_dates,
            y = price,
            mode = 'lines',
            name = ticker,
            line=dict(color='rgb(146,32,225)', width=2)
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
                gridcolor='#fcfcfc', #to make grid lines lighter
                color = 'white'
            ),

            yaxis=dict(
            showgrid=True,
            gridcolor='#fcfcfc',
            color='white' #axis text color
            ),

            font=dict(
                family="Sans-serif, Arial",
                size=20,
                color="#fcfcfc" #default font color
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
            return None  # Indicate no data
        
        price_list = prices.squeeze().astype(float).tolist()
        x_dates = prices.index.tolist()

        if not price_list or not x_dates:
            CTkMessagebox(title="Error", message="No data after processing. Check ticker and date range.", icon="cancel")
            return None

        #train the LSTM model
        global lstm_model_obj, lstm_scalar, lstm_look_back 
        lstm_model_obj, lstm_scalar, lstm_look_back = lm.train_lstm_model(prices)

        return {"ticker": ticker, "x_dates": x_dates, "price_list": price_list}  # Return a dictionary
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
        predict_date_str = predict_date_entry.get()
        predict_date = datetime.strptime(predict_date_str, "%Y-%m-%d").date()

        if prices is None or len(prices) == 0:
            CTkMessagebox(title="Error", message="No data available. Generate graph first.", icon="cancel")
            return
        
        if len(prices) < lstm_look_back:
            CTkMessagebox(title="Error", message="Not enough data to make a prediction.", icon="cancel")
            return
        
        '''
        We get the last 'look_back' prices from the training data
        Assuming 'prices' is available from process_input (needs to be fixed)
        This is a place holder
        '''
        last_sequence = prices[-lstm_look_back:].values
        
        #we make the prediction
        predicted_price = lm.predict_lstm_price(lstm_model_obj, lstm_scalar, last_sequence, lstm_look_back)

        #we display the result
        result_text = f"Predicted price for {predict_date_str}: ${predicted_price:.2f}"
        display_result(result_text)
    except ValueError:
        CTkMessagebox(title="Error", message="Invalid date format. Use YYYY-MM-DD.", icon="cancel")
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
app.configure(fg_color="#180a30", corner_radius=0)
app.iconbitmap("./image/icon.ico")
window_width = 750
window_height = 600
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()

x = (screen_width / 2) - (window_width / 2)
y = (screen_height / 2) - (window_height / 2)

app.geometry(f'{window_width}x{window_height}+{int(x)}+{int(y)}')
app.minsize(window_width, window_height)

logo_frame = ctk.CTkFrame(master=app, fg_color = "#180a30")
logo_frame.grid(row=0, column=0, columnspan=4, padx=50, pady=(30, 10), sticky="ew")
logo_image = ctk.CTkImage(light_image=Image.open("./image/logo-new.png"), dark_image=Image.open("./image/logo-new.png"), size=(250, 250))
logo_label = ctk.CTkLabel(master=logo_frame, image=logo_image, text="")
logo_label.pack(pady=5)
#Input fields
input_frame = ctk.CTkFrame(master=app, fg_color="#362257")
input_frame.grid(row=1, column=0, columnspan=4, padx=60, pady=(30,30), sticky="ew")

ctk.CTkLabel(master=input_frame, text="Stock Ticker:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
ticker_entry = ctk.CTkEntry(master=input_frame, placeholder_text="e.g., AAPL", width=200, corner_radius=6)
ticker_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(master=input_frame, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
start_date_entry = ctk.CTkEntry(master=input_frame, placeholder_text="YYYY-MM-DD")
start_date_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(master=input_frame, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
end_date_entry = ctk.CTkEntry(master=input_frame, placeholder_text="YYYY-MM-DD")
end_date_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(master=input_frame, text="Predict Date (YYYY-MM-DD):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
predict_date_entry = ctk.CTkEntry(master=input_frame, placeholder_text="YYYY-MM-DD")
predict_date_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

input_frame.grid_columnconfigure(1, weight=1)
input_frame.grid_rowconfigure(3, weight=1)

button_frame = ctk.CTkFrame(master=app, fg_color="#362257")
button_frame.grid(row=2, column=0, columnspan=4, padx=50, pady=(5,10), sticky="ew")

run_btn = ctk.CTkButton(master=button_frame, text="Graph", corner_radius=5, command=generate_graph, fg_color="#9220e1", text_color="white", hover_color="#bf58e4")
run_btn.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

dp_btn = ctk.CTkButton(master=button_frame, text="Dynamic Programming", corner_radius=5, command=lambda: calculate_and_display("dp"),fg_color="#9220e1", text_color="white", hover_color="#bf58e4")
dp_btn.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

greedy_btn = ctk.CTkButton(master=button_frame, text="Greedy Algorithm", corner_radius=5, command=lambda: calculate_and_display("greedy"),fg_color="#9220e1", text_color="white", hover_color="#bf58e4")
greedy_btn.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

predict_btn = ctk.CTkButton(master=button_frame, text="Predict", corner_radius=5, command=predict_price, fg_color="#9220e1", text_color="white", hover_color="#bf58e4")
predict_btn.grid(row=0, column=3, padx=10, pady=5, sticky="ew")

button_frame.grid_columnconfigure(0, weight=1)
button_frame.grid_columnconfigure(1, weight=1)
button_frame.grid_columnconfigure(2, weight=1)
button_frame.grid_columnconfigure(3, weight=1)

app.grid_columnconfigure(0, weight=1)

from datetime import date, timedelta
today = date.today()
year_ago = today - timedelta(days=365)
start_date_entry.insert(0, year_ago.strftime("%Y-%m-%d"))
end_date_entry.insert(0, today.strftime("%Y-%m-%d"))
predict_date_entry.insert(0, (today + timedelta(days=1)).strftime("%Y-%m-%d"))

app.mainloop()
