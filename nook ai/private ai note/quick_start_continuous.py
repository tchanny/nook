#!/usr/bin/env python3
"""
Быстрый старт с непрерывной транскрипцией
"""

import sys
from pathlib import Path

# Добавить nook_engine в путь
sys.path.append(str(Path(__file__).parent / "nook_engine"))

from nook_engine import NookEngine

def quick_start():
    """Быстрый старт с непрерывной транскрипцией"""
    
    print("🎤 Nook Engine - Быстрый старт")
    print("=" * 40)
    
    # Создать движок с непрерывным режимом
    engine = NookEngine(
        model_size="base.en",      # Модель Whisper
        continuous_mode=True,      # Включить непрерывный режим
        interruption_gap=1.0,      # 1 секунда для определения перебивания
        language="en"              # Язык распознавания
    )
    
    # Инициализировать
    print("🔄 Инициализация...")
    if not engine.initialize():
        print("❌ Ошибка инициализации")
        return
    
    print("✅ Движок инициализирован")
    print(f"🔄 Непрерывный режим: {'ВКЛ' if engine.continuous_mode else 'ВЫКЛ'}")
    print(f"⏱️  Промежуток перебивания: {engine.interruption_gap}с")
    
    # Укажите путь к вашему аудиофайлу
    audio_file = "ваш_файл.wav"  # ЗАМЕНИТЕ НА ВАШ ФАЙЛ
    
    if not Path(audio_file).exists():
        print(f"⚠️  Аудиофайл не найден: {audio_file}")
        print("📁 Доступные файлы в директории:")
        for file in Path(".").glob("*.wav"):
            print(f"   - {file.name}")
        print("\nИспользуем тестовый файл...")
        audio_file = "mic_test.wav"
    
    # Выполнить диаризацию
    print(f"\n🎵 Обработка: {audio_file}")
    result = engine.diarize_audio(audio_file)
    
    if result:
        print("\n✅ Обработка завершена!")
        
        # Показать результаты
        segments = result.get('segments', [])
        speakers = result.get('speakers', [])
        
        print(f"👥 Обнаружено спикеров: {len(speakers)}")
        print(f"📝 Сегментов: {len(segments)}")
        print(f"⏱️  Общая длительность: {result.get('total_duration', 0):.1f}с")
        
        # Показать транскрипцию
        print("\n📋 Транскрипция:")
        print("-" * 40)
        for i, segment in enumerate(segments):
            speaker = segment['speaker']
            text = segment['text']
            start = segment['start']
            end = segment['end']
            print(f"\n{i+1}. {speaker} ({start:.1f}s - {end:.1f}s):")
            print(f"   {text}")
        
        # Сохранить результат
        output_file = "continuous_result.json"
        engine.save_result(result, output_file, "json")
        print(f"\n💾 Результат сохранен: {output_file}")
        
    else:
        print("❌ Ошибка обработки")
    
    # Очистить ресурсы
    engine.cleanup()
    print("\n🧹 Ресурсы очищены")

if __name__ == "__main__":
    quick_start()
