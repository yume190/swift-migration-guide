# 平常編譯錯誤
識別、理解並處理您在使用 Swift 同步程式時遇到的常見問題。
compiler 的數據隔離保證對所有 Swift 代碼生效。這意味著完整的同步檢查可以揭示潛在問題，即便是在不直接使用 concurrency 語言特性的一些 Swift 5代碼中。
啟用 Swift 6 語言模式後，這些潛在問題也可能成為錯誤。
after 啟用完整檢查，許多項目可能包含大量警告和錯誤。
_不要_ 感到被壓垮！大多數這些錯誤可以追溯到較少的一組根本原因。
而且，這些原因，經常是由於常見模式所導致，這些模式不僅容易修正，也能夠幫助您理解 Swift 的數據隔離模型。

## 非安全全域及靜態變數

全域狀態，包括靜態變數，是任意地方在程式碼中的存取。

這種可見性使它們對於並發存取特别脆弱。

在資料競爭安全前，全域變數模式仰賴程式設計師小心地訪問全域狀態，以免出現資料競爭，而不需要編譯器的幫助。

> 實驗：這些代碼範例可以在套件中找到。自己試試看在 [Globals.swift][Globals] 中。

[Globals]: https://github.com/apple/swift-migration-guide/blob/main/Sources/Examples/Globals.swift

### 可傳送類型
```
var 支持樣式計數 = 42
```
在這裡，我們已經定義了一個全域變數。
全域變數從任何隔離領域中都是非孤立的，並且可以進行修改。將上述代碼在 Swift 6 模式下编译後，會出現錯誤訊息：
```
1  | var 支持樣式計數 = 42
   |               |- 錯誤：全域變數 '支持樣式計數' 是因為它是非孤立的全球共享可變狀態，而不是並發安全的
   |               |- 註解：將 '支持樣式計數' 轉換為 'let'常數，以使共享狀態變得不可變
   |               |- 註解：限制 '支持樣式計數' 只能在主要行程中存取
   |               |- 註解：危險地標 '支持樣式計數' 為並發安全的，如果所有存取都是由外部同步機制保護的
2  |
```
兩個具有不同隔離領域的函數存取這個變數，risk data races。以下代碼中，`printSupportedStyles()` 可能在主要行程中與 `addNewStyle()` 在其他隔離領域中存取：
```
@MainActor
func printSupportedStyles()  {
    print("支持樣式：", 支持樣式計數)
}

func addNewStyle()  {
    let style = Style()
    支持樣式計數 += 1
    storeStyle(style)
}
```
要解决問題的一種方法是將變數的隔離方式改變。
```
@MainActor
var 支持樣式計數 = 42
```
變數仍然可以進行修改，但是已經隔離到了全域行程中。所有存取現在都只能發生在一個隔離領域中，而同步存取在 `addNewStyle` 中將在編譯時期被無效化。
如果變數是意味著為常數，並且從不進行修改，可以直截所給的解決方案。通過將 `var` 變成 `let`，编译器可以靜態地Disallowmutation， Guarantee safe read-only access。
```
let 支持樣式計數 = 42
```
如果存在同步機制保護這個變數，以致編譯器無法檢測出來，你可以使用 `nonisolated(unsafe)` 語法禁用所有隔離檢查：
```
/// 這個值僅在持有 'styleLock' 時才被存取。
nonisolated(unsafe) var 支持樣式計數 = 42
```
只使用 `nonisolated(unsafe)` 時，你應該小心地保護變數的存取，以致外部同步機制保護，例如鎖或派遣隊列。

### 非可发送類型

在上面的範例中，變數是一個 `Int`，這是一種本質上是可以发送的值類型。全域參考類型則另有一個挑戰，因為他們通常不是可发送的。
```swift
class WindowStyler  {  
    var background: ColorComponents  

    static let defaultStyler  = WindowStyler()  
} 
```
這個 `static let`聲明與變數是否可寫入無關。問題是，`WindowStyler`是一個非可发送的類型，因此其內部狀態不安全地跨越隔離領域共享。
```swift
func resetDefaultStyle()  {  
    WindowStyler.defaultStyler.background  = ColorComponents(red: 1.0, green: 1.0, blue: 1.0)  
}  

@MainActor  
class StyleStore  {  
    var stylers: [WindowStyler]  

    func hasDefaultBackground() -> Bool  {  
        stylers.contains { $0.background == WindowStyler.defaultStyler.background }  
    }  
} 
```
在這裡，我們看到兩個函數可以同時存取 `WindowStyler.defaultStyler` 的內部狀態。編譯器只允許這種跨隔離領域存取與可发送類型。
一個選項是使用全域Actor來隔離變數到單一領域。如果有意義，可以直接添加對 `Sendable` 的遞承。

## 協議相容性孤立不符
協議定義了一個符合協議的類型所需滿足的需求。
Swift 確保了協議的客戶能夠以尊重資料孤立的方式與其方法和屬性進行互動。
為此，兩者都需要指定靜態孤立。
這可能導致協議聲明與符合協議類型之間的孤立不符。

這種問題有很多可能的解決方案，但是這些方案通常涉及權衡。
選擇適當的approach 首先需要了解為什麼發生了 mismatch 。

> 實驗：這些代碼範例已經在package形式提供。
試試自己在 [ConformanceMismatches.swift][ConformanceMismatches] 中執行這些代碼。

[ConformanceMismatches]: https://github.com/apple/swift-migration-guide/blob/main/Sources/Examples/ConformanceMismatches.swift

### 缺乏明確協議

最常遇到的這種問題發生在協議中沒有明確的隔離。
在這種情況下，像所有其他聲明一樣，這暗示著非隔離協議要求。
非隔離協議需求可以從泛用代碼中在任何隔離領域被叫用。如果需求是同步的，它就無效地對遵循協議的類別實現進行Actor隔離狀態訪問：

```swift
protocol Styler  { 
    func applyStyle() 
} 

@MainActor 
class WindowStyler: Styler  { 
    func applyStyle()  { 
        //存取主演員隔離狀態
     } 
}
```

上面的代碼在 Swift 6 模式下產生錯誤：

```swift
5  | @MainActor
6  | class WindowStyler: Styler  { 
7  |     func applyStyle()  { 
|           |- error: main actor-isolated instance method 'applyStyle()' cannot be used to satisfy nonisolated protocol requirement
|          `- note: add 'nonisolated' to 'applyStyle()' to make this instance method not isolated to the actor
8  |          //存取主演員隔離狀態
9  |      } 
```

這可能是協議本身應該被隔離，但還沒有更新為并發環境。
如果遵循協議的類別先進行正確隔離，然後進行更新，這樣就會產生ismatch。

```swift
// 這只在主演員類型中才有意義，但還沒有更新以反映這一點。
protocol Styler  { 
    func applyStyle() 
} 

// 一個遵循協議的類別，現在正確地隔離了，但暴露了一個ismatch。
@MainActor 
class WindowStyler: Styler  { 
} 
```

#### 添加隔離
如果協議需求始終從主演員呼叫，添加 `@MainActor` 是最佳的解決方案。

有兩種方法可以將協議需求隔離到主演員：

```
// 整個協議
@MainActor
protocol Styler {
    func applyStyle()
}

// 按需隔離
protocol Styler {
    @MainActor
    func applyStyle()
}
```

標記協議為全域演員屬性意味著所有協議需求和延伸方法都將受到全域演員隔離的影響。此外，當非延伸方式進行符合協議的情況時，還會被推斷為全域演員。


按需隔離具有較窄的演員隔離影響，因為推斷只適用於該需求的實現，不會影響協議延伸或其他方法在遵循類型中的演員隔離。这種approach應該是青睞，如果它能使符合協議的類型不一定也與同一個全域演員相關聯。

無論哪種方式，変更協議的隔離都可能會影響遵循類型的隔離，並且可以限制使用協議在泛型需求中的泛型代碼。你可以使用 `@preconcurrency` 來_STAGE_Diagnostics_ caused by adding global actor isolation on a protocol：

```
@preconcurrency @MainActor
protocol Styler {
    func applyStyle()
}
```

#### 非同步需求
為實現同步協議需求的方法，該方法要麼與需求的隔離完全匹配，要麼就是 `nonisolated`，這意味著該方法可以從任何隔離領域呼叫，無需擔心数据競爭情況。使需求非同步提供了更多的彈性，以滿足符合類型的隔離。

```swift
protocol Styler {
    func applyStyle() async
}
```

因為 `async` 方法保證了隔離，Switch 到相應的行為者在實現中，所以可以使用隔離方法滿足非同步協議需求：

```swift
@MainActor
class WindowStyler: Styler {
    //match，儘管它是同步且行為者隔離的
    func applyStyle() {
    }
}
```

上述代碼是安全的，因為泛型代碼總是以非同步方式呼叫 `applyStyle()`，允許隔離實現Switch 行為者前.access actor 隔離狀態。

然而，這種彈性需要支付成本。將方法變為非同步可能對每個呼叫站點有顯著影響。在additions to an async 上下文，參數和返回值都需要跨越隔離界限。此外，這些可能需要進行結構化的改變以address。

這可能仍然是正確的解決方案，但是在涉及到的類型較少的情況下，也應該小心考慮side- effects。

#### 預Concurrency 合作性

Swift 提供了多種機制，幫助您逐步採用Concurrency，並與尚未使用Concurrency 的代碼進行互操作。這些工具既可適用於您不控制的代碼，也可應用於您擁有的代碼，但無法輕鬆地進行改變。

使用 `@preconcurrency`  annotation 來標注協議 conformance，讓您可以忽略任何隔離 mismatch 的錯誤。

```swift
@MainActor
class WindowStyler: @preconcurrency Styler {
    func applyStyle() {
        // 實現身體
    }
}
```

這樣就會插入 runtime 檢查，以確保符合的類別始終維持静态隔離。

> 注意：了解逐步採用和動態隔離更多內容，請參考 [Dynamic Isolation][]

[Dynamic Isolation]: incrementaladoption#Dynamic-Isolation

### 孤立符合型態
到目前為止，所提出之解決方案假設孤立不符的原因 Ultimately rooted 在 協議定義上。
但它可能是協議的靜態孤立性正確，而問題的真正原因只是一個符合型態。

#### 非孤立的
即使是一個完全非孤立的函數，它仍然可以是有用的。
```swift
@MainActor
class WindowStyler: Styler  {
    nonisolated func applyStyle() {
         // 或許這個實作不涉及其他 MainActor-孤立狀態
     }
}
```
非孤立的實現的下落是一種孤立狀態和函數無法使用。這確實是主要的限制，但是仍然可以適用，特別是在它被專門用於 instance-獨立設定的來源時。

#### (Translation)

#### 代理適應性
它可能使用中間型別幫助解決靜態隔離差異。
這種方法特别有效，如果協議需要其遵循類型的繼承。
```swift
class UIStyler {
}
```
```swift
protocol Styler : UIStyler {
    func applyStyle()
}

actor WindowStyler : Styler {
}
```

引進一個新的類型，間接遵循可以使這種情況工作。但是，這個解決方案將需要對 `WindowStyler` 的結構進行改變，並且可能影響相依的代碼。

```swift
struct CustomWindowStyle : Styler {
    func applyStyle() {
    }
}
```
在這裡，一個新的類型已經創建，能夠滿足所需的繼承。在將其整合到 `WindowStyler` 時，最好只使用遵循於內部。

（Note: I kept the original Markdown formatting and made sure to use Traditional Chinese characters and Taiwan-style names, as requested.）

## 簡隔界限

任何需要從一個孤立領域移動到另一個孤立領域的值，
都必須是 `Sendable` 或保留互斥存取。使用不滿足這些要求的值在需要它们的地方，是非常常見的問題。
因為庫和框架可能會更新以使用 Swift 的 concurrency 特性，這些問題也可能出現在您的代碼還沒有變更的情況下。

> 實驗：這些代碼範例可以在package形式中找到。自己嘗試執行這些範例，詳見 [Boundaries.swift][Boundaries]。

[Boundaries]: https://github. com/apple/swift-migration-guide/blob/main/Sources/Examples/ Boundaries.swift

### 隱含可傳送類型
許多值類型只包含 `_Sendable` 屬性。
編譯器將這種類型視為隱含 `_Sendable`，惟有在它們不是非公共的時候。
```swift
public struct ColorComponents  { 
    public let red: Float
    public let green: Float
    public let blue: Float
} 

@MainActor 
func applyBackground(_ color: ColorComponents)  { 
} 

func updateStyle(backgroundColor: ColorComponents) async  { 
    await applyBackground(backgroundColor) 
} 
```
`_Sendable` 相容性是類型的公共 API 合約的一部分，這是你需要宣告的。
因為 `ColorComponents` 標記為 `public`，因此不會隱含相容 `_Sendable`。
這將導致以下錯誤：
```swift
 6 | 
 7 | func updateStyle(backgroundColor: ColorComponents) async  { 
 8 |     await applyBackground(backgroundColor) 
    |- error: sending 'backgroundColor' risks causing data races
    `- note: sending task-isolated 'backgroundColor' to main actor-isolated global function 'applyBackground' risks causing data races between main actor-isolated and task-isolated uses
 9 | } 
10 | 
```
直截了當的解決方法是，將類型的 `_Sendable` 相容性表現為明文：
```swift
public struct ColorComponents: Sendable  { 
     // ... 
} 
```
即使是簡單的，添加 `_Sendable` 相容性總是需要小心的。
記住 `_Sendable` 是 thread 安全性的保證，是類型的 API 合約的一部分。
將相容性移除是 API 切換的變化。

### 前置並行import

即使在另一個模組中定義的型別實際上是 `Sendable`，但仍不一定能夠修改它的定義。

這種情況下，您可以使用 `@preconcurrency import` 來壓制錯誤直到庫更新為止。

```swift
// ColorComponents 在這裡定義
@preconcurrency import UnmigratedModule

func updateStyle(backgroundColor: ColorComponents) async {
    // 途經隔離領域 여기
    await applyBackground(backgroundColor)
}
```

隨著增加這個 `@preconcurrency import`，`ColorComponents`仍然不是 `Sendable`。然而，編譯器的行為將會被改變。在使用 Swift 6 語言模式時，這裡所產生的錯誤將降級為警告。Swift 5 語言模式將不產生任何診斷信息。

### 潛在隔離

有時候，需要一個 `_apparent_` 的 `Sendable` 型別實際上是潛在隔離問題的症狀。
一個型別需要是 `Sendable` 就是要跨越隔離邊界。如果可以避免跨越邊界altogether，結果往往較為簡單，也反映系統的真實特性。

```swift
@MainActor
func applyBackground(_ color: ColorComponents) { }
 
func updateStyle(backgroundColor: ColorComponents) async {
    await applyBackground(backgroundColor)
}
```

`updateStyle(backgroundColor:)` 函數不是隔離的。
這意味著非隔離參數也是非隔離的。
實際上，這個函數從非隔離域即刻跨越到 `MainActor` 時候呼叫 `applyBackground(_:)`。

因為 `updateStyle(backgroundColor:)` 正在直接與 `MainActor` 隔離函數和非 `Sendable` 型別進行工作，僅將 `MainActor` 隔離應用可能更合適。

```swift
@MainActor
func updateStyle(backgroundColor: ColorComponents) async {
    applyBackground(backgroundColor)
}
```

現在，不再有隔離邊界讓非 `Sendable` 型別需要跨越。
在這種情況下，不僅解決問題，還刪除了無需异步調用的需求。
解决潛在隔離問題也可能使 API 簡化。

缺乏 `MainActor` 隔離是一種最常見的潛在隔離形式。
對於開發者來說，這是一個非常正常的狀態。程式具有使用界面的話，通常會有很大的 `MainActor` 隔離狀態。

對於長期同步工作的擔憂，可以通過少數特定的非隔離函數進行addressing。

### 計算值
 
嘗試將非「可傳遞」類型通過邊界，而可能使用一個可以創造所需值的「可傳遞」函數。
 
```swift
func updateStyle(backgroundColorProvider: @Sendable () -> ColorComponents) async {
    await applyBackground(using: backgroundColorProvider)
}
```
 
在這裡，不管 `ColorComponents` 不是「可傳遞」，使用一個可以計算值的「可傳遞」函數，缺乏 sendability 完全被繼承。

### 可傳送符合性
當遇到隔離領域交界問題時，很自然的反應是試圖將符合性添加到 `Sendable` 中。你可以以四種方式使得一個類型變為 `Sendable`。

#### 全球孤立

將全球孤立添加到任何類型中，使其隐含地成為 `Sendable`。
```swift
@MainActor
public struct ColorComponents {
    // ...
}
```
通過將這個類型孤立於 `MainActor`，從其他孤立領域進行存取的所有存取都必須异步進行。這使得可以安全地將實例傳遞到跨域的領域。

(Note: I kept the code block intact and translated only the surrounding text.)

#### 演員們

演員們自然地具有 `Sendable` conformance，因为其屬性受到演員隔離的保護。
```swift
actor 風格 {
    private var 背景：顏色成分 {}
}
```
除了獲得 `Sendable` conformance之外，演員們還獲得了自己的孤立領域。这允許他們在內部自由運用其他非 `Sendable` 型別。這可能是有優點，但也會帶來某些折中的考慮。

因為演員的孤立方法都需要異步執行，
因此訪問類型的站點可能需要一個async 上下文。这本身是一個需要小心改變的原因。但是進一步地，傳入或從演員中出出的數據可能需要跨越隔離邊界。这可能導致需要更多 `Sendable` 型別。

#### 手動同步協調
如果您已經擁有一種類型，該類型正在進行手動同步，您可以將Sendable conformance標記為`unchecked`以告知编譯器。
```swift
class Style: @unchecked Sendable {
    private var background: ColorComponents
    private let queue: DispatchQueue
}
```
您不應該感到強迫去移除使用隊列、鎖定或其他手動同步形式來整合SwiftConcurrency系統。然而，大多數類型並不是 thread-safe 的。
總的規律是，如果某種類型原本就不是线程安全的，那麼嘗試將其`Sendable`化不應該是您的首選。
這樣通常更容易，您可以先嘗試其他技術，等真正必要時才使用手動同步。

(Note: I kept the original formatting and markup, as it was provided in Markdown format.)

#### 可送引考標式

可將引用型別驗證為 `Sendable` без `unchecked` qualifier，但這只會在非常狹隘的情況下進行。

允許checked `Sendable` conformance，class 必須：

* 是 `final` 的
* 無法繼承其他class，只能繼承 `NSObject`
* 無非隔離的可變屬性

```swift
public struct ColorComponents: Sendable { 
    // ...
}

final class Style: Sendable {
    private let background: ColorComponents
}
```

遵從 `Sendable` 的引用型別，有時候是 struct 的好選擇，但是在某些情況下，需要保留引用 semantics 或與 mixed Swift/ Objective-C代碼庫base 兼容。



#### 使用Composition
您不需要選擇單一的技術來創建引用型別`Sendable`。
一個類型可以內部使用多種技術。

```swift
final class Style : Sendable  {
    private(nonisolated(unsafe)) var background: ColorComponents
    private let queue: DispatchQueue
    
    @MainActor
    private var foreground: ColorComponents
}
```

`background` 屬性受到手動同步的保護，while `foreground` 屬性使用 actor 隔離。
這兩種技術的組合結果是一個類型，它更好地描述其內部 semantics。
透過這樣做，類型繼續 tận dụng編譯器的自動隔離檢查。

### 非孤立初始化

演員隔離類型在非孤立上下文中進行初始化時，可能會出現問題。
這種情況常見於類型用於默認值表達式或物件 initializer 時。

> 註：這些問題也可能是[潜在隔離](#潜在隔離)或[不明確協議](#不明確協議)的症狀。

在這裡，非孤立的`Stylers`類型正在對一個`MainActor`-isolated initializer 進行呼叫。
```swift
@MainActor
class WindowStyler  {
    init()  {
     }
}
struct Stylers  {
    static let window = WindowStyler()
}
```
這個代碼將導致以下錯誤：
```swift
7 | 
8 | struct Stylers  {
9 |     static let window = WindowStyler()
 |- error: main actor-isolated default value in a non-isolated context
10 |
11 |
```
全球隔離類型有時不需要在初始化方法中參考任何全局演員狀態。
通過將`init` 方法標記為`nonisolated`，它便可以從任何孤立上下文中被呼叫。
這仍然是安全的，因為編譯器保證了任何隔離的狀態只有在`MainActor` 中才能訪問。

```swift
@MainActor
class WindowStyler  {
    private var viewStyler = ViewStyler()
    private var primaryStyleName: String

    nonisolated init(name: String)  {
        self.primaryStyleName = name
         // 類型在這裡已經完全初始化
     }
}
```

所有`Sendable` 屬性仍然可以從這個`init` 方法中安全地訪問。
而任何非`Sendable` 屬性的不能，然而卻可以使用默認表達式進行初始化。

### 非隔離式 deinitialization

即使類型具有.actor 獨立性，deinitializers 也_總是_非隔離的。

```swift
actor BackgroundStyler {
    // 另一個.actor-獨立型別
    private let store = StyleStore()

    deinit {
        // 這裡不是隔離的
        store.stopNotifications()
    }
}
```

這個代碼產生錯誤：

```swift
error: 在同步非隔離上下文中呼叫.actor-獨立實例方法 'stopNotifications()'
 5 |     deinit {
 6 |          // 這裡不是隔離的
 7 |         store.stopNotifications()
    |               `error: 在同步非隔離上下文中呼叫.actor-獨立實例方法 'stopNotifications()'
 8 |      }
 9 | } 
```

雖然這可能感到驚奇，考慮到這個類型是.actor，但是這並不是新約束。執行 deinitializer 的線程從不被保證，Swift 的資料隔離現在正表現出這個事實。

通常，deinit 內的工作不需要同步。解決方案是使用未結構化的Task 將隔離值捕捉並操作。在使用這種技巧時，是 _關鍵_ 保證你不捕捉 `self`，即使是隱式地。

```swift
actor BackgroundStyler {
    // 另一個.actor-獨立型別
    private let store = StyleStore()

    deinit {
        // 這裡不是隔離的，所以task 不會繼承隔離
        Task { [store] in
            await store.stopNotifications()
        }
    }
}
```

> 重要：**絕不**從 `deinit` 延長 `self` 的生命週期。在 runtime 時執行的代碼將導致崩潰。