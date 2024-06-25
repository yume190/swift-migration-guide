# 資料競爭安全性

學習 Swift 中使用的基本概念，讓您能夠撰寫資料競爭免疫的同步代碼。
傳統上，.Mutable state 需要通過精心的 runtime 同步保護。
使用工具，例如鎖定和佇列，預防資料競爭取決於程式設計師本身。这是非常困難的不僅如此，也需要長期保持正確性。
即使确定需要同步也可能會遇到挑戰。
最糟的是，無法 Guarantee 失敗的代碼在 runtime 時可能仍會執行。
這種代碼通常似乎能夠運作，也可能是因為需要 highly 不尋常的情況來展現資料競爭中錯誤和不可預測的行為。
更多正式地，資料競爭發生於一個 thread存取記憶體，而另一個 thread meanwhile 正在變更相同的記憶體。
Swift 6 語言模式 eliminar 這些問題，通過在編譯時間中防止資料競爭。

>Important：您可能曾經遇到其他語言中的 `async`/`await` 和 actors 建構式。請特別注意，Swift 中的這些概念可能只是一種外觀相似處。

## 資料孤立

Swift 的Concurrency 系統允許編譯器理解和驗證所有可變狀態的安全性。

它透過名為《資料孤立》的機制實現這點。

資料孤立保證互斥存取可變狀態。這是一種同步化的方式，類似於鎖定。

然而，與鎖定不同的是，資料孤立提供的保護在編譯時發生。

Swift 程式設計師通過兩種方式與資料孤立交互：

靜態地和動態地。

靜態指的是無法受到 runtime 狀態影響的程式元素，這些元素，如函數定義，都是由關鍵字和註釋組成。Swift 的Concurrency 系統是其型別系統的延伸。當您聲明函數和類別時，您正在靜態地進行聲明。孤立可以是這些靜態聲明的一部分。

然而，在某些情況下，型別系統獨力不能夠充分描述系統的行為。例如，一個Objective-C 型別被暴露給 Swift，這種聲明由於不是在 Swift 代碼中進行，因此可能無法提供足夠信息給編譯器以確保安全使用。為了適應這些情況，還有額外的功能允許您express孤立要求動態地。

無論是靜態或動態，資料孤立都允許編譯器確保您的 Swift代碼不包含資料競爭。

### 孤立領域
資料孤立是保護共享可變狀態的《機制》。
然而，它們經常有用於談論獨立單位的孤立領域。
這就是所謂的《孤立領域》。
某個領域負責保護的狀態數量會廣泛不同。一個孤立領域可能保護單一變數，
或整個子系統，例如使用者界面。

孤立領域的關鍵特徵是它們提供的安全性。
可變狀態只能從一個孤立領域同時存取一次。
你可以將可變狀態從一個孤立領域傳給另一個，但你不能
從不同的領域並發地存取該狀態。
這個保證由编譯器驗證。

即使你自己沒有明確定義過，所有函數和變數聲明都具有固定的靜態
孤立領域。
這些領域總是落入三種類別之一：
1. 非孤立
2. 對於 actor 值進行孤立
3. 對於全局 actor 進行孤立

### 非隔離
函數和變數不需要是明確的隔離領域的一部分。
實際上，缺乏隔離就是默認狀態，稱為非隔離。這種缺乏隔離就像是一個自己獨立的領域一樣。
因為所有資料隔離規則適用，因此無法將protected在另一個領域中的状态進行 mutate。

```
```swift
func 運海() {
}
```

```

### 演員
演員提供了一種定義孤立領域的方法，
隨之運算在該領域中的方法。
每個存儲的實例屬性都被隔離到該演員實例中。

```swift
actor 島 { 
    var 蜂群：[雞] 
    var 食物：[鳯梨]

    func 加入蜂群() { 
        蜂群.append(雞()) 
     } 
}
```
這裡，每個 `島` 實例都定義了一個新的領域，
該領域將用於保護對其屬性的存取。
方法 `島.加入蜂群` 說明為 `self` 隔離的。
方法體能夠存取所有與之共享同一個隔離領域的數據，
因此，`蜂群` 屬性同步可存取。

演員隔離可以選擇禁用。
這在你想將代碼組織在孤立類型中，但 opt-出隔離要求的情況下很有用。
非隔離方法不能同步訪問任何保護狀態。

```swift
actor 島 { 
    var 蜂群：[雞] 
    var 食物：[鳯梨]

    nonisolated func 可以長大() -> 植物種 { 
        // 這裡無法存取蜂群或食物
     } 
}
```
演員隔離領域不僅限於其方法。
接受孤立參數的函數也能夠獲得演員-孤立狀態存取權，
而且不需要任何其他形式的同步。

```swift
func 加入蜂群(of 島: 隔離 Island) { 
    島.蜂群.append(雞()) 
}

### 全球演員

全球演員擁有regular actor的所有特性，但還能靜態地將聲明分配到其隔離領域。這是透過匹配演員名稱的註解所實現的。全球演員對於當群類型都需要作為一個共享不可變狀態池時特別有用。

```swift
@主要演員
class ChickenValley  {
    var flock: [雞]
    var food: [鳯梨]
}
```

這個類別靜態隔離到 `主要演員`。這保證所有對其不可變狀態的存取都是從該隔離領域進行的。

您可以選擇退出這種演員隔離，使用 `nonisolated` 关键字。

和 Actor 类型一樣，您將無法存取任何保護狀態。

```swift
@主要演員
class ChickenValley  {
    var flock: [雞]
    var food: [鳯梨]

    nonisolated func 可以生長() -> 植物種  {
        // 在這裡不可變狀態中的flock、food或任何其他主要演員隔離狀態都是不可存取的
    }
}

### 任務

一個 `任務` 是指可以並發執行於您的程式中的單位工作。
Swift 中，您無法在外部使用 task 進行並發執行， 
然而，這並不意味著您總是需要手動啟動一個 task。
通常，非同步函數不需要知道正在執行task的資訊。
事實上，tasks 可能會開始於較高層級， 
在應用程式框架中，或者甚至是您的整個程序的根源。

tasks 之間可以並發執行，但是每個單獨的 task 只會執行一次函數。 
它們會按照順序執行代碼，從開始到結束。

```swift
Task {
    flock.map(Chicken.produce)
}
```

一個 task toujours 有一個孤立領域。它們可以被孤立於某個 actor 的實例中、全域actor 中，或者是非孤立的。
這種孤立可以通過手動設定，但也可以自動繼承基于上下文。

task 的孤立，與所有其他 Swift代碼相同，決定了它們能夠存取什麼可變狀態。

tasks 可以執行同步和非同步代碼。無論結構如何，以及有多少 tasks_involved，同一孤立領域中的函數不能並發執行。
將只有一個 task 執行同步代碼，與任何給定的孤立領域相關。

> 注意：欲了解更多信息，請查看《Swift 程式語言》中[Task]的部分。

[Tasks]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency#Tasks-and-Task-Groups

### 孤立推斷和繼承
有很多方法可以明確指定孤立。
但是，有些情況下，宣告的上下文會以《孤立推斷》方式暗示孤立。

(Note: I've used the term "孤立" to translate "isolation", as it is commonly used in Taiwanese Mandarin. I've also maintained consistency in translating "inference" as "推斷".)

#### 類別

subclass 永遠具有與其父類似的隔離性。
```swift
@主線程執行 Actor
class 動物  {
}

class 鴨子 : 動物  {
}
```
因為 `鴨子` 繼承自 `動物`，因此 `動物` 型別的靜態隔離性也會被隐式套用。
不僅如此，它們還無法被subclass所改變。
所有 `動物` 實例都已經聲明為 `主線程執行` 隔離性，這意味著所有 `鴨子` 實例都必須相同。
。

靜態隔離性也會默認為類別的屬性和方法。
```swift
@主線程執行 Actor
class 動物  {
    // 本型別內所有聲明也都是隱式 `主線程執行` 隔離性
    let 名稱: String

    func 吃(食材: 菜青瓜)  {
    }
}
```

> 註：更多資訊，請參閱《Swift 程式語言》中的 [繼承][] 區段。

[繼承]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/inheritance

#### 協定

協定符合可以間接影響孤立。
然而，協定的孤立效果取決於該符合方式的運用。

```swift
@主要執行緒
protocol Feedable  {
    func eat(food: Pineapple)
}

// 噴射孤立只適用於整個類型
class Chicken: Feedable  {
}

// 噴射孤立僅適用於擴展部分
extension Pirate: Feedable  {
}
```

協定的需求本身也可以進行孤立。
這樣允許對符合類型的孤立进行更細微控制。

```swift
protocol Feedable  {
    @主要執行緒
    func eat(food: Pineapple)
}
```

不管協定是如何定義和符合，无法變更其他靜態孤立機制。
如果某個類型是全局孤立的，即使是透過 superclass 的推斷，一個協定符合不能用來改變它。

> 註：欲了解更多信息，請參考《Swift 程式語言》中的[協定]一節。

[協定]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/protocols

#### 功能類型

_isolation inference_ 允許類型隐含定義其屬性和方法的隔離。
但是，這些都是《聲明》的範例。
還是有可能透過功能值，實現相似的效果，通過隔離_inheritance_。

一個封閉體可以捕捉到在其聲明所在地點的隔離，而不是類型靜態定義的隔離方式。
這個機制聽起來可能複雜，但是在實踐中，它允許非常自然的行為。

```swift
@MainActor
func eat(food: Pineapple) {
    // 静态隔离这个函数的聲明被封閉體創建所捕捉
    Task {
        // 允许封閉體的主題繼承 MainActor-隔離
        Chicken.prizedHen.eat(food: food)
    }
}
```

在這裡，封闭体的類型由 `Task.init` 定義。
尽管聲明不是隔離到任何演員，但這個新的任務將_inherit_ 封閉體的enclosing	scope 的 `MainActor` 隔離。

需要注意的是，這種形式的隔離繼承必须使用 `isolated(any)` 注釋進行Explicitly。
功能類型提供了控制其隔離行為的一些機制，但默認情況下，它們的行为與其他類型相同。

> 註：更多信息，請見《Swift Programming Language》的[封閉體][]章節。

[封閉體]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/closures

## 隔離界限

隔離領域保護其可變狀態，但有用程式需要更多。它們需要通訊和協調，經常通過將資料傳遞回來。

將值進出隔離領域稱為跨越隔離界限。
只有在沒有對共享可變狀態的並發存取可能的情況下，才能允許值跨越界限。
值可以直接跨越界限，通過異步函數呼叫。
它們也可以間接跨越界限，因為被封閉所捕捉。

當你使用異步函數，與不同的隔離領域一起呼叫時，參數和回傳值需要跨越界限。
封閉引入了許多跨越隔離界限的機會。它們可以在一個領域中創建，並且在另一個領域中執行。
甚至可以在多個不同的領域中執行。

### 可傳送類型

有些情況下，一個特定的類型的所有值都可以安全地通過隔離界限傳遞，因為它們本身具有線程安全性。這種線程安全性類型的屬性由 `Sendable` 協議所表示。

當您在文檔中看到某種類型符合 `Sendable` 協議時，意味著該類型是线程安全的，可以將值分享給任意隔離領域，而無法引發数据竞争。

Swift鼓勵使用值類型，因為他們自然安全。用值類型不同部分的程序就不能共享相同的值。
當您將值類型的實例傳遞給函數時，該函數將擁有獨立的值副本。
因為值 semantics 保證了所有的mutable state在不同的執行個體中，因此Swift中的值類型隐含地是 `Sendable`，假如所有儲存的屬性都是 Sendable 的。

然而，這種隐含的符合性並不在外部模組中可見。

將一個class標記為 `Sendable` 是該public API 合同的一部分，並且需要明確地進行操作。

```swift
enum ripeness  { 
    case hard 
    case perfect 
    case mushy(daysPast: Int) 
}

struct Pineapple  {
    var weight: Double
    var ripeness: Ripeness
}
```

這裡，`Ripeness` 和 `Pineapple` 都是隐含地 `Sendable` 的，因為他們完全由 `Sendable` 值類型組成。

> 註：欲了解更多資訊，請參考《The Swift Programming Language》的[可傳送類型][]部分。

[可傳送類型]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency#Sendable-Types

### 演員孤立型別
演員不是值型別，但因為它們保護所有state在自己的孤立領域中，
因此，它們天然地安全傳遞至界限。
這使得演員型別隐含地是`Sendable`，即使他們的屬性本身不是`Sendable`。

```swift
actor 島  {
    var 雞群：[雞]   // 非 Sendable
    var 食物：[鳯梨]  // Sendable
}
```
全域演員孤立型別也因類似原因而隐含地是`Sendable`。
它們沒有私人、專門的孤立領域，但其state仍受到演員保護。

```swift
@MainActor
class 雞谷  {
    var 雞群：[雞]   // 非 Sendable
    var 食物：[鳯梨]  // Sendable
}
```
作為`Sendable`，演員和全域演員孤立型別總是安全傳遞至界限。

### 參考類型
與值類型不同，參考類型無法隐式地成為 `Sendable`。
雖然它們可以被做成 `Sendable`，
但是這需要滿足一系列限制。
要使一個類別 `Sendable`，它必須沒有可變狀態。
而任何不可變的屬性也Must是 `Sendable`。
此外，编译器只能驗證 final 類別的實現。
```swift
final class 鴨子 : Sendable {
    let name: String
}
```
可以使用同步primitive來滿足 `Sendable` 的線程安全要求，
例如通過 OS-特定的construct 或
當與 C/C++/Objective-C 中實現的 thread-safe 型別進行工作。
這種型別可能被標記為遵循 `@unchecked Sendable`，承諾編譯器該型別是線程安全的。
編譯器將不對一個 `@unchecked Sendable` 型別進行檢查，
因此，這個選項出Must用以小心。

### 停頓點

任務可以在一個孤立領域中切換到另一個孤立領域，當一個領域中的函數呼叫另一個領域中的函數時發生。

跨越孤立界限的呼叫必須非同步進行，因為目標孤立領域可能正在執行其他任務。如果這樣，任務將被停頓直到目標孤立領域可用。

重要的是，停頓點不會阻塞。目前的孤立領域（及其所在的執行緒）會釋放，以便進行其他工作。
SwiftConcurrency runtime預期代碼從不會在未來工作上阻塞，這允許系統始終能夠進步。這消除了並發代碼中的一種常見死鎖問題。

```swift
@MainActor
func stockUp()  {
    // 在 MainActor 上開始執行
    let food = Pineapple()

    //切換到島嶼.actor 的領域
    await island.store(food)
}
```

可能的停頓點在源代碼中以 `await` keyword 標記。它的出現表示呼叫可能會在 runtime 時停頓，但 `await` 不會強制停頓。函數被調用的函數可能只在某些動態條件下停頓。
可能有一個帶有 `await` 的呼叫不會實際地停頓。

Note: I've translated the code and text according to your guidelines, using Taiwan's formal writing style.

### 原子性

雖然演員可以保證資料競爭的安全，但是他們不會確保原子性跨越中斷點。
因為当前孤立領域被释放，以執行其他工作，.actor 隔離狀態可能在異步呼叫後發生變化。
因此，你可以視之為明確標記潛在中斷點，以表明批評區的結束。
```swift
func deposit(pineapples: [Pineapple], onto island: Island) async {
    var food = await island.food
    food += pineapples
    await island.store(food)
}
```
這個代碼假設，錯誤地，以為 `island` 演員的 `food` 值在異步呼叫之間不會發生變化。
批評區應該總是以同步方式構建。

> 註：更多信息請參考《The Swift Programming Language》中的
[定義和呼叫非同步函數][] 區塊。

[定義和呼叫非同步函數]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/#Defining-and-Calling-Asynchronous-Functions