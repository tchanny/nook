#!/usr/bin/env python3
"""
Тест системы в реальном времени с непрерывной транскрипцией
"""

import sys
from pathlib import Path

# Добавить nook_engine в путь
sys.path.append(str(Path(__file__).parent / "nook_engine"))

from nook_engine import NookEngine

def test_realtime_continuous():
    """Тест в реальном времени"""
    
    print("🎙️ Nook Engine - Тест в реальном времени")
    print("=" * 50)
    
    # Создать движок с непрерывным режимом
    engine = NookEngine(
        model_size="base.en",      # Быстрая модель для реального времени
        continuous_mode=True,      # Непрерывный режим
        interruption_gap=0.8,      # Более чувствительное определение перебивания
        language="en"
    )
    
    # Инициализировать
    if not engine.initialize():
        print("❌ Ошибка инициализации")
        return
    
    print("✅ Движок готов к работе")
    print("🔄 Непрерывный режим: ВКЛ")
    print("⏱️  Промежуток перебивания: 0.8с")
    
    # Настройки записи
    output_file = "realtime_continuous.json"
    chunk_duration = 5  # 5 секунд на chunk
    
    print(f"\n🎤 Начинаем запись в реальном времени...")
    print(f"📁 Файл результата: {output_file}")
    print(f"⏱️  Длительность chunk: {chunk_duration}с")
    print("🛑 Нажмите Ctrl+C для остановки")
    
    try:
        # Запустить обработку в реальном времени
        success = engine.process_realtime(
            output_file=output_file,
            chunk_duration=chunk_duration,
            save_audio=True
        )
        
        if success:
            print("✅ Запись завершена успешно")
        else:
            print("❌ Ошибка при записи")
            
    except KeyboardInterrupt:
        print("\n🛑 Запись остановлена пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        engine.cleanup()
        print("🧹 Ресурсы очищены")

if __name__ == "__main__":
    test_realtime_continuous()
