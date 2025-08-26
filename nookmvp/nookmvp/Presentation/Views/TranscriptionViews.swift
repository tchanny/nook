import SwiftUI

struct TranscriptionPanelView: View {
    let transcription: String
    let isListening: Bool
    let currentSpeaker: String
    let speakerSegments: [(speaker: String, text: String)]
    let fullTranscript: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
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
            if transcription.isEmpty && speakerSegments.isEmpty && fullTranscript.isEmpty {
                EmptyTranscriptionView()
            } else {
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

struct TranscriptionContentSingleLine: View {
    let liveText: String
    let isListening: Bool
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                // Show partial text in real-time while listening
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


