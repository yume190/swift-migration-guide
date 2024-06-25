# 啟用 Swift 6 語言模式
確保您的代碼免受資料競爭影響，啟用 Swift 6 語言模式。

使用 Swift 編譯器

啟用在命令行中直接運行 `swift` 或 `swiftc` 時的完全Concurrency檢查，可以傳入 `-swift-version 6` 適配符：

```
~ swift -swift-version 6 main.swift
```

使用 Swift Package Manager

(Note: Since this is a title, I did not include any markdown formatting)

### 命令列-invocation
```
-swift-version 6``可在 Swift package manager 命令列.invocation 中通過 `-Xswiftc` Flag 進行傳遞：
```
~ swift build -Xswiftc -swift-version 6
~ swift test -Xswiftc -swift-version 6
```

### 包含清單
一個使用 `6.0` 的 `swift-tools-version` 的 `Package.swift` 檔案，將為所有目標啟用 Swift 6 語言模式。
您仍然可以使用 `Package` 的 `swiftLanguageVersions` 屬性，以設定整個包的語言模式。

然而，您現在也可以根據需要在每個目標上變更語言模式，使用新的 `swiftLanguageVersion` 建立設定：
```
// swift-tools-version: 6.0

let package = Package(
    name: "MyPackage",
    products: [
        // ...
    ],
    targets: [
        // 使用默認工具語言模式
        .target(name: "FullyMigrated"),
        // 尚需要 5
        .target(name: "NotQuiteReadyYet",
                swiftSettings: [
                    .swiftLanguageVersion(.v5)
                ])
    ]
)
```

使用 Xcode

### 建置設定 
你可以藉由將「Swift 語言版本」建置設定設為「6」，來控制 Xcode 項目或目標的語言模式。

### XCConfig

您也可以在 xcconfig 檔案中設定 `SWIFT_VERSION` 設定為 `6`：

```markdown
// 在 Settings.xcconfig 中
SWIFT_VERSION = 6;
```