# Binance Data Fetcher

Скрипт для получения данных с Binance API, включая:

1. Aggregated Open Interest (OI) по STABLECOIN-маржинальным фьючерсам
2. Aggregated Liquidations
3. Spot Cumulative Volume Delta (CVD)
4. Futures Cumulative Volume Delta (CVD)

## Требования

- Python 3.7+
- Необходимые библиотеки:
  - python-binance
  - pandas
  - matplotlib
  - python-dotenv

Установите необходимые зависимости:

```bash
pip install python-binance pandas matplotlib python-dotenv
```

## Настройка API ключей

1. Создайте API ключи на Binance:
   - Войдите в свою учетную запись Binance
   - В правом верхнем углу нажмите на иконку профиля и выберите "API Management"
   - Нажмите "Create API"
   - Введите метку для ключа и пройдите проверку безопасности
   - Скопируйте API Key и Secret Key
   - Для этого приложения достаточно включить только разрешения на чтение

2. Запустите скрипт для создания файла .env:
   ```bash
   python create_env.py
   ```
   
   Скрипт запросит ваши API ключи и сохранит их в файле .env.

## Запуск скрипта

После настройки API ключей запустите основной скрипт:

```bash
python binance_data_fetcher.py
```

Результаты работы скрипта:
1. Загрузка данных Open Interest для STABLECOIN-маржинальных фьючерсов
2. Получение данных о ликвидациях
3. Расчет Spot CVD
4. Расчет Futures CVD
5. Сравнение Spot и Futures CVD

Все результаты будут выведены в консоль, а графики сохранены в текущую директорию в формате PNG.

## Выходные файлы

- `open_interest.png`: График Open Interest
- `liquidations_bar.png`: График ежедневных ликвидаций
- `liquidations_pie.png`: Круговая диаграмма распределения ликвидаций
- `spot_cvd.png`: График Spot CVD
- `spot_interval_cvd.png`: График интервального Spot Volume Delta
- `futures_cvd.png`: График Futures CVD
- `futures_interval_cvd.png`: График интервального Futures Volume Delta
- `cvd_comparison.png`: Сравнение Spot и Futures CVD
- `cvd_difference.png`: Разница между Futures и Spot CVD

## Настройка параметров

Для изменения параметров (символ, интервал, период) откройте файл `binance_data_fetcher.py` и измените соответствующие значения в функции `main()`:

```python
# Определяем символы для анализа
symbol = 'BTCUSDT'  # Измените на любой другой символ

# Для изменения интервала или периода отредактируйте вызовы функций:
# spot_cvd = fetcher.get_spot_cvd(symbol=symbol, interval='1h', limit=24)
# futures_cvd = fetcher.get_futures_cvd(symbol=symbol, interval='1h', limit=24)
```

## API Class Methods

### `BinanceDataFetcher`

- `get_stablecoin_margined_futures_open_interest(symbol=None, limit=30)`: Gets OI data for stablecoin-margined futures
- `get_aggregated_liquidations(symbol=None, start_time=None, end_time=None, limit=1000)`: Gets liquidation data
- `get_spot_cvd(symbol='BTCUSDT', interval='1h', limit=24)`: Calculates Spot CVD
- `get_futures_cvd(symbol='BTCUSDT', interval='1h', limit=24)`: Calculates Futures CVD 