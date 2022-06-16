#region imports
from AlgorithmImports import *
#endregion
# ------------------------------------------------------------------------------
EQUITIES = ['AAPL','TSLA']; CRYPTOS = ['BTCUSD', 'ETHUSD']; CFDS = ['WTICOUSD'];
RSI_PERIOD = 14; SL = -0.1; TP = 0.3; ATR_PERIOD = 14; SL_ATR_MULTIPLES = 2; 
TP_ATR_MULTIPLES = 6
# ------------------------------------------------------------------------------

class SimpleRSIAddingOiltoFire(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2012, 1, 1) 
        self.SetEndDate(2022, 5, 1) 
        self.SetCash(100000)
        self.equities = [self.AddEquity(ticker, Resolution.Minute).Symbol for ticker in EQUITIES]
        self.cryptos = [self.AddCrypto(ticker, Resolution.Minute).Symbol for ticker in CRYPTOS]
        self.cfds = [self.AddCfd(ticker, Resolution.Minute).Symbol for ticker in CFDS]
        self.assets = self.equities + self.cryptos + self.cfds 
        self.rsi = {}
        self.atr = {}
        self.entry_price = {} 
        self.sl_distance = {}
        self.tp_distance = {}
        
        for sec in self.assets:
            self.rsi[sec] = self.RSI(sec, RSI_PERIOD, MovingAverageType.Simple, Resolution.Daily)
            self.atr[sec] = self.ATR(sec, ATR_PERIOD, MovingAverageType.Simple, Resolution.Daily)
            self.entry_price[sec] = None
        self.SetWarmUp(RSI_PERIOD + 1, Resolution.Daily)
        self.SetBenchmark("SPY")
        

    def OnData(self, data):
        if not (self.Time.hour == 10 and self.Time.minute == 1): return #algo only execute at this time, else algo executed twice a day 00:00 hrs and 19:00hrs
        if self.IsWarmingUp: return
        # self.Log(self.assets)

        for sec in self.assets:
            rsi = self.rsi[sec].Current.Value
            self.Plot("RSI", sec, rsi)
            if not self.Portfolio[sec].Invested:
                if rsi >= 50:
                    self.SetHoldings(sec, 0.2) 
                    self.Debug("{} initiate buy at {}".format(str(sec), str(self.Portfolio[sec].Price)))
                    self.entry_price[sec] = self.Portfolio[sec].Price
                    self.sl_distance[sec] = self.atr[sec].Current.Value * SL_ATR_MULTIPLES
                    self.tp_distance[sec] = self.atr[sec].Current.Value * TP_ATR_MULTIPLES
                    #self.Debug("{} ATR {}".format(str(sec), str(self.sl_distance[sec])))

            elif self.Portfolio[sec].Invested:
                pnl = self.Securities[sec].Holdings.UnrealizedProfitPercent
                #self.Debug("{} Unrealized profit percent ".format(str(pnl)))
                
                if rsi < 45: # exit if rsi < 50
                    self.Liquidate(sec, "rsi < 50")
                    self.Debug("{} liquidated at {}. Rsi < 50".format(str(sec), str(self.Portfolio[sec].Price)))
                #elif pnl < SL: #cut loss at 5%
                elif self.Portfolio[sec].Price <= self.entry_price[sec] - self.sl_distance[sec]: # cut loss at 2X ATR
                    self.Liquidate(sec, "Stop Loss")
                    self.Debug("{} cut loss at {}".format(str(sec), str(self.Portfolio[sec].Price)))
                #elif pnl > TP: # take profit at >10%
                elif self.Portfolio[sec].Price >= self.entry_price[sec] + self.tp_distance[sec]: # tp at 6x ATR
                    self.Liquidate(sec, "Take Profit")
                    self.Debug("{} take profit at {}".format(str(sec), str(self.Portfolio[sec].Price)))
