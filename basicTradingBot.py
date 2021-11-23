import numpy as np

class SimpleBreakoutExample(QCAlgorithm):

    def Initialize(self):
        # Set the test start and end date along side cash
        self.SetStartDate(2020,10,1)
        self.SetEndDate(2021,11,23)
        self.SetCash(100000)
        
        # Set crypto/stock to be targeted
        self.symbol = self.AddEquity("TSLA", Resolution.Daily).Symbol
        
        # Set the lower/upper bound for loss
        self.initialStopLoss = 0.96
        self.dependentStopLoss = 0.9
        self.lookback = 20
        self.highestLookBack = 30
        self.lowestLookBack = 10
        
        # Enable trading bot to run 30 mins after market open
        self.Schedule.On(self.DateRules.EveryDay(self.symbol), \
                            self.TimeRules.AfterMarketOpen(self.symbol, 30), \
                            Action(self.EveryMarketOpen))
        


 
    def EveryMarketOpen(self):
        # Determine volatility based off 30 day chart
        closePrice = self.History(self.symbol, 31, Resolution.Daily)["close"]
        todayVolatility = np.std(closePrice[1:31])
        yesVolatility = np.std(closePrice[0:30])
        deltavol = (todayVolatility - yesVolatility) / todayVolatility
        self.lookback = round(self.lookback * (1 + deltavol))
        
        # Insure the lookback is not greater than both its max and low then set Daily highs list
        if self.lookback > self.highestLookBack:
            self.lookback = self.highestLookBack
        elif self.lookback < self.lowestLookBack:
            self.lookback = self.lowestLookBack
        self.high = self.History(self.symbol, self.lookback, Resolution.Daily)["high"]
        
        # Buy if breakout
        if not self.Securities[self.symbol].Invested and \
                self.Securities[self.symbol].Close >= max(self.high[:-1]):
            self.SetHoldings(self.symbol, 1)
            self.breakoutlvl = max(self.high[:-1])
            self.highestPrice = self.breakoutlvl
        
        
        # Adjust dependent loss in case of breakout
        if self.Securities[self.symbol].Invested:
            
            # Send initial stop loss in case of no orders
            if not self.Transactions.GetOpenOrders(self.symbol):
                self.stopMarketTicket = self.StopMarketOrder(self.symbol, \
                                        -self.Portfolio[self.symbol].Quantity, \
                                        self.initialStopLoss * self.breakoutlvl)
            
            if self.Securities[self.symbol].Close > self.highestPrice and \
                    self.initialStopLoss * self.breakoutlvl < self.Securities[self.symbol].Close * self.dependentStopLoss:
                self.highestPrice = self.Securities[self.symbol].Close
                updateFields = UpdateOrderFields()
                updateFields.StopPrice = self.Securities[self.symbol].Close * self.dependentStopLoss
                self.stopMarketTicket.Update(updateFields)
                self.Debug(updateFields.StopPrice)
            
            # Plot data
            self.Plot("Data Chart", "Stop Price", self.stopMarketTicket.Get(OrderField.StopPrice))