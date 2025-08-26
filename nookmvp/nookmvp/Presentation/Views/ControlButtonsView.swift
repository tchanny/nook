import SwiftUI

struct ControlButtonsView: View {
    @ObservedObject var presenter: MainPresenter
    
    var body: some View {
        HStack(spacing: 20) {
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

            Button(action: {
                if presenter.isEngineReady {
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


