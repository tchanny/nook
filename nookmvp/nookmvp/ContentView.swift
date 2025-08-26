//
//  ContentView.swift
//  nookmvp
//
//  Created by Даниил Тчанников on 14.08.2025.
//

import SwiftUI
import AppKit

struct ContentView: View {
    @ObservedObject var presenter: MainPresenter
    
    var body: some View {
        ZStack {
            // Градиентный фон
            LinearGradient(
                colors: [
                    Color(NSColor.controlBackgroundColor),
                    Color(NSColor.controlBackgroundColor).opacity(0.8)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            VStack(spacing: 0) {
                HeaderView(isReady: presenter.isEngineReady)
                BodyView(presenter: presenter)
                Spacer()
            }
        }
        .frame(minWidth: 800, minHeight: 600)
        .onAppear {
            presenter.onAppear()
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView(presenter: MainPresenter(engine: PythonEngineService()))
    }
}
