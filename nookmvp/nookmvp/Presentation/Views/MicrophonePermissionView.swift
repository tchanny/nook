import SwiftUI
import AppKit

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


