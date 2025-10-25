import requests
import os
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class LightshotDownloader:
    def __init__(self):
        self.folder = "screenshots"
        self.downloaded = 0
        self.lock = threading.Lock()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def generate_random_code(self):
        """Генерирует случайный код для Lightshot"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))

    def download_screenshot(self, code):
        """Скачивает скриншот по коду"""
        urls = [
            f"https://image.prntscr.com/image/{code}.png",
            f"https://i.imgur.com/{code}.png",  # иногда редирект на imgur
        ]
        
        for url in urls:
            try:
                response = self.session.get(url, timeout=5, stream=True)
                if response.status_code == 200:
                    content_length = int(response.headers.get('content-length', 0))
                    
                    # Проверяем что это реальная картинка, а не заглушка
                    if content_length > 5000:  # минимальный размер нормального скриншота
                        filename = os.path.join(self.folder, f"{code}.png")
                        
                        with open(filename, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        with self.lock:
                            self.downloaded += 1
                            print(f"[+] #{self.downloaded} Успешно: {code}.png ({content_length} bytes)")
                        return True
                    
            except Exception as e:
                continue
        
        return False

    def worker(self, codes_queue):
        """Рабочий поток"""
        for code in codes_queue:
            if self.downloaded >= self.target_count:
                break
            self.download_screenshot(code)

    def main(self):
        print("=== FAST Lightshot Screenshot Downloader ===")
        print("[+] Используем 50 потоков\n")
        
        # Создаем папку для скриншотов
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        # Спрашиваем сколько скриншотов нужно
        try:
            self.target_count = int(input("Сколько скриншотов скачать? "))
        except:
            print("введи нормальное число!")
            return

        print(f"\n[+] Цель: {self.target_count} скриншотов")
        print("[+] Запускаем 50 потоков...")
        
        start_time = time.time()
        
        # Создаем пул потоков
        with ThreadPoolExecutor(max_workers=50) as executor:
            # Генерируем коды в реальном времени
            futures = []
            codes_generated = 0
            
            while self.downloaded < self.target_count and codes_generated < self.target_count * 3:
                code = self.generate_random_code()
                future = executor.submit(self.download_screenshot, code)
                futures.append(future)
                codes_generated += 1
                
                # Небольшая пауза чтобы не перегружать
                if codes_generated % 50 == 0:
                    time.sleep(0.1)
            
            # Ждем завершения
            for future in as_completed(futures):
                if self.downloaded >= self.target_count:
                    executor.shutdown(wait=False)
                    break

        end_time = time.time()
        
        print(f"\n[+] Готово за {end_time - start_time:.2f} секунд!")
        print(f"[+] Скачано: {self.downloaded}/{self.target_count} скриншотов")
        print(f"[+] Папка: {os.path.abspath(self.folder)}")

if __name__ == "__main__":
    downloader = LightshotDownloader()
    downloader.main()
