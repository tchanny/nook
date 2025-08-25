import SwiftUI

struct HeaderView: View {
    let isReady: Bool
    
    var body: some View {
        HStack {
            Text("Nook AI")
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundColor(.primary)
            Spacer()
            HStack(spacing: 8) {
                Circle()
                    .fill(isReady ? Color.green : Color.red)
                    .frame(width: 8, height: 8)
                    .scaleEffect(isReady ? 1.0 : 0.8)
                    .animation(.easeInOut(duration: 0.5).repeatForever(autoreverses: true), value: isReady)
                Text(isReady ? "Готов" : "Не готов")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.horizontal, 24)
        .padding(.top, 20)
        .padding(.bottom, 16)
    }
}


