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
    private var seenFinalHashes: [String] = [] // FIFO of recent finals (normalized)
    private let seenFinalMax = 200

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

        // Show partials in real-time for speed
        engine.liveText
            .receive(on: DispatchQueue.main)
            .sink { [weak self] text in
                print("🟡 Partial from engine: \(text)")
                self?.handlePartial(text)
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
        let normalized = normalizeText(partial)
        guard !normalized.isEmpty else { return }
        
        // Filter out low-quality partials (too short, repetitive, or nonsensical)
        guard isValidPartial(normalized) else { return }
        
        if !lastPartialText.isEmpty {
            if cumulativeText.hasSuffix(" " + lastPartialText) {
                cumulativeText.removeLast(lastPartialText.count + 1)
            } else if cumulativeText.hasSuffix(lastPartialText) {
                cumulativeText.removeLast(lastPartialText.count)
            }
        }
        let toAppend = dropOverlap(prefix: normalized, againstSuffixOf: cumulativeText, maxTokens: 8)
        let sep = cumulativeText.isEmpty || toAppend.isEmpty ? "" : " "
        cumulativeText += sep + toAppend
        lastPartialText = normalized
        transcription = cumulativeText
    }
    
    private func handleFinal(speaker: String, text: String) {
        let normalized = normalizeText(text)
        guard !normalized.isEmpty else { return }
        
        // Strong quality filtering for finals
        guard isValidFinal(normalized) else { return }
        
        let key = normalized.lowercased()
        if seenFinalHashes.contains(key) {
            // Skip duplicate finals seen previously
            return
        }
        // Stronger deduplication: if recent tail already contains this final, skip
        let recentTail = String(cumulativeText.suffix(220))
        if recentTail.localizedCaseInsensitiveContains(normalized) ||
            cumulativeText.hasSuffix(normalized) {
            // Do not duplicate identical final segments
        } else {
            let toAppend = dropOverlap(prefix: normalized, againstSuffixOf: cumulativeText, maxTokens: 12)
            let sep = cumulativeText.isEmpty ? "" : " "
            cumulativeText += sep + toAppend
            // Collapse accidental duplicate punctuation/spaces
            cumulativeText = cumulativeText.replacingOccurrences(of: "  +", with: " ", options: .regularExpression)
        }
        // Track seen finals (bounded)
        seenFinalHashes.append(key)
        if seenFinalHashes.count > seenFinalMax { seenFinalHashes.removeFirst(seenFinalHashes.count - seenFinalMax) }
        lastPartialText = ""
        transcription = cumulativeText
        speakerSegments.append(TranscriptSegment(speaker: speaker, text: normalized))
        currentSpeaker = speaker
        fullTranscript = cumulativeText
    }
    
    // MARK: - Quality Filtering
    
    private func isValidPartial(_ text: String) -> Bool {
        let words = text.split(whereSeparator: { $0.isWhitespace })
        
        // Reject very short partials (likely noise)
        guard words.count >= 2 else { return false }
        
        // Reject repetitive patterns
        if hasRepetitivePattern(words) { return false }
        
        // Reject nonsensical word combinations
        if hasNonsensicalCombination(words) { return false }
        
        return true
    }
    
    private func isValidFinal(_ text: String) -> Bool {
        let words = text.split(whereSeparator: { $0.isWhitespace })
        
        // Reject very short finals
        guard words.count >= 3 else { return false }
        
        // Reject repetitive patterns
        if hasRepetitivePattern(words) { return false }
        
        // Reject nonsensical word combinations
        if hasNonsensicalCombination(words) { return false }
        
        // Reject incomplete sentences (missing proper ending)
        if !hasProperEnding(text) { return false }
        
        return true
    }
    
    private func hasRepetitivePattern(_ words: [Substring]) -> Bool {
        // Check for A B A B patterns
        if words.count >= 4 {
            for i in 0..<(words.count - 3) {
                if words[i] == words[i+2] && words[i+1] == words[i+3] {
                    return true
                }
            }
        }
        
        // Check for consecutive identical words
        for i in 1..<words.count {
            if words[i] == words[i-1] {
                return true
            }
        }
        
        return false
    }
    
    private func hasNonsensicalCombination(_ words: [Substring]) -> Bool {
        // Common nonsensical patterns to reject
        let nonsensicalPatterns = [
            "this meme", "tell a ball", "holdings", "callings",
            "hear me", "do you hear me"
        ]
        
        let text = words.joined(separator: " ").lowercased()
        for pattern in nonsensicalPatterns {
            if text.contains(pattern) {
                return true
            }
        }
        
        return false
    }
    
    private func hasProperEnding(_ text: String) -> Bool {
        // Check if text ends with proper punctuation or common sentence endings
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        let properEndings = [".", "!", "?", "...", "etc", "etc."]
        
        for ending in properEndings {
            if trimmed.hasSuffix(ending) {
                return true
            }
        }
        
        // Check for common sentence endings
        let commonEndings = ["thank you", "thanks", "goodbye", "bye", "see you", "that's all"]
        let lowerText = trimmed.lowercased()
        for ending in commonEndings {
            if lowerText.hasSuffix(ending) {
                return true
            }
        }
        
        return false
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


