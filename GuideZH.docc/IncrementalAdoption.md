# 繼續採用

學習如何將 SwiftConcurrency特性引入您的項目
逐步。

將專案轉移到 Swift 6 語言模式通常是階段性的。
事實上，許多項目已經開始進行這個過程甚至於 Swift 6 還沒有出現。
您可以繼續引入Concurrency功能_
逐步增加
處理在路上遇到的問題。
這樣可以讓您作進步的成就不會中斷整個專案。

Swift包括了許多語言特性和標準庫 API，以幫助 Ease 的 Incremental 採用。

## Wrap around Callback-Based Functions

APIs that accept and invoke a single function upon completion 是 Swift 中的絕對常見模式。

可以將這種函數轉換為可直接從異步上下文中使用。


```swift
func updateStyle(backgroundColor: ColorComponents, completionHandler: @escaping () -> Void) {
    // ...
}
```

這是一個使用回呼來告知客戶工作完成的範例。

沒有方法讓調用者能夠 Deterministic 的了解 callback 何時和在什麼執行緒上被invoke 而不 Consult 文件。

可以將函數Wrapped 成一個異步版本使用 `_continuations`。





```swift
func updateStyle(backgroundColor: ColorComponents) async {
    withCheckedContinuation { continuation in
        updateStyle(backgroundColor: backgroundColor) {
            // ... do some work here ...
            
            continuation.resume()
        }
    }
}
```

> 注意：你需要小心地_resume_ 繼續 exactly 一次。如果你 Miss invoke 它，調用任務將保持 Suspended 直到結束。另一方面，如果 resuming Checked 繼續多於一次，將導致預期的 Crash，保護你免於未定義行為。

以異步版本為例，沒有任何不明朗之處。在函數完成後，執行將總是恢復在最初開始的同一個上下文中。





```swift
await updateStyle(backgroundColor: color)
// style has been updated
```

`withCheckedContinuation` 是一種標準庫API，用於使非 async 和 async 程式碼之間進行交互。

> 註：引入異步程式碼到一個項目中可以浮現資料隔離檢查違反。要理解和處理這些 Violation，請見 [Crossing Isolation Boundaries][]



[Crossing Isolation Boundaries]: commonproblems#Crossing-Isolation-Boundaries
[continuation-apis]: https://developer.apple.com/documentation/swift/continuations

## 靜態孤立化

使用注釋和語言構造表達您的程式靜態孤立化，既是強大也非常緊湊。
然而，它可能很難在不更新所有依賴項的情況下引入靜態孤立化。

靜態孤立化提供了 runtime 機制，您可以將其作為 fallback 使用，以描述數據孤立化。
這樣的工具對於界面 Swift 6 的元件和還未更新的元件尤其重要，即使這些元件位於 _同一_ 模組內。

### 內部孤立

假設您已經確定在您的專案中有一種參考型，可以最佳地描述為 `MainActor` 靜態孤立。
```swift
@MainActor
class WindowStyler  {
    private var backgroundColor: ColorComponents

    func applyStyle()  {
        // ...
    }
}
```
這個 `MainActor` 孤立可能是邏輯上正確的。但是，如果這種類型在其他未遷移的位置中被使用，則將這裡添加靜態孤立可能需要進行許多額外的變更。另一個選擇是使用動態孤立來控制範圍。

```swift
class WindowStyler  {
    @MainActor
    private var backgroundColor: ColorComponents

    func applyStyle()  {
        MainActor.assumeIsolated  {
            // 使用和與其他 `MainActor` 狀態互動
        }
    }
}
```
這裡，孤立已經內部化到類型中。這樣就可以將變更局限於類型，而不會影響類型的客戶。但是，這種方法的主要缺點是類型的真正孤立需求保持不transparent。沒有什麼方法讓客戶 determination 如果或如何根據這個公開API進行變更。

應該僅在遇到其他選擇已經穩定後使用這種方法作為暫時解決方案。

### 使用限制孤立
如果將孤立僅限於某一型別實施困難，可以選擇將孤立擴展到只涵蓋其API使用。

做到這點，先對型別進行靜態孤立，然後在使用位置使用動態孤立：
```
@MainActor
class WindowStyler {
    // ...
}
class UIStyler {
    @MainActor
    private let windowStyler: WindowStyler
    
    func applyStyle() {
        MainActor.assumeIsolated {
            windowStyler.applyStyle()
        }
    }
}
```
將靜態和動態孤立結合可以是一個有力工具，讓變化的範圍逐步增加。

### 易明主要演員上下文

`assumeIsolated` 方法是一個同步方法，旨在從執行環境回復隔離資訊，並將其還原為型別系統，以防止因為假設錯誤而導致執行。否則，這些資訊對编譯器是隱藏的。

`MainActor` 型別也擁有一個方法，可以在異步上下文中手動切換隔離。

```swift
// 尚未更新的應該是 MainActor 的類型
class 個人交通工具  { }
```

```swift
await MainActor.run {
    // 在這裡是隔離的主要演員
    let 運輸 = 個人交通工具()

    // ...
}
```

記住，靜態隔離可以讓编译器 Both verify 和自動化切換隔離的過程。即使使用了靜態隔離，在合併使用 `MainActor.run` 時，也很難确定何時 `MainActor.run` 是真正必要的。

雖然 `MainActor.run` 在遷移期間可以是有用的，但它 shouldn't 作為表達系統隔離需求的 substitute。最终目標仍應該將 `@MainActor` 適用於 `個人交通工具`。

## 缺失註釋
動態隔離給你工具，讓你在執行階段表達隔離。
但是，你也可能發現需要描述其他並發性質，以補充未遷移模組中的缺失。

### 未標記的可送遞關閉

關閉的可送遞特性影響了編譯器對其身體所需的隔離。
一個 callback 关闭，它實際上跨越隔離領域界限，但缺乏 `@Sendable` 註釋違反並發系統的重要不變式。

```swift
// 在 pre-Swift 6 模組中定義
extension JPKJetPack {
    // 註釋 lacked @Sendable 註釋
    static func jetPackConfiguration(_ callback: @escaping () -> Void) {
        // 可能跨越隔離領域
    }
}

@MainActor
class PersonalTransportation {
    func configure() {
        JPKJetPack.jetPackConfiguration { 
            // 在 MainActor 階級會被推斷出來
            self.applyConfiguration()
        }
    }

    func applyConfiguration() {
    }
}
```

如果 `jetPackConfiguration` 可能在另一個隔離領域中invoke其關閉，它就需要標記為 `@Sendable`。
當未遷移模組還沒有做到這一點，它將導致錯誤的主角推斷。
這個代碼會在編譯時沒有問題，但是會在運行時崩潰。

為了解決這個問題，你可以手動標記關閉為 `@Sendable`。
這樣，编译器就知道主角隔離可能發生變化，因此需要在呼叫處加上 await。
```swift
@MainActor
class PersonalTransportation {
    func configure() {
        JPKJetPack.jetPackConfiguration { @Sendable in 
            // @Sendable 关闭不會推斷主角隔離，使這個上下文非隔離
            await self.applyConfiguration()
        }
    }

    func applyConfiguration() {
    }
}
```

## 後向相容性



在建立静態隔離的型別系統時，需要注意的是，這將影響你的公開 API。
但是，你可以遵循一種方式，讓自己的模組在 Swift 6 上獲得改善的 API，而不破壞任何現有的客戶端。
假設 `WindowStyler` 是一個公開 API。
你已經確定它真正應該是以 `MainActor` 進行隔離，但想要保證向後相容性，以便讓現有客戶端繼續使用。

```swift
@preconcurrency  @MainActor
public class WindowStyler {
    // ...
}
```

使用 `@preconcurrency` 這樣標記隔離，將條件限定於客戶端模組也需要啟用 complete checking 才能運行。
這樣保留了與還未開始採用 Swift 6 的客戶端的源相容性。

## Dependencies

通常，你無法控制需要匯入的模組。這些模組如果尚未遵循 Swift 6，可能導致難以解決或不可解決的錯誤。
使用未遷移代碼時，有多種問題會發生。
`@preconcurrency` 注釋可以幫助許多這些情況：

- [非可傳送型別][]
- 協議相容孤立ismatch[]

[非可傳送型別]: commonproblems#Crossing-Isolation-Boundaries
[協議相容孤立ismatch]: commonproblems#Crossing-Isolation-Boundaries

## C/Objective-C
您可以使用註釋，將 SwiftConcurrency 的支持暴露給您的 C 和 Objective-C API。
這是由 Clang 提供的 [concurrency-pecific annotations][clang-annotations]：

[clang-annotations]: https://clang.llvm.org/docs/AttributeReference.html#customizing-swift-import

````
__attribute__((swift_attr__(" Sendable")))  
__attribute__((swift_attr__("nonSendable")))  
__attribute__((swift_attr__("nonisolated"))) 
__attribute__((swift_attr("@UIActor")))

__attribute__((swift_async(.none)))  
__attribute__((swift_async(not_swift_private, COMPLETION_BLOCK_INDEX))) 
__attribute__((swift_async(swift_private, COMPLETION_BLOCK_INDEX))) 
__attribute__((__swift_async_name__(NAME))) 
__attribute__((swift_async_error(none)))
__attribute__((__swift_attr__("@_unavailableFromAsync(message: \"\"msg\"\"\")")))

```

當您使用可以導入 Foundation  的項目時，在 `NSObjCRuntime.h` 中可以使用以下註釋宏：

````
NS_SWIFT_SENDABLE
NS_SWIFT_NONSENDABLE
NS_SWIFT_NONISOLATED
NS_SWIFT_UI_ACTOR

NS_SWIFT_DISABLE_ASYNC
NS_SWIFT_ASYNC(COMPLETION_BLOCK_INDEX)
NS_REFINED_FOR_SWIFT_ASYNC(COMPLETION_BLOCK_INDEX)
NS_SWIFT_ASYNC_NAME
NS_SWIFT_ASYNC_NOTHROW
NS_SWIFT_UNAVAILABLE_FROM_ASYNC(msg)
```

### Objective-C 庫中的缺少隔離註解處理

在 Objective-C 庫和其他 Objective-C 庫中，SwiftConcurrency 的進展，使得我們可以將曾經只存在文件中的合約文本轉化為编譯器和 runtime強制的隔離檢查。例如，在 SwiftConcurrency 之前，API 通常需要使用注釋來説明它們的執行緒行為，像这样“這個函數總是被叫用的在主要執行緒”。

SwiftConcurrency 可以讓我們將這些註釋轉化為编译器和 runtime強制的隔離檢查，這樣 Swift 就會在您使用這些 API 時進行驗證。

例如，假設我們有一個名為 NSJetPack 的虚擬協議，它總是從主要執行緒中調用所有委派方法，因此它現在已經變成 MainActor 隔離的。

庫作者可以使用 `NS_ SWIFT_UI_ACTOR` 屬性標記 MainActor 隔離，與 Swift 中的 `@MainActor` 相同：

```swift
NS_ SWIFT_UI_ACTOR
@protocol NSJetPack  //虛擬協議
   //...
@end
```

由於這個原因，我們可以讓所有成員方法都繼承 MainActor 隔離，但是大多數方法這樣都是正確的。

然而，在這個例子中，假設我們考慮一個方法，它的隔離註解被錯誤地推斷為 MainActor 隔離，因為它的父類型上有注釋。這個方法的隔離註解是：NS_ SWIFT_UI_ACTOR // SDK作者使用 MainActor 在最近的SDKaudits 中進行了注釋。

```objc
@property(readonly) BOOL supportsHighAltitude;  // 虚擬協議方法

@end
```

這個方法的隔離註解被錯誤地推斷為 MainActor 隔離，因為它的父類型上有注釋。這意味著在使用這個方法時，Swift 會自動 inject 執行緒檢查，這樣就會導致執行緒 assert 失敗。

正確的長期解決方案是修復庫中的方法註解，以標記它為 `nonisolated`：

```objc
// 解決方案在庫中： @property(readonly) BOOL supportsHighAltitude NS_ SWIFT_NONISOLATED;
```

直到庫作者修復其注釋問題，您可以使用正確的 `nonisolated` 方法，例如：

```swift
// 解決方案在客戶端代碼中：@MainActor final class MyJetPack: NSJetPack {
   //正確的
  override nonisolated class var readyForTakeoff: Bool {
    true
   }
}
```

這樣 Swift 就知道不需要檢查方法是否需要主要執行緒隔離。

## 派遣
有些你從派遣（Dispatch）或其他并發庫中習慣的模式可能需要重新塑形，以適應 Swift 的結構化並發模型。

### 限制並發使用 Task Groups

有時候，你可能會遇到需要處理的大量工作清單。
 
雖然可以將所有工作項目 enqueue 到一個 Task Group 中，如下所示：
```swift
// WARNING: Potentially wasteful  -- perhaps this creates thousands of tasks concurrently  (?!)
let lotsOfWork: [Work] = ...
await withTaskGroup(of: Something.self) { group in
    for work in lotsOfWork {
        // WARNING: If this is thousands of items, we may end up creating a lot of tasks
        //  which won't get to be executed until much later, as we have a global limit on
        //  the amount of concurrently running tasks  - depending on the core count of the system,
        //  and the default global executor's configuration.
        group.addTask {
            await work.work()
        }
    }

    for await result in group {
        process(result)  // process the result somehow, depends on your needs
    }
}
```
 
如果你懷疑可能會處理數百或數千個項目，它可能會是廢棄的。如果在 `addTask` 中創建一個任務，需要為任務分配一些記憶體，以便 suspend 和 execute 進行，這個amount 的記憶體並不太大，但如果創建數千個任務但不 immediate execution，則可以變得非常大的。
 
當 faced with such a situation，它可能有助於手動調整 Task Group 中的.concurrently added tasks 的數量，如下所示：
```swift
let lotsOfWork: [Work] = ...  // ...
let maxConcurrentWorkTasks = min(lotsOfWork.count, 10)
assert(maxConcurrentWorkTasks > 0)

await withTaskGroup(of: Something.self) { group in
    var submittedWork = 0
    for _ in 0..<maxConcurrentWorkTasks {
        group.addTask { // or 'addTaskUnlessCancelled'
            await lotsOfWork[submittedWork].work()
        }
        submittedWork += 1
    }

    for await result in group {
        process(result)  // process the result somehow, depends on your needs

        // Every time we get a result back, check if there's more work we should submit and do so
        if submittedWork < lotsOfWork.count,
           let remainingWorkItem = lotsOfWork[submittedWork] {
            group.addTask { // or 'addTaskUnlessCancelled'
                await remainingWorkItem.work()
            }
            submittedWork += 1
        }
    }
}
```
 
如果"work"任務涉及長時間的同步代碼，可能需要自願 suspend 任務以允許其他任務执行：
```swift
struct Work {
    let dependency: Dependency
    func work() async {
        await dependency.fetch()
        // execute part of long running synchronous code
        await Task.yield()  // explicitly insert a suspension point
        // continue long running synchronous execution
    }
}
```
 
引入明確的 suspension 點可以幫助 Swift 在此任務和其他任務之間取得平衡。如果這個任務在系統中具有最高優先權，執行器將立即恢復同一個任務的执行。因此，明確的 suspension 點並不一定是避免資源星vation 的方法。