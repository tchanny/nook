//
//  ContentView.swift
//  nookmvp
//
//  Created by Даниил Тчанников on 14.08.2025.
//

import SwiftUI

struct ContentView: View {
    @StateObject var presenter: MainPresenter
    
    var body: some View {
        ZStack {
            // Градиентный фон
            LinearGradient(
                colors: [
                    Color(NSColor.controlBackgroundColor),
                    Color(NSColor.controlBackgroundColor).opacity(0.8)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            VStack(spacing: 0) {
                HeaderView(isReady: presenter.isEngineReady)
                BodyView(presenter: presenter)
                Spacer()
            }
        }
        .frame(minWidth: 800, minHeight: 600)
        .onAppear {
            presenter.onAppear()
        }
    }
}

// MARK: - Microphone Permission View
struct MicrophonePermissionView: View {
    let openSettingsAction: () -> Void
    
    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.orange)
                .font(.title2)
                .scaleEffect(1.0)
                .animation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true), value: true)
            
            VStack(alignment: .leading, spacing: 4) {
                Text("Требуется доступ к микрофону")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Text("Приложению необходим доступ к микрофону для записи аудио")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Button("Настройки", action: openSettingsAction)
            .buttonStyle(.borderedProminent)
            .controlSize(.small)
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.orange.opacity(0.1))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.orange.opacity(0.3), lineWidth: 1)
                )
        )
    }
}

// MARK: - Control Buttons View
struct ControlButtonsView: View {
    let presenter: MainPresenter
    
    var body: some View {
        HStack(spacing: 20) {
            // Кнопка запуска движка
            Button(action: { presenter.onLaunchTap() }) {
                HStack(spacing: 8) {
                    Image(systemName: "play.circle.fill")
                        .font(.system(size: 16, weight: .medium))
                    Text("Запустить движок")
                        .font(.system(size: 14, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
                .background(
                    RoundedRectangle(cornerRadius: 0)
                        .fill(Color.purple)
                )
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(presenter.isEngineReady)

            // Кнопка инициализации/очистки
            Button(action: {
                if presenter.isEngineReady {
                    // Не вызываем cleanup автоматически, только при явном нажатии
                    print("ℹ️ Engine is ready, no action needed")
                } else {
                    presenter.onInitTap()
                }
            }) {
                HStack(spacing: 8) {
                    Image(systemName: presenter.isEngineReady ? "checkmark.circle.fill" : "gearshape.fill")
                        .font(.system(size: 16, weight: .medium))
                    
                    Text(presenter.isEngineReady ? "Готов" : "Инициализация")
                        .font(.system(size: 14, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
                .background(
                    RoundedRectangle(cornerRadius: 0)
                        .fill(presenter.isEngineReady ? Color.green : Color.blue)
                )
                .scaleEffect(presenter.isEngineReady ? 1.0 : 1.0)
                .animation(.easeInOut(duration: 0.2), value: presenter.isEngineReady)
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(presenter.isEngineReady)
            
            // Кнопка записи/остановки
            Button(action: { presenter.onRecordTap() }) {
                HStack(spacing: 8) {
                    Image(systemName: presenter.isListening ? "stop.fill" : "mic.fill")
                        .font(.system(size: 16, weight: .medium))
                    
                    Text(presenter.isListening ? "Стоп" : "Запись")
                        .font(.system(size: 14, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
                .background(
                    RoundedRectangle(cornerRadius: 0)
                        .fill(presenter.isListening ? Color.red : Color.green)
                )
                .scaleEffect(presenter.isListening ? 1.0 : 1.0)
                .animation(.easeInOut(duration: 0.2), value: presenter.isListening)
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(!presenter.microphonePermissionGranted)
            .opacity((!presenter.microphonePermissionGranted) ? 0.5 : 1.0)
            
            // Кнопка очистки (только когда движок готов)
            if presenter.isEngineReady {
                Button(action: { presenter.onCleanupTap() }) {
                    HStack(spacing: 8) {
                        Image(systemName: "trash.fill")
                            .font(.system(size: 16, weight: .medium))
                        
                        Text("Очистка")
                            .font(.system(size: 14, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
                    .background(
                        RoundedRectangle(cornerRadius: 0)
                            .fill(Color.orange)
                    )
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
    }
}

// MARK: - Transcription Panel View
struct TranscriptionPanelView: View {
    let transcription: String
    let isListening: Bool
    let currentSpeaker: String
    let speakerSegments: [(speaker: String, text: String)]
    let fullTranscript: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Заголовок панели
            HStack {
                HStack(spacing: 8) {
                    Image(systemName: "text.bubble.fill")
                        .foregroundColor(.blue)
                        .font(.title3)
                    
                    Text("Транскрипция")
                        .font(.headline)
                        .foregroundColor(.primary)
                }
                
                Spacer()
                
                // Индикатор записи
                if isListening {
                    HStack(spacing: 6) {
                        Circle()
                            .fill(Color.red)
                            .frame(width: 8, height: 8)
                            .scaleEffect(1.0)
                            .animation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true), value: isListening)
                        
                        Text("Запись")
                            .font(.caption)
                            .foregroundColor(.red)
                            .fontWeight(.medium)
                    }
                }
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            
            Divider()
                .padding(.horizontal, 20)
            
            // Содержимое транскрипции
            if transcription.isEmpty && speakerSegments.isEmpty && fullTranscript.isEmpty {
                EmptyTranscriptionView()
            } else {
                // Показываем одну живую строку (без финального блока)
                TranscriptionContentSingleLine(liveText: transcription, isListening: isListening)
            }
        }
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(NSColor.controlBackgroundColor))
                .shadow(color: .black.opacity(0.08), radius: 12, x: 0, y: 4)
        )
        .frame(maxHeight: .infinity)
    }
}

// MARK: - Empty Transcription View
struct EmptyTranscriptionView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "mic.slash")
                .font(.system(size: 48))
                .foregroundColor(.gray.opacity(0.4))
                .scaleEffect(1.0)
                .animation(.easeInOut(duration: 2.0).repeatForever(autoreverses: true), value: true)
            
            VStack(spacing: 8) {
                Text("Начните говорить")
                    .font(.title3)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                Text("Нажмите кнопку 'Запись' и говорите в микрофон")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(40)
    }
}

// MARK: - Transcription Content View
struct TranscriptionContentView: View {
    let speakerSegments: [(speaker: String, text: String)]
    let currentSpeaker: String
    let isListening: Bool
    let liveText: String
    
    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 16) {
                ForEach(Array(speakerSegments.enumerated()), id: \.offset) { index, segment in
                    TranscriptionSegmentView(
                        speaker: segment.speaker,
                        text: segment.text,
                        index: index
                    )
                }
                
                // Индикатор текущего спикера + живая строка
                if isListening && (!currentSpeaker.isEmpty || !liveText.isEmpty) {
                    VStack(spacing: 8) {
                        CurrentSpeakerIndicator(speaker: currentSpeaker.isEmpty ? "" : currentSpeaker)
                        if !liveText.isEmpty {
                            TranscriptionSegmentView(
                                speaker: currentSpeaker.isEmpty ? "" : currentSpeaker,
                                text: liveText,
                                index: speakerSegments.count
                            )
                        }
                    }
                }
            }
            .padding(20)
        }
    }
}

// MARK: - Transcription Segment View
struct TranscriptionSegmentView: View {
    let speaker: String
    let text: String
    let index: Int
    
    @State private var isVisible = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(speaker)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(
                        Capsule()
                            .fill(Color.blue.opacity(0.1))
                    )
                
                Spacer()
            }
            
            Text(text)
                .font(.body)
                .foregroundColor(.primary)
                .lineLimit(nil)
                .textSelection(.enabled)
                .padding(.leading, 4)
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.blue.opacity(0.03))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.blue.opacity(0.1), lineWidth: 1)
                )
        )
        .opacity(isVisible ? 1.0 : 0.0)
        .offset(x: isVisible ? 0 : -20)
        .onAppear {
            withAnimation(.easeOut(duration: 0.4).delay(Double(index) * 0.1)) {
                isVisible = true
            }
        }
    }
}

// MARK: - Current Speaker Indicator
struct CurrentSpeakerIndicator: View {
    let speaker: String
    
    @State private var isAnimating = false
    
    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(Color.green)
                .frame(width: 8, height: 8)
                .scaleEffect(isAnimating ? 1.2 : 0.8)
                .animation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true), value: isAnimating)
            
            Text("\(speaker) говорит...")
                .font(.caption)
                .foregroundColor(.green)
                .fontWeight(.medium)
            
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.green.opacity(0.1))
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.green.opacity(0.3), lineWidth: 1)
                )
        )
        .onAppear {
            isAnimating = true
        }
    }
}

// MARK: - Unified Transcript View
struct TranscriptionContentUnifiedView: View {
    let fullTranscript: String
    let isListening: Bool
    let liveText: String
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                if isListening && !liveText.isEmpty {
                    HStack(spacing: 12) {
                        Circle()
                            .fill(Color.green)
                            .frame(width: 8, height: 8)
                            .scaleEffect(1.0)
                        Text(liveText)
                            .font(.body)
                            .foregroundColor(.primary)
                    }
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color.green.opacity(0.08))
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.green.opacity(0.2), lineWidth: 1)
                            )
                    )
                }
                if !fullTranscript.isEmpty {
                    Text(fullTranscript)
                        .font(.body)
                        .foregroundColor(.primary)
                        .textSelection(.enabled)
                        .padding(12)
                        .background(
                            RoundedRectangle(cornerRadius: 8)
                                .fill(Color.blue.opacity(0.03))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color.blue.opacity(0.1), lineWidth: 1)
                                )
                        )
                }
                // Rolling transcript (final + partial)
                if isListening && !liveText.isEmpty {
                    Text(liveText)
                        .font(.body)
                        .foregroundColor(.primary)
                        .padding(.vertical, 4)
                }
            }
            .padding(20)
        }
    }
}

// MARK: - Single Line Transcript View
struct TranscriptionContentSingleLine: View {
    let liveText: String
    let isListening: Bool
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                if isListening {
                    HStack(spacing: 12) {
                        Circle()
                            .fill(Color.green)
                            .frame(width: 8, height: 8)
                        Text(liveText.isEmpty ? "Listening..." : liveText)
                            .font(.title3)
                            .foregroundColor(.primary)
                            .textSelection(.enabled)
                    }
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color.green.opacity(0.08))
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.green.opacity(0.2), lineWidth: 1)
                            )
                    )
                } else if !liveText.isEmpty {
                    Text(liveText)
                        .font(.title3)
                        .foregroundColor(.primary)
                        .textSelection(.enabled)
                }
            }
            .padding(20)
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView(presenter: MainPresenter(engine: PythonEngineService()))
    }
}
