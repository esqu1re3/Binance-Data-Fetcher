import time
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

if not api_key or not api_secret:
    print("⚠️ Файл .env не найден или API ключи не заданы.")
    print("Создайте файл .env с параметрами BINANCE_API_KEY и BINANCE_API_SECRET")
    exit(1)
else:
    print("✅ API ключи загружены успешно.")

class BinanceDataFetcher:
    def __init__(self, api_key, api_secret):
        if not api_key or not api_secret:
            raise ValueError("API key и secret обязательны для работы класса.")
            
        self.client = Client(api_key=api_key, api_secret=api_secret)
        
    def get_stablecoin_margined_futures_open_interest(self, symbol=None, limit=30):
        """
        Получение агрегированного Open Interest для STABLECOIN-маржинальных фьючерсов
        
        Args:
            symbol (str, optional): Символ для получения данных (напр., 'BTCUSDT'). 
                                   Если None, получает данные для всех символов.
            limit (int): Количество записей (по умолчанию: 30)
            
        Returns:
            pd.DataFrame: DataFrame с данными Open Interest
        """
        result = []
        
        if symbol is None:
            exchange_info = self.client.futures_exchange_info()
            symbols = [s['symbol'] for s in exchange_info['symbols'] 
                    if s['symbol'].endswith(('USDT', 'USDC', 'BUSD', 'DAI'))]
        else:
            symbols = [symbol]
            
        for sym in symbols:
            try:
                oi_data = self.client.futures_open_interest_hist(
                    symbol=sym, 
                    period='1d', 
                    limit=limit
                )
                
                if oi_data:
                    for item in oi_data:
                        item['symbol'] = sym
                        item['timestamp'] = datetime.fromtimestamp(item['timestamp'] / 1000)
                        item['sumOpenInterest'] = float(item['sumOpenInterest'])
                        item['sumOpenInterestValue'] = float(item['sumOpenInterestValue'])
                    
                    result.extend(oi_data)
            except Exception as e:
                print(f"Ошибка получения данных OI для {sym}: {e}")
                
        if result:
            df = pd.DataFrame(result)
            return df
        else:
            return pd.DataFrame()
        
    def get_aggregated_liquidations(self, symbol=None, start_time=None, end_time=None, limit=1000):
        """
        Получение данных о ликвидациях
        
        Args:
            symbol (str, optional): Символ для получения данных. 
                                   Если None, получает данные для нескольких основных пар.
            start_time (int, optional): Начальное время в миллисекундах
            end_time (int, optional): Конечное время в миллисекундах
            limit (int): Количество записей (по умолчанию: 1000)
            
        Returns:
            pd.DataFrame: DataFrame с данными ликвидаций
        """
        if start_time is None:
            start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
            
        if end_time is None:
            end_time = int(datetime.now().timestamp() * 1000)
            
        if symbol is None:
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT']
        else:
            symbols = [symbol]
            
        all_liquidations = []
        
        for sym in symbols:
            try:
                liquidations = self.client.futures_liquidation_orders(
                    symbol=sym,
                    startTime=start_time,
                    endTime=end_time,
                    limit=limit
                )
                
                for liq in liquidations:
                    liq['time'] = datetime.fromtimestamp(liq['time'] / 1000)
                    liq['price'] = float(liq['price'])
                    liq['origQty'] = float(liq['origQty'])
                    liq['executedQty'] = float(liq['executedQty'])
                    liq['averagePrice'] = float(liq['averagePrice'])
                    liq['value'] = liq['price'] * liq['origQty'] 
                
                all_liquidations.extend(liquidations)
            except Exception as e:
                print(f"Ошибка получения данных о ликвидациях для {sym}: {e}")
                
        if all_liquidations:
            df = pd.DataFrame(all_liquidations)
            return df
        else:
            return pd.DataFrame()
    
    def calculate_cvd(self, trades):
        """Вспомогательная функция для расчета Cumulative Volume Delta из сделок"""
        buy_volume = 0
        sell_volume = 0
        
        for trade in trades:
            qty = float(trade.get('q', trade.get('qty', 0)))
            is_buyer = trade.get('m', trade.get('isBuyerMaker', False))
            
            if is_buyer:
                sell_volume += qty
            else:
                buy_volume += qty
                
        return buy_volume - sell_volume
        
    def get_spot_cvd(self, symbol='BTCUSDT', interval='1h', limit=24):
        """
        Расчет Spot Cumulative Volume Delta
        
        Args:
            symbol (str): Символ для получения данных
            interval (str): Интервал для свечей (напр., '1h', '4h', '1d')
            limit (int): Количество интервалов
            
        Returns:
            pd.DataFrame: DataFrame с данными CVD
        """
        result = []
        
        try:
            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            
            timestamps = []
            cvd_values = []
            cumulative_cvd = 0
            
            for i, kline in enumerate(klines):
                start_time = datetime.fromtimestamp(kline[0] / 1000)
                end_time = datetime.fromtimestamp(kline[6] / 1000)
                
                trades = self.client.get_aggregate_trades(
                    symbol=symbol,
                    startTime=int(kline[0]),
                    endTime=int(kline[6]),
                    limit=1000
                )
                
                interval_cvd = self.calculate_cvd(trades)
                cumulative_cvd += interval_cvd
                
                result.append({
                    'timestamp': start_time,
                    'open_time': start_time,
                    'close_time': end_time,
                    'symbol': symbol,
                    'interval': interval,
                    'interval_cvd': interval_cvd,
                    'cumulative_cvd': cumulative_cvd
                })
                
        except Exception as e:
            print(f"Ошибка расчета spot CVD для {symbol}: {e}")
            
        if result:
            return pd.DataFrame(result)
        else:
            return pd.DataFrame()
        
    def get_futures_cvd(self, symbol='BTCUSDT', interval='1h', limit=24):
        """
        Расчет Futures Cumulative Volume Delta
        
        Args:
            symbol (str): Символ для получения данных
            interval (str): Интервал для свечей (напр., '1h', '4h', '1d')
            limit (int): Количество интервалов
            
        Returns:
            pd.DataFrame: DataFrame с данными CVD
        """
        result = []
        
        try:
            klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)
            
            timestamps = []
            cvd_values = []
            cumulative_cvd = 0
            
            for i, kline in enumerate(klines):
                start_time = datetime.fromtimestamp(kline[0] / 1000)
                end_time = datetime.fromtimestamp(kline[6] / 1000)
                
                trades = self.client.futures_aggregate_trades(
                    symbol=symbol,
                    startTime=int(kline[0]),
                    endTime=int(kline[6]),
                    limit=1000
                )
                
                interval_cvd = self.calculate_cvd(trades)
                cumulative_cvd += interval_cvd
                
                result.append({
                    'timestamp': start_time,
                    'open_time': start_time,
                    'close_time': end_time,
                    'symbol': symbol,
                    'interval': interval,
                    'interval_cvd': interval_cvd,
                    'cumulative_cvd': cumulative_cvd
                })
                
        except Exception as e:
            print(f"Ошибка расчета futures CVD для {symbol}: {e}")
            
        if result:
            return pd.DataFrame(result)
        else:
            return pd.DataFrame()

def visualize_open_interest(oi_data):
    """Визуализация данных Open Interest"""
    if oi_data.empty:
        print("Нет данных для визуализации Open Interest.")
        return
        
    print(f"Получено данных OI для {oi_data['symbol'].unique().size} символов")
    print(oi_data.head())
    
    plt.figure(figsize=(14, 7))
    symbol_data = oi_data[oi_data['symbol'] == oi_data['symbol'].iloc[0]]
    plt.plot(symbol_data['timestamp'], symbol_data['sumOpenInterestValue'] / 1e9, linewidth=2)
    plt.title(f"Open Interest для {symbol_data['symbol'].iloc[0]}", fontsize=16)
    plt.xlabel('Дата', fontsize=14)
    plt.ylabel('Open Interest Value (млрд USD)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('open_interest.png')
    plt.close()
    print(f"Сохранен график Open Interest: open_interest.png")

def visualize_liquidations(liq_data):
    """Визуализация данных о ликвидациях"""
    if liq_data.empty:
        print("Нет данных для визуализации ликвидаций.")
        return
        
    print(f"Получено {len(liq_data)} записей о ликвидациях")
    print(liq_data.head())
    
    liq_data['date'] = liq_data['time'].dt.date
    daily_liq = liq_data.groupby(['date', 'side']).agg({'value': 'sum'}).reset_index()
    
    plt.figure(figsize=(14, 8))
    
    buy_liq = daily_liq[daily_liq['side'] == 'BUY']
    sell_liq = daily_liq[daily_liq['side'] == 'SELL']
    
    if not buy_liq.empty:
        plt.bar(buy_liq['date'], buy_liq['value'] / 1e6, color='green', alpha=0.7, 
                label='Long Liquidations (BUY)')
        
    if not sell_liq.empty:
        plt.bar(sell_liq['date'], sell_liq['value'] / 1e6, color='red', alpha=0.7, 
                label='Short Liquidations (SELL)')
    
    plt.title("Ежедневные ликвидации", fontsize=16)
    plt.xlabel('Дата', fontsize=14)
    plt.ylabel('Стоимость ликвидаций (млн USD)', fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('liquidations_bar.png')
    plt.close()
    print(f"Сохранен график ликвидаций: liquidations_bar.png")
    
    side_totals = liq_data.groupby('side')['value'].sum()
    colors = ['red', 'green']
    
    plt.figure(figsize=(10, 8))
    plt.pie(side_totals, labels=side_totals.index, autopct='%1.1f%%', colors=colors, 
            shadow=True, startangle=140, textprops={'fontsize': 14})
    plt.title('Распределение ликвидаций по типу', fontsize=16)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('liquidations_pie.png')
    plt.close()
    print(f"Сохранена круговая диаграмма: liquidations_pie.png")

def visualize_cvd(cvd_data, type_name='Spot'):
    """Визуализация данных Cumulative Volume Delta"""
    if cvd_data.empty:
        print(f"Нет данных для визуализации {type_name} CVD.")
        return
        
    print(f"Рассчитан {type_name} CVD для {len(cvd_data)} интервалов")
    print(cvd_data.head())
    
    plt.figure(figsize=(14, 7))
    color = '#1f77b4' if type_name == 'Spot' else 'orange'
    plt.plot(cvd_data['timestamp'], cvd_data['cumulative_cvd'], marker='o', linewidth=2, 
             markersize=8, color=color)
    plt.title(f"{type_name} Cumulative Volume Delta для {cvd_data['symbol'].iloc[0]}", fontsize=16)
    plt.xlabel('Время', fontsize=14)
    plt.ylabel('Cumulative Volume Delta', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{type_name.lower()}_cvd.png')
    plt.close()
    print(f"Сохранен график {type_name} CVD: {type_name.lower()}_cvd.png")
    
    plt.figure(figsize=(14, 7))
    plt.bar(cvd_data['timestamp'], cvd_data['interval_cvd'], 
            color=['green' if x > 0 else 'red' for x in cvd_data['interval_cvd']], alpha=0.7)
    plt.title(f"{type_name} Interval Volume Delta для {cvd_data['symbol'].iloc[0]}", fontsize=16)
    plt.xlabel('Время', fontsize=14)
    plt.ylabel('Interval Volume Delta', fontsize=14)
    plt.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{type_name.lower()}_interval_cvd.png')
    plt.close()
    print(f"Сохранен график {type_name} интервального CVD: {type_name.lower()}_interval_cvd.png")

def compare_spot_futures_cvd(spot_cvd, futures_cvd):
    """Сравнение Spot и Futures CVD"""
    if spot_cvd.empty or futures_cvd.empty:
        print("Недостаточно данных для сравнения Spot и Futures CVD.")
        return
        
    spot_data = spot_cvd.set_index('timestamp')
    futures_data = futures_cvd.set_index('timestamp')
    
    common_times = spot_data.index.intersection(futures_data.index)
    
    if len(common_times) > 0:
        spot_values = spot_data.loc[common_times, 'cumulative_cvd']
        futures_values = futures_data.loc[common_times, 'cumulative_cvd']
        
        plt.figure(figsize=(14, 8))
        plt.plot(common_times, spot_values, marker='o', linewidth=2, 
                label='Spot CVD', color='#1f77b4')
        plt.plot(common_times, futures_values, marker='s', linewidth=2, 
                label='Futures CVD', color='orange')
        plt.title(f"Сравнение Spot и Futures CVD для {spot_cvd['symbol'].iloc[0]}", fontsize=16)
        plt.xlabel('Время', fontsize=14)
        plt.ylabel('Cumulative Volume Delta', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=14)
        plt.tight_layout()
        plt.savefig('cvd_comparison.png')
        plt.close()
        print(f"Сохранено сравнение CVD: cvd_comparison.png")
        
        plt.figure(figsize=(14, 6))
        diff = futures_values - spot_values
        colors = ['green' if x > 0 else 'red' for x in diff]
        plt.bar(common_times, diff, color=colors, alpha=0.7)
        plt.title(f"Разница между Futures и Spot CVD для {spot_cvd['symbol'].iloc[0]}", fontsize=16)
        plt.xlabel('Время', fontsize=14)
        plt.ylabel('Futures CVD - Spot CVD', fontsize=14)
        plt.grid(True, axis='y', alpha=0.3)
        plt.axhline(y=0, color='black', linestyle='-', linewidth=1)
        plt.tight_layout()
        plt.savefig('cvd_difference.png')
        plt.close()
        print(f"Сохранен график разницы CVD: cvd_difference.png")

def main():
    """Основная функция для получения и визуализации данных"""
    try:
        fetcher = BinanceDataFetcher(api_key=api_key, api_secret=api_secret)
        print("✅ BinanceDataFetcher успешно инициализирован")
        
        symbol = 'BTCUSDT' 
        
        print("\n1. Получение Open Interest...")
        oi_data = fetcher.get_stablecoin_margined_futures_open_interest(symbol=symbol, limit=30)
        visualize_open_interest(oi_data)
        
        print("\n2. Получение данных о ликвидациях...")
        liq_data = fetcher.get_aggregated_liquidations(symbol=symbol)
        visualize_liquidations(liq_data)
        
        print("\n3. Получение Spot CVD...")
        spot_cvd = fetcher.get_spot_cvd(symbol=symbol, interval='1h', limit=24)
        visualize_cvd(spot_cvd, 'Spot')
        
        print("\n4. Получение Futures CVD...")
        futures_cvd = fetcher.get_futures_cvd(symbol=symbol, interval='1h', limit=24)
        visualize_cvd(futures_cvd, 'Futures')
        
        print("\n5. Сравнение Spot и Futures CVD...")
        compare_spot_futures_cvd(spot_cvd, futures_cvd)
        
        print("\nОбработка данных завершена!")
        print(f"Все графики сохранены в текущей директории.")
        
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")

if __name__ == "__main__":
    main() 