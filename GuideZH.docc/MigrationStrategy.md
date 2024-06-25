# 迁移到 Swift 6 語言模式
開始將您的項目遷移到 Swift 6 語言模式。
在模組中啟用完整的並發檢查，可能會報告許多資料競爭安全問題。
這些警告可能數百甚至數千個。
當您面臨這麼大的問題集時，尤其是您還在學習 Swift 的資料隔離模型，這可能讓您感到絕望。

**不要驚慌。**
通常，您只需要進行幾項變更就可以取得實際進度。
隨著您的進度，您對於 SwiftConcurrency 系統的認知也會rapidly develop。

> importantes：這些建議不應被解釋為建議。你應該感到自信地使用其他方法。

## 策略
本文件概述了一個可作為起點的通用策略。
沒有單一的方法可以適用於所有專案。
策略具有三個關鍵步驟：

* 選擇模組
* 對Swift 5進行更嚴格的檢查
*處理警告
這個過程將是 _iterative_ 的。即使單一的變動在一個模組中也可能對整個專案的狀態產生大幅影響。

## 開始從外圍

可以從外圍最外層的模組開始。這就是說，這不會是任何其他模組的依賴關係。
這裡的變化只可能產生局部影響，讓您能夠將工作限定於某個範圍內。

## 使用 Swift 5 語言模式
你可能發現將專案從 Swift 5 直接移到 Swift 6 語言模式會很挑戰。
相反，您可以逐步啟用更多的 Swift 6 檢查機制，繼續使用 Swift 5 模式。
這樣就能 Surface 問題，只是一個警告，而您的建置和測試仍然可行。
要開始，請啟用單一的即將到來的並發性功能。
這樣就可以讓您專注於一次一種問題。

提議     | 描述  | 功能旗標 
:-----------|-------------|-------------|
[SE-0401][]  | 移除 Actor 隔離推斷（caused by 屬性 wrapper）  | `DisableOutwardActorInference` 
[SE-0412][]  |嚴格並發性全球變數  | `GlobalConcurrency` 
[SE-0418][]  | 將方法和鍵文字推斷為 `Sendable`  | `InferSendableFromCaptures`

[SE-0401]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0401-remove-property-wrapper-isolation.md
[SE-0412]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0412-strict-concurrency-for-global-variables.md
[SE-0418]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0418-inferring-sendable-for-methods.md

這些功能旗標可以獨立啟用，並且可以在任何順序下啟用。
當您已經處理了由未來的功能旗標所揭露的問題後，下一步就是啟用完整檢查［CompleteChecking］for 模組。
這樣就會啟動所有编譯器剩餘的數據隔離檢查。

## Warning警示處理

你應該遵循的guiding原則是：**表現当前真實情況**。抵制對代碼進行修改，以便解決問題。
你將發現， minimized the amount of change needed to achieve a warning-free state with complete concurrency checking 是非常有益的事情。然後，你可以使用之前所應用的 unsafe opt-outs 作為引入一個更安全的隔離機制的機會。

> 注意：欲了解常見問題處理，請見<doc:CommonProblems>。

## 迭代

起初，你很可能會使用技術來disable或 bypass 資料隔離問題。

當你覺得自己已經到達了高級模組的終點，然後鎖定其中的一個依賴項，該依賴項需要 workaround。

你不需要刪除所有警告以繼續進行下一步。記住，有時候非常 minor 的變化可以有顯著的影響。你總是可以回頭來更新一個模組，一旦其依賴項已經被更新。