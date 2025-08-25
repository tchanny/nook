import Foundation
import Combine

public protocol EngineService {
    var isListening: CurrentValueSubject<Bool, Never> { get }
    var isReady: CurrentValueSubject<Bool, Never> { get }
    var statusText: CurrentValueSubject<String, Never> { get }
    var errorText: PassthroughSubject<String, Never> { get }

    var liveText: PassthroughSubject<String, Never> { get }
    var finalSegment: PassthroughSubject<(speaker: String, text: String), Never> { get }

    func initialize()
    func launch()
    func startListening()
    func stopListening()
    func cleanup()
}


