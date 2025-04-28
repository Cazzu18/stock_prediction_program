import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

def create_lstm_model(x_train, y_train, look_back=1):
    model = Sequential()
    model.add(LSTM(60, activation='tanh', input_shape=(look_back, x_train.shape[2]), return_sequences=True))
    model.add(Dropout(0.3))
    model.add(LSTM(120, activation='tanh'))
    model.add(Dropout(0.3))
    model.add(Dense(20))
    model.add(Dense(1))
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    return model

def prepare_lstm_data(data, look_back=1):
    if len(data) <= look_back:
        raise ValueError(f"Data length ({len(data)}) must be greater than look_back ({look_back})")
    x, y = [], []
    for i in range(len(data) - look_back):
        a = data[i:(i + look_back), 0:]
        x.append(a)
        y.append(data[i + look_back, 0])
    return np.array(x), np.array(y)

def train_lstm_model(prices):
    scaler = MinMaxScaler(feature_range=(0, 1))
    try:
        scaled_data = scaler.fit_transform(prices.values.reshape(-1, 1))
    except Exception as e:
        print(f"Error in MinMaxScaler: {e}")
        return None, None, None

    look_back = 10
    x, y = prepare_lstm_data(scaled_data, look_back)
    x = np.reshape(x, (x.shape[0], x.shape[1], 1))

    train_size = int(len(x) * 0.8)
    x_train, x_test = x[0:train_size], x[train_size:len(x)]
    y_train, y_test = y[0:train_size], y[train_size:len(y)]

    model = create_lstm_model(x_train, y_train, look_back)
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    checkpoint = ModelCheckpoint('best_lstm_model.h5', monitor='val_loss', save_best_only=True)

    model.fit(x_train, y_train, batch_size=32, epochs=100, verbose=0, callbacks=[early_stop, checkpoint])

    return model, scaler, look_back

def predict_lstm_price(model, scaler, last_sequence, look_back):
    try:
        # Scale the input sequence
        scaled_last_sequence = scaler.transform(last_sequence.reshape(-1, 1))

        # Reshape input for LSTM model
        x = scaled_last_sequence.reshape((1, look_back, 1))

        # Predict
        scaled_prediction = model.predict(x, verbose=0)

        # Inverse transform to get original price
        predicted_price = scaler.inverse_transform(scaled_prediction)[0][0]

        return predicted_price
    except Exception as e:
        print(f"Prediction error: {e}")
        return None
