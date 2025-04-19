import numpy as np #we use NumPy for numerical operations, especially when we work with arrays
import pandas as pd #used for data manipulation and analysis, especially DataFrame
from sklearn.preprocessing import MinMaxScaler #used for sclaing data to a range between 0 and 1. Important for neural networks to improve training stability and performance
from tensorflow.keras.models import Sequential #used to create a linear stack of layer for the neural network
from tensorflow.keras.layers import LSTM, Dense, Dropout #LSTM is a type of recurrent neural network layer suitable for handling sequential data. Dense is a fully connected layer used for outputting final prediction
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping #to prevent the model from training for too many epochs and overfitting(model has learned the training data too well and is not generalizing to new data)
'''
This function defines and trains the LSTM(long short-term memory model) neural network model

@param: x_train: the training data input(features)
        y_train: the training data output(target variable - the actual prices)
        look_back: the number of previous time steps to use as input features(defaults to 1). This determines
                    how much historical data the model considers when making a prediction
'''
def create_lstm_model(x_train, y_train, look_back = 1):
    model = Sequential() #creates a sequential model, which is a linear stack of layers

    ''' activation = "relu" uses the ReLu(rectified linear unit) activation function)
        input_shape = (look_back, x_train.shape[2]) specifies the input shape for the LSTM layer\
                        x_train.shape[2] is the number of features per time step(which is 1 in this case, as we are only using closing price)
    '''
  
    model.add(LSTM(50, activation='relu', input_shape=(look_back, x_train.shape[2]), return_sequences=True))#Adds an LSTM later with 100 units(memory cells)
    model.add(Dropout(0.3))
    model.add(LSTM(50, activation='relu'))
    model.add(Dropout(0.3))

    model.add(Dense(1))#adds a dense (fully connected) layer(organized structures that process information sequentially. Each layer transforms data from the previous layer, ultimately leading to a final output or prediction. ) with 1 unit, which outputs the final predicted prices
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse') #configures the learning process. optimzier = 'adam' uses the adam optimization algorithm. loss='mse' uses the mean squared error loss function, whihc is common for regression problems
    #model.fit(x_train, y_train, epochs=200, verbose=0)#trains the model using the training data. epoch =200 the number of times the entire training dataset is passed through the model. verbose = 0 suppresses the training progress output

    return model #we return the trained model


'''
This function prepares the data for the LSTM model by creating sequences of data points and their corresponding target values.

@param: data: the input data(scaled stock prices)
        look_back: again, the number of previous time steps to use as input features
'''
def prepare_lstm_data(data, look_back = 1):
    if len(data) <= look_back:
        raise ValueError(f"Data length ({len(data)}) must be greater than look_back ({look_back})")
    
    x, y= [], [] #lists to store sequences(x) and target values(y)
    
    for i in range(len(data) - look_back): #creates sequences of length(look_back)
        a = data[i:(i+look_back), 0:] #creates a sequence of look_bac data points starting from the index
        x.append(a) #appends sequence to list
        y.append(data[i+look_back, 0])#appends the data point immediately following the sequence to y list(target value)

    return np.array(x), np.array(y) #converts x and y to numpy arrays and returns them


'''
This function orchestrates the data preparation, scaling, and model training processes. We can think of it like the __main__

@param: prices: the input data(stock prices)
'''
def train_lstm_model(prices):
    #scaling data

    scaler = MinMaxScaler(feature_range=(0, 1)) #creates a MinMaxScaler object to scale the data between 0 and 1
    try:
        scaled_data = scaler.fit_transform(prices.values.reshape(-1, 1)) #scales the stock prices using the MinMaxScaler object. The .reshape(-1,-1) is used to reshape the data into a column vector, which is  REQUIRED by the fit_transform method
    except Exception as e:
        print(f"Error in MinMaxScaler: {e}")
        return None, None, None  # Return None values to indicate an error

    #preparing data for LSTM
    look_back = 10 #we can adjust as needeed. time step(days in this case)
    x, y = prepare_lstm_data(scaled_data, look_back) #returs two numpy arrays
    x = np.reshape(x, (x.shape[0], x.shape[1], 1)) #we reshpae the input data x to have the shape(number of samples, look_back, number of features). In this case, the number of features is 1(closing price). Necessary for LSTM layer.

    #splitting into training and testing sets
    train_size = int(len(x) * 0.8) #calculating the size of the training set(80% of the data)
    x_train, x_test = x[0:train_size], x[train_size:len(x)]#splits the input data into training and testing sets
    y_train, y_test = y[0:train_size], y[train_size:len(y)]#splits the target data into training and testing sets

    #creating and training the LSTM model
    model = create_lstm_model(x_train, y_train, look_back) #creates and trains the LSTM model using training data

     #implement EarlyStopping
    early_stopping = EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)  #we stop if loss doesn't improve for 10 epochs
    model.fit(x_train, y_train, epochs=200, verbose=0, callbacks=[early_stopping])  # Add callbacks to the fit method

    return model, scaler, look_back #return scalar for inverse transforming predictions(involves reversing a transformation applied to data before making a prediction, so the model output can be interpreted in the ORIGINAL SCALE)

'''
This function uses the trained LSTM model to predict the stock price for a given input sequence.

@param: model: the trained LSTM model
        scaler: the MinMaxScaler objext used to scale the training data
        last_sequence: the last look_back data points(stock prices) to use as input for the prediction
        look_back: the number of previous time steps to use as input features
'''
def predict_lstm_price(model, scaler, last_sequence, look_back):
    #scaling lastsequence
    scaled_last_sequence = scaler.transform(last_sequence.reshape(-1, 1)) #we scale the input sequence using the same MinMaxScaler object used for training

    #reshaping the input for LSTM
    x = np.reshape(scaled_last_sequence, (1, look_back, 1)) #reshape the scaled input to have the shape(1, lookback, 1) which is the expected input shape for the LSTM model

    #predicting the scaled price
    scaled_prediction_price = model.predict(x)#uses the trained model to predict the scaled stock price

    #inverse transform to get the actual price
    predicted_price = scaler.inverse_transform(scaled_prediction_price)[0][0] #inverse transfomrs the scaled prediction back to the original scale to get the ACTUAL predicted price

    return predicted_price #returns the predicted price





    
