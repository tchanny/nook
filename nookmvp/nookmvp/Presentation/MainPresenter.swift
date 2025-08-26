import Foundation
import Combine

final class MainPresenter: ObservableObject {
    // Inputs (from View)
    private let engine: EngineService

    // Outputs (to View)
    @Published var isListening: Bool = false
    @Published var isEngineReady: Bool = false
    @Published var engineStatus: String = "Не инициализирован"
    @Published var microphonePermissionGranted: Bool = true
    @Published var transcription: String = ""
    @Published var speakerSegments: [TranscriptSegment] = []
    @Published var currentSpeaker: String = ""
    @Published var fullTranscript: String = ""

    private var cancellables: Set<AnyCancellable> = []
    private var cumulativeText: String = ""
    private var lastPartialText: String = ""

    init(engine: EngineService) {
        self.engine = engine
        bind()
    }

    func onAppear() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.engine.initialize()
        }
    }

    func onLaunchTap() { engine.launch() }
    func onInitTap() { engine.initialize() }
    func onRecordTap() { isListening ? engine.stopListening() : engine.startListening() }
    func onCleanupTap() { engine.cleanup(); resetTranscript() }

    private func bind() {
        engine.isListening
            .receive(on: DispatchQueue.main)
            .assign(to: &self.$isListening)

        engine.isReady
            .receive(on: DispatchQueue.main)
            .assign(to: &self.$isEngineReady)

        engine.statusText
            .receive(on: DispatchQueue.main)
            .assign(to: &self.$engineStatus)

        // Ignore partials in UI (we only show finals)
        engine.liveText
            .receive(on: DispatchQueue.main)
            .sink { text in
                print("🟡 Partial from engine: \(text)")
            }
            .store(in: &cancellables)

        engine.finalSegment
            .receive(on: DispatchQueue.main)
            .sink { [weak self] seg in
                print("🟢 Final from engine: \(seg.speaker): \(seg.text)")
                self?.handleFinal(speaker: seg.speaker, text: seg.text)
            }
            .store(in: &cancellables)

        engine.errorText
            .receive(on: DispatchQueue.main)
            .sink { err in
                print("🔴 Engine error: \(err)")
            }
            .store(in: &cancellables)
    }

    private func resetTranscript() {
        transcription = ""
        speakerSegments = []
        currentSpeaker = ""
        fullTranscript = ""
        cumulativeText = ""
        lastPartialText = ""
    }

    private func handlePartial(_ partial: String) {
        // No-op: partials are not shown in UI
    }

    private func handleFinal(speaker: String, text: String) {
        let normalized = normalizeText(text)
        guard !normalized.isEmpty else { return }
        let toAppend = dropOverlap(prefix: normalized, againstSuffixOf: cumulativeText, maxTokens: 8)
        let sep = cumulativeText.isEmpty ? "" : " "
        cumulativeText += sep + toAppend
        lastPartialText = ""
        transcription = cumulativeText
        speakerSegments.append(TranscriptSegment(speaker: speaker, text: normalized))
        currentSpeaker = speaker
        fullTranscript = cumulativeText
    }

    private func normalizeText(_ text: String) -> String {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return "" }
        let tokens = trimmed.split(whereSeparator: { $0.isWhitespace })
        if tokens.isEmpty { return trimmed }
        var deduped: [Substring] = []
        var i = 0
        while i < tokens.count {
            let t = tokens[i]
            if !deduped.isEmpty && deduped.last!.caseInsensitiveCompare(t) == .orderedSame {
                i += 1
                continue
            }
            if i+1 < tokens.count && deduped.count >= 2 {
                let a1 = deduped[deduped.count-2]
                let b1 = deduped[deduped.count-1]
                let a2 = tokens[i]
                let b2 = tokens[i+1]
                if a1.caseInsensitiveCompare(a2) == .orderedSame && b1.caseInsensitiveCompare(b2) == .orderedSame {
                    i += 2
                    continue
                }
            }
            deduped.append(t)
            i += 1
        }
        return deduped.joined(separator: " ")
    }

    private func dropOverlap(prefix: String, againstSuffixOf base: String, maxTokens: Int) -> String {
        guard !base.isEmpty else { return prefix }
        let baseTokens = base.split(whereSeparator: { $0.isWhitespace })
        let prefTokens = prefix.split(whereSeparator: { $0.isWhitespace })
        let k = min(maxTokens, baseTokens.count, prefTokens.count)
        if k == 0 { return prefix }
        for n in stride(from: k, through: 1, by: -1) {
            let baseSuffix = baseTokens.suffix(n).joined(separator: " ")
            let prePrefix = prefTokens.prefix(n).joined(separator: " ")
            if baseSuffix.caseInsensitiveCompare(prePrefix) == .orderedSame {
                let rest = prefTokens.dropFirst(n).joined(separator: " ")
                return rest
            }
        }
        return prefix
    }
}


