import Foundation
import Combine
import AppKit

final class PythonEngineService: EngineService {
    let isListening = CurrentValueSubject<Bool, Never>(false)
    let isReady = CurrentValueSubject<Bool, Never>(false)
    let statusText = CurrentValueSubject<String, Never>("Не инициализирован")
    let errorText = PassthroughSubject<String, Never>()

    let liveText = PassthroughSubject<String, Never>()
    let finalSegment = PassthroughSubject<(speaker: String, text: String), Never>()

    private let tempDir: String
    private var statusTimer: Timer?
    private var streamTimer: Timer?
    private var engineProcess: Process?
    private var engineLogFile: URL?
    private var lastProcessedLineCount: Int = 0
    private var lastSeenLineHash: Int = 0

    private var statusFile: String { "\(tempDir)/status.json" }
    private var commandFile: String { "\(tempDir)/command.json" }
    private var streamFile: String { "\(tempDir)/stream.jsonl" }

    init() {
        let homeDirectory = FileManager.default.homeDirectoryForCurrentUser
        self.tempDir = homeDirectory.appendingPathComponent("Documents/nook_engine").path
        createTempDirectory()
        startMonitoring()
        purgeOldFiles()
    }

    deinit {
        stopMonitoring()
    }

    func initialize() {
        if !FileManager.default.fileExists(atPath: statusFile) {
            launch()
        } else {
            checkEngineStatus()
        }
        if !isReady.value {
            sendCommand(["type": "get_status"])
        }
    }

    func launch() {
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

        let writeToLog: (FileHandle) -> Void = { handle in
            handle.readabilityHandler = { file in
                let data = file.availableData
                guard !data.isEmpty else { return }
                if let engineLogFile = self.engineLogFile, let logFH = try? FileHandle(forWritingTo: engineLogFile) {
                    logFH.seekToEndOfFile()
                    logFH.write(data)
                    try? logFH.close()
                } else if let engineLogFile = self.engineLogFile {
                    fm.createFile(atPath: engineLogFile.path, contents: nil)
                }
            }
        }
        writeToLog(outPipe.fileHandleForReading)
        writeToLog(errPipe.fileHandleForReading)

        do {
            try proc.run()
            engineProcess = proc
            statusText.send("Запуск движка...")
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { [weak self] in
                self?.checkEngineStatus()
            }
        } catch {
            errorText.send("Не удалось запустить движок: \(error.localizedDescription)")
        }
    }

    func startListening() {
        if !isReady.value { initialize() }
        let fm = FileManager.default
        [self.streamFile, "\(self.tempDir)/live_transcription.json.stream", "\(self.tempDir)/live_transcription.json"].forEach { path in
            if fm.fileExists(atPath: path) { try? fm.removeItem(atPath: path) }
        }
        lastProcessedLineCount = 0
        sendCommand([
            "type": "start_listening",
            "output_file": "live_transcription.json",
            "enable_diarization": true,
            "partial_updates": true,
            "update_interval": 0.25
        ])
        isListening.send(true)
    }

    func stopListening() {
        sendCommand(["type": "stop_listening"])
        isListening.send(false)
    }

    func cleanup() {
        sendCommand(["type": "cleanup"])
        isListening.send(false)
        isReady.send(false)
        statusText.send("Очистка завершена")
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
            isReady.send(false)
            statusText.send("Нет соединения с движком")
            return
        }
        do {
            let data = try Data(contentsOf: URL(fileURLWithPath: statusFile))
            let status = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            let listening = status?["is_listening"] as? Bool ?? false
            let ready = status?["is_initialized"] as? Bool ?? false
            isListening.send(listening)
            isReady.send(ready)
            statusText.send(ready ? "Готов к работе" : "Не готов")
        } catch {
            // ignore
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

            // Handle file truncation (engine may rewrite file)
            if lines.count < lastProcessedLineCount {
                lastProcessedLineCount = 0
            }

            // If this is a continuously rewritten single-line stream, process last line on change
            if pathToUse == altStream {
                guard let last = lines.last else { return }
                let currentHash = last.hashValue
                if currentHash == lastSeenLineHash { return }
                lastSeenLineHash = currentHash
                guard let update = try? JSONSerialization.jsonObject(with: Data(last.utf8)) as? [String: Any] else { return }
                let text = (update["text"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                let speaker = update["speaker"] as? String ?? "Unknown"
                let isFinal = update["is_final"] as? Bool ?? false
                guard !text.isEmpty else { return }
                if isFinal {
                    finalSegment.send((speaker: speaker, text: text))
                } else {
                    liveText.send(text)
                }
                return
            }

            // Default: process only newly appended lines
            if lines.count > lastProcessedLineCount {
                let newLines = Array(lines.suffix(from: lastProcessedLineCount))
                for line in newLines {
                    guard let update = try? JSONSerialization.jsonObject(with: Data(line.utf8)) as? [String: Any] else { continue }
                    let text = (update["text"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                    let speaker = update["speaker"] as? String ?? "Unknown"
                    let isFinal = update["is_final"] as? Bool ?? false
                    guard !text.isEmpty else { continue }
                    if isFinal {
                        finalSegment.send((speaker: speaker, text: text))
                    } else {
                        liveText.send(text)
                    }
                }
                lastProcessedLineCount = lines.count
            }
        } catch {
            // ignore
        }
    }

    private func sendCommand(_ command: [String: Any]) {
        do {
            let data = try JSONSerialization.data(withJSONObject: command)
            try data.write(to: URL(fileURLWithPath: commandFile))
        } catch {
            errorText.send("Ошибка отправки команды: \(error.localizedDescription)")
        }
    }

    private func createTempDirectory() {
        let fm = FileManager.default
        if !fm.fileExists(atPath: tempDir) {
            try? fm.createDirectory(atPath: tempDir, withIntermediateDirectories: true)
        }
    }

    private func purgeOldFiles() {
        let fm = FileManager.default
        [statusFile, streamFile].forEach { path in
            if fm.fileExists(atPath: path) { try? fm.removeItem(atPath: path) }
        }
    }
}


