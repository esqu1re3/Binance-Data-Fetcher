print("Создание файла .env для API ключей Binance")
print("-----------------------------------------")
print("Этот скрипт создаст файл .env с вашими API ключами Binance")
print("Вы можете получить API ключи на странице API Management в вашем аккаунте Binance")
print("")

api_key = input("Введите ваш Binance API Key: ")
api_secret = input("Введите ваш Binance API Secret: ")

with open('.env', 'w') as f:
    f.write(f"BINANCE_API_KEY={api_key}\n")
    f.write(f"BINANCE_API_SECRET={api_secret}\n")

print("\nФайл .env успешно создан!")
print("Теперь вы можете запустить скрипт для получения данных:")
print("python binance_data_fetcher.py")