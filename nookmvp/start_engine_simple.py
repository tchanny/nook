#!/usr/bin/env python3
"""
Простой запуск движка Nook AI для macOS приложения
"""

import sys
import os
import signal
import time
import json

# Добавить путь к nook_engine
engine_path = os.path.join(os.path.dirname(__file__), '..', 'nook ai', 'private ai note')
sys.path.insert(0, engine_path)

def signal_handler(signum, frame):
    """Обработчик сигнала для корректного завершения"""
    print("\n🛑 Получен сигнал завершения, очистка...")
    if 'engine' in globals():
        engine.cleanup()
    print("✅ Движок остановлен")
    sys.exit(0)

def create_communication_files(temp_dir):
    """Создать необходимые файлы для связи"""
    files = [
        os.path.join(temp_dir, "stream.jsonl")
    ]
    
    for file_path in files:
        if not os.path.exists(file_path):
            if file_path.endswith('.jsonl'):
                with open(file_path, 'w') as f:
                    pass  # Создать пустой файл
                print(f"✅ Создан файл: {os.path.basename(file_path)}")
    
    # НЕ создаем command.json и result.json - они создаются движком при необходимости
    print("ℹ️  Файлы command.json и result.json будут созданы движком автоматически")

def main():
    """Основная функция"""
    print("🚀 Запуск движка Nook AI для macOS приложения")
    print("=" * 50)
    
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        from nook_engine import create_macos_engine
        
        # Создать движок
        print("🔧 Создание движка...")
        temp_dir = os.path.expanduser("~/Documents/nook_engine")
        
        # Создать файлы связи
        print("📁 Создание файлов связи...")
        create_communication_files(temp_dir)
        
        engine = create_macos_engine(
            model_size="small.en",    # excellent quality, reasonable size (~244MB)
            continuous_mode=True,
            interruption_gap=0.45,     # optimized for small.en
            temp_dir=temp_dir
        )
        
        # Инициализировать
        print("🚀 Инициализация движка...")
        if not engine.initialize():
            print("❌ Ошибка инициализации движка")
            return
        
        print("✅ Движок успешно инициализирован!")
        print("🔄 Continuous mode: ON (interruption gap: 0.45s)")
        print("🖥️ macOS приложение может теперь подключаться")
        
        # Показать файлы
        print("\n📋 Доступные файлы:")
        print(f"   Статус: {engine.status_file}")
        print(f"   Команды: {engine.command_file}")
        print(f"   Поток: {engine.stream_file}")
        
        print("\n🔄 Движок работает и ожидает команды...")
        print("💡 Нажмите Ctrl+C для остановки")
        
        # Основной цикл ожидания
        while True:
            time.sleep(1)
            
            # Проверяем статус
            try:
                status = engine.get_status()
                if 'error' in status:
                    print(f"⚠️  Ошибка движка: {status['error']}")
            except Exception as e:
                print(f"⚠️  Ошибка получения статуса: {e}")
    
    except KeyboardInterrupt:
        print("\n🛑 Прерывание пользователем")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Очистка
        if 'engine' in locals():
            print("🧹 Очистка ресурсов...")
            try:
                engine.cleanup()
                print("✅ Очистка завершена")
            except Exception as e:
                print(f"⚠️  Ошибка при очистке: {e}")

if __name__ == "__main__":
    main()
