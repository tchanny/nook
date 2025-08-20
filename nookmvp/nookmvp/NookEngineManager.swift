import Foundation
import AVFoundation
import Combine
import AppKit

class NookEngineManager: ObservableObject {
    @Published var isListening = false
    @Published var transcription = ""
    @Published var fullTranscript = ""
    @Published var displayTranscript = ""
    @Published var currentSpeaker: String = ""
    @Published var speakerSegments: [(speaker: String, text: String)] = []
    @Published var engineStatus = "Не инициализирован"
    @Published var isEngineReady = false
    @Published var errorMessage = ""
    @Published var microphonePermissionGranted = false
    
    private let tempDir: String
    private var statusTimer: Timer?
    private var streamTimer: Timer?
    private var speakerIdToDisplayName: [String: String] = [:]
    private var nextSpeakerOrdinal: Int = 3
    private var engineProcess: Process?
    private var engineLogFile: URL?
    private var lastProcessedLineCount: Int = 0
    private var cumulativeText: String = ""
    private var lastPartialText: String = ""
    
    // Communication files
    private var statusFile: String { "\(tempDir)/status.json" }
    private var commandFile: String { "\(tempDir)/command.json" }
    private var streamFile: String { "\(tempDir)/stream.jsonl" }
    
    init() {
        // Use user's Documents directory for sandbox compatibility
        let homeDirectory = FileManager.default.homeDirectoryForCurrentUser
        self.tempDir = homeDirectory.appendingPathComponent("Documents/nook_engine").path
        
        print("🔧 NookEngineManager: tempDir = \(tempDir)")
        
        createTempDirectory()
        checkMicrophonePermission()
        startMonitoring()
        purgeOldFiles()
    }
    
    deinit {
        stopMonitoring()
        cleanup()
    }
    
    // MARK: - Setup
    
    private func checkMicrophonePermission() {
        // For macOS, we'll check permission when trying to record
        microphonePermissionGranted = true
    }
    
    private func createTempDirectory() {
        let fileManager = FileManager.default
        if !fileManager.fileExists(atPath: tempDir) {
            do {
                try fileManager.createDirectory(atPath: tempDir, withIntermediateDirectories: true, attributes: nil)
                print("✅ Created temp directory at: \(tempDir)")
            } catch {
                print("❌ Error creating temp directory: \(error)")
                errorMessage = "Ошибка создания временной папки: \(error.localizedDescription)"
            }
        } else {
            print("✅ Temp directory already exists at: \(tempDir)")
        }
    }
    
    // MARK: - Engine Control
    
    func initializeEngine() {
        print("🚀 Initializing engine...")
        
        // Проверить, готов ли движок
        let statusExists = FileManager.default.fileExists(atPath: statusFile)
        if !statusExists {
            // Автозапуск движка, если статуса нет
            print("🔄 Status file not found. Launching engine...")
            launchEngine()
        } else {
            checkEngineStatus()
        }
        
        // Если движок не готов, попробовать отправить команду get_status
        if !isEngineReady {
            print("🔄 Engine not ready, requesting status...")
            let command = ["type": "get_status"]
            sendCommand(command)
            
            // Проверить статус через секунду
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                self.checkEngineStatus()
            }
        }
        
        print("🚀 Engine initialization requested")
    }
    
    func startListening() {
        if !isEngineReady {
            // Попробовать автозапуск и повтор
            initializeEngine()
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                self.startListening()
            }
            return
        }
        print("🎤 Starting listening...")
        // Reset session state and clear previous streams
        DispatchQueue.main.async {
            self.transcription = ""
            self.fullTranscript = ""
            self.displayTranscript = ""
            self.speakerSegments = []
            self.currentSpeaker = ""
            self.lastProcessedLineCount = 0
            self.cumulativeText = ""
            self.lastPartialText = ""
        }
        let fm = FileManager.default
        [self.streamFile, "\(self.tempDir)/live_transcription.json.stream", "\(self.tempDir)/live_transcription.json"].forEach { path in
            if fm.fileExists(atPath: path) { try? fm.removeItem(atPath: path) }
        }
        let command: [String: Any] = [
            "type": "start_listening",
            "output_file": "live_transcription.json",
            "enable_diarization": true,
            "partial_updates": true,
            "update_interval": 0.25
        ]
        sendCommand(command)
        DispatchQueue.main.async {
            self.isListening = true
        }
        print("🎤 Listening started, waiting for transcription...")
    }
    
    func stopListening() {
        print("🛑 Stopping listening...")
        
        let command = ["type": "stop_listening"]
        sendCommand(command)
        
        // Обновить UI сразу
        DispatchQueue.main.async {
            self.isListening = false
        }
        
        print("🛑 Listening stopped")
    }
    
    func cleanup() {
        print("🧹 Cleaning up...")
        
        let command = ["type": "cleanup"]
        sendCommand(command)
        
        DispatchQueue.main.async {
            self.isListening = false
            self.isEngineReady = false
            self.engineStatus = "Очистка завершена"
            self.transcription = ""
            self.fullTranscript = ""
            self.speakerSegments = []
            self.currentSpeaker = ""
            self.speakerIdToDisplayName = [:]
            self.nextSpeakerOrdinal = 3
        }
        
        print("🧹 Cleanup completed")
    }
    
    // MARK: - Monitoring
    
    private func startMonitoring() {
        statusTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            self.checkEngineStatus()
        }
        
        streamTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { _ in
            self.checkStream()
        }
    }
    
    private func stopMonitoring() {
        statusTimer?.invalidate()
        streamTimer?.invalidate()
    }
    
    private func checkEngineStatus() {
        guard FileManager.default.fileExists(atPath: statusFile) else {
            DispatchQueue.main.async {
                self.isEngineReady = false
                self.engineStatus = "Нет соединения с движком"
            }
            return
        }
        
        do {
            let data = try Data(contentsOf: URL(fileURLWithPath: statusFile))
            let status = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            
            DispatchQueue.main.async {
                self.isListening = status?["is_listening"] as? Bool ?? false
                self.isEngineReady = status?["is_initialized"] as? Bool ?? false
                
                if self.isEngineReady {
                    self.engineStatus = "Готов к работе"
                } else {
                    self.engineStatus = "Не готов"
                }
            }
        } catch {
            print("Error reading status: \(error)")
        }
    }

    // MARK: - Launch Engine (Python)
    func launchEngine() {
        // Prevent duplicate launches
        if engineProcess != nil { return }
        
        let fm = FileManager.default
        let home = fm.homeDirectoryForCurrentUser
        let venvPython = home.appendingPathComponent("Desktop/nook project/.venv/bin/python").path
        let scriptPath = home.appendingPathComponent("Desktop/nook project/nookmvp/start_engine_simple.py").path
        
        let pythonExec: String
        var arguments: [String]
        if fm.fileExists(atPath: venvPython) {
            pythonExec = venvPython
            arguments = [scriptPath]
        } else {
            pythonExec = "/usr/bin/env"
            arguments = ["python3", scriptPath]
        }
        
        let logsDir = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("nookmvp_logs")
        try? fm.createDirectory(at: logsDir, withIntermediateDirectories: true)
        engineLogFile = logsDir.appendingPathComponent("engine.log")
        
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: pythonExec)
        proc.arguments = arguments
        
        let outPipe = Pipe()
        let errPipe = Pipe()
        proc.standardOutput = outPipe
        proc.standardError = errPipe
        
        // Stream logs to file
        let logHandle = try? FileHandle(forWritingTo: engineLogFile!)
        if logHandle == nil {
            fm.createFile(atPath: engineLogFile!.path, contents: nil)
        }
        let writeToLog: (FileHandle) -> Void = { handle in
            handle.readabilityHandler = { file in
                let data = file.availableData
                guard !data.isEmpty else { return }
                if let logFH = try? FileHandle(forWritingTo: self.engineLogFile!) {
                    logFH.seekToEndOfFile()
                    logFH.write(data)
                    try? logFH.close()
                }
            }
        }
        writeToLog(outPipe.fileHandleForReading)
        writeToLog(errPipe.fileHandleForReading)
        
        do {
            try proc.run()
            engineProcess = proc
            DispatchQueue.main.async {
                self.engineStatus = "Запуск движка..."
            }
            // Poll status shortly after launch
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                self.checkEngineStatus()
            }
        } catch {
            DispatchQueue.main.async {
                self.errorMessage = "Не удалось запустить движок: \(error.localizedDescription)"
            }
        }
    }
    
    private func checkStream() {
        let fm = FileManager.default
        let primaryStream = streamFile
        let altStream = "\(tempDir)/live_transcription.json.stream"
        let pathToUse: String
        if fm.fileExists(atPath: primaryStream) {
            pathToUse = primaryStream
        } else if fm.fileExists(atPath: altStream) {
            pathToUse = altStream
        } else {
            return
        }
        
        do {
            let data = try Data(contentsOf: URL(fileURLWithPath: pathToUse))
            guard let content = String(data: data, encoding: .utf8) else { return }
            
            let lines = content.components(separatedBy: .newlines).filter { !$0.isEmpty }
            
            // Обработать только новые строки на основе lastProcessedLineCount
            if lines.count > lastProcessedLineCount {
                let newLines = Array(lines.suffix(from: lastProcessedLineCount))
                for line in newLines {
                    guard let update = try? JSONSerialization.jsonObject(with: Data(line.utf8)) as? [String: Any] else { continue }
                    
                    let text = (update["text"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                    let rawSpeaker = update["speaker"] as? String ?? "Unknown"
                    let speaker = self.mapDisplayName(for: rawSpeaker)
                    let isFinal = update["is_final"] as? Bool ?? false
                    
                    guard !text.isEmpty else { continue }
                    
                    if isFinal {
                        print("📝 Final: \(speaker): \(text)")
                        DispatchQueue.main.async {
                            self.speakerSegments.append((speaker: speaker, text: text))
                            self.currentSpeaker = speaker
                            self.appendToCumulative(text)
                            self.lastPartialText = ""
                            self.transcription = self.cumulativeText
                            self.displayTranscript = self.cumulativeText
                        }
                    } else {
                        // Обновляем только живой текст без добавления сегмента
                        DispatchQueue.main.async {
                            self.currentSpeaker = speaker
                            self.mergePartial(text)
                            self.transcription = self.cumulativeText
                            self.displayTranscript = self.cumulativeText
                        }
                    }
                }
                lastProcessedLineCount = lines.count
            }
        } catch {
            print("Error reading stream: \(error)")
        }
    }

    // MARK: - Speaker Mapping
    private func mapDisplayName(for rawSpeaker: String) -> String {
        if let existing = speakerIdToDisplayName[rawSpeaker] {
            return existing
        }
        let assigned: String
        switch speakerIdToDisplayName.count {
        case 0:
            assigned = "Вы"
        case 1:
            assigned = "Собеседник"
        default:
            assigned = "Спикер \(nextSpeakerOrdinal)"
            nextSpeakerOrdinal += 1
        }
        speakerIdToDisplayName[rawSpeaker] = assigned
        return assigned
    }

    // MARK: - Transcript Aggregation
    private func appendToCumulative(_ finalText: String) {
        let normalized = normalizeText(finalText)
        guard !normalized.isEmpty else { return }
        let toAppend = dropOverlap(prefix: normalized, againstSuffixOf: cumulativeText, maxTokens: 8)
        guard !toAppend.isEmpty else { return }
        let sep = cumulativeText.isEmpty ? "" : " "
        cumulativeText += sep + toAppend
    }

    private func mergePartial(_ partial: String) {
        let p = normalizeText(partial)
        guard !p.isEmpty else { return }
        // Remove previous partial from display and add new one
        if !lastPartialText.isEmpty {
            if cumulativeText.hasSuffix(" " + lastPartialText) {
                cumulativeText.removeLast(lastPartialText.count + 1)
            } else if cumulativeText.hasSuffix(lastPartialText) {
                cumulativeText.removeLast(lastPartialText.count)
            }
        }
        let toAppend = dropOverlap(prefix: p, againstSuffixOf: cumulativeText, maxTokens: 8)
        let sep = cumulativeText.isEmpty || toAppend.isEmpty ? "" : " "
        cumulativeText += sep + toAppend
        lastPartialText = p
    }

    // Remove consecutive duplicates (words/bigrams) and trim spaces
    private func normalizeText(_ text: String) -> String {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return "" }
        let tokens = trimmed.split(whereSeparator: { $0.isWhitespace })
        if tokens.isEmpty { return trimmed }
        var deduped: [Substring] = []
        var i = 0
        while i < tokens.count {
            let t = tokens[i]
            // Dedup single-word repeats
            if !deduped.isEmpty && deduped.last!.caseInsensitiveCompare(t) == .orderedSame {
                i += 1
                continue
            }
            // Dedup bigram repeats (A B A B)
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

    // Drop overlapping prefix tokens that repeat the suffix of the existing text
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
    
    // MARK: - Communication
    
    private func sendCommand(_ command: [String: Any]) {
        do {
            let data = try JSONSerialization.data(withJSONObject: command)
            try data.write(to: URL(fileURLWithPath: commandFile))
            print("✅ Command sent: \(command["type"] ?? "unknown")")
        } catch {
            print("❌ Error sending command: \(error)")
            DispatchQueue.main.async {
                self.errorMessage = "Ошибка отправки команды: \(error.localizedDescription)"
            }
        }
    }
    
    // MARK: - Housekeeping
    
    private func purgeOldFiles() {
        // Remove old stream/result/status on app start for clean state
        let fm = FileManager.default
        [statusFile, streamFile].forEach { path in
            if fm.fileExists(atPath: path) {
                try? fm.removeItem(atPath: path)
            }
        }
    }
    
    // MARK: - Error Handling
    
    func clearError() {
        errorMessage = ""
    }
    
    // MARK: - macOS Specific
    
    func openSystemPreferences() {
        let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone")!
        NSWorkspace.shared.open(url)
    }
}
