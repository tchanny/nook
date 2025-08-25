import Foundation

public struct TranscriptSegment: Identifiable, Equatable {
    public let id = UUID()
    public let speaker: String
    public let text: String
}

public enum EngineReadiness: String {
    case uninitialized
    case ready
    case notReady
}


