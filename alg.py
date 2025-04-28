def max_profit_dynamic_programming(prices, dates): 
    n = len(prices)
    if n < 2:
        return 0, None, None
    
    dp = [0] * n
    buy_date = None
    sell_date = None
    max_profit = 0

    for i in range(1, n):
        profit_if_sell_now = prices[i] - prices[0]
        for j in range(1, i):
            profit_if_sell_now = max(profit_if_sell_now, prices[i] - prices[j])
        dp[i] = max(dp[i-1], profit_if_sell_now)
        
        if dp[i] > max_profit:
            max_profit = dp[i]
            for k in range(i):
                if prices[i] - prices[k] == dp[i]:
                    buy_date = dates[k]
                    sell_date = dates[i]
                    break

    return max_profit, buy_date, sell_date

def max_profit_with_dates(prices, data):
    if not prices or len(prices) != len(data):
        return 0, None, None
    
    min_price = float('inf')
    max_profit = 0
    buy_date = None
    sell_date = None
    current_buy_date = None

    for i, price in enumerate(prices):
        if price < min_price:
            min_price = price
            current_buy_date = data[i]
        elif price - min_price > max_profit:
            max_profit = price - min_price
            buy_date = current_buy_date
            sell_date = data[i]

    return max_profit, buy_date, sell_date
