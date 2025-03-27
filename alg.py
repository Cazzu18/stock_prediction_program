def max_profit_greedy_algorithm(prices):
    #finding the max profit with a single buy-sell transaction
    min_price = float('inf')
    max_profit = 0

    for price in prices:
        min_price = min(min_price, price)
        max_profit = max(max_profit, price - min_price)

    return max_profit

def max_profit_dynamic_proigramming(prices):
    print(prices)
    profit = 0

    for i in range(1, len(prices)):
        if(prices[i] > prices[i - 1]): #buy on a dip, sell on a rise
            profit += prices[i] - prices[i - 1]
    return profit

