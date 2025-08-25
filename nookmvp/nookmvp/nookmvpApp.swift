//
//  nookmvpApp.swift
//  nookmvp
//
//  Created by Даниил Тчанников on 14.08.2025.
//

import SwiftUI

@main
struct nookmvpApp: App {
    var body: some Scene {
        WindowGroup {
            let presenter = MainPresenter(engine: PythonEngineService())
            ContentView(presenter: presenter)
        }
    }
}
