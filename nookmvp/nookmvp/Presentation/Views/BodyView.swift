import SwiftUI

struct BodyView: View {
    let presenter: MainPresenter
    
    var body: some View {
        VStack(spacing: 24) {
            if !presenter.microphonePermissionGranted {
                MicrophonePermissionView(openSettingsAction: {
                    if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone") {
                        NSWorkspace.shared.open(url)
                    }
                })
            }
            ControlButtonsView(presenter: presenter)
            TranscriptionPanelView(
                transcription: presenter.transcription,
                isListening: presenter.isListening,
                currentSpeaker: presenter.currentSpeaker,
                speakerSegments: presenter.speakerSegments.map { ($0.speaker, $0.text) },
                fullTranscript: presenter.fullTranscript
            )
        }
        .padding(.horizontal, 24)
    }
}


