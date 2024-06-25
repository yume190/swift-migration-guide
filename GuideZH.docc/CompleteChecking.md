# 启用完整并發檢查
Incrementally 將資料競爭安全性問題轉換為警告，以便在您的專案中進行處理。
Swift 6 語言模式中的資料競爭安全性是為了逐步遷移而設計的。您可以根據模組逐步處理資料競爭安全性問題，並在 Swift 5 語言模式中啟用 compiler 的 actor isolation 和 `Sendable` 檢查，讓您能夠評估進度以便完全消除資料竞争。
使用 `-strict-concurrency` 编译器 flag 在 Swift 5 語言模式中啟用完整的資料競爭安全性檢查。

## 使用 Swift 編譯器
要在命令行直接運行 `swift` 或 `swiftc` 時，啟用完整並發檢查，可以傳遞 `-strict-concurrency=complete` 參數：
```
~ swift -strict-concurrency=complete main.swift
```

使用 Swift Package Manager

(Note: I assume you want me to translate the title as it is, since it's a technical term. If you have any specific request or instruction, please let me know.)

### 使用 SwiftPM 命令行 Invocation 時的(strict-concurrency=complete)選項
```
~ swift build -Xswiftc -strict-concurrency=complete
~ swift test -Xswiftc -strict-concurrency=complete
```
這可以用於在將該旗標永久添加到 package 標識檔案前，先測試 concurrency警告的amount。

### 在 SwiftPM 套件清單中

為了在使用 Swift 5.9 或 Swift 5.10 工具的 Swift套件中啟用完全的同步檢查，於目標中的 Swift 設定中使用 `[SwiftSetting.enableExperimentalFeature](https://developer.apple.com/documentation/packagedescription/swiftsetting/enableexperimentalfeature(_:_:))`：

```swift
.target(
  name: "MyTarget",
  swiftSettings: [
    .enableExperimentalFeature("StrictConcurrency")
  ]
)
```

當使用 Swift 6.0 工具或更晚版本時，於預設為 Swift 6 語言模式的目標中使用 `[SwiftSetting.enableUpcomingFeature](https://developer.apple.com/documentation/packagedescription/swiftsetting(enableupcomingfeature(_:_:))`：

```swift
.target(
  name: "MyTarget",
  swiftSettings: [
    .enableUpcomingFeature("StrictConcurrency")
  ]
)
```

使用 Swift 6 語言模式的目標將自動啟用完整檢查，不需要進行任何設定變更。

## 使用 Xcode

要在 Xcode 專案中啟用完整的Concurrency檢查，請在 Xcode 建置設定中將「Strict Concurrency Checking」設定為「Complete」。或者，您也可以在 xcconfig 檔案中設定 `SWIFT_STRICT_CONCURRENCY` 為 `complete`：

```
// 在 Settings.xcconfig 中
SWIFT_STRICT_CONCURRENCY = complete;
```