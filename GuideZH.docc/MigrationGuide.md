# 導入 Swift 6

@Metadata {  
   @TechnologyRoot 
}

@Options(scope:全局){  
   @AutomaticSeeAlso(disabled)  
   @AutomaticTitleHeading(disabled)  
   @AutomaticArticleSubheading(disabled)  
}

## 過erview

Swift 的Concurrency 系統，自 Swift 5.5 起便能夠簡化寫作並讓理解更加容易。  
隨著 Swift 6 語言模式的引入，編譯器現在能夠保證 concurrency 程式庫中無資料競爭。  
當啟用語言安全檢查時，這些檢查將從之前的選項變為必需。

您可以根據目標獨立地控制 Swift 6 語言模式。
既有使用於前一個模式的目標，另外使用其他語言暴露給 Swift 的代碼，都能夠與已遷移到 Swift 6 語言模式的模組進行交互。

您的項目可能正在逐步採用 concurrency 功能。  
或者，您可能等待 Swift 6 釋出後才開始使用。  
無論您項目處於何種過程，這本指南提供了概念和實際幫助，讓您更容易遷移。

在這裡，你將找到文章和代碼範例，它們將：

* 說明Swift 的資料競爭安全模型所用的概念。
* 提出可能的遷移方式。
* 顯示如何啟用 Swift 5 項目中的完整 concurrency 檢查。
* 顯示如何啟用 Swift 6 語言模式。
* 呈現解決常見問題的策略。
* 提供逐步採用的技巧。

> 注意：Swift 6 語言模式為 _選項_。  
已有的項目將不會自動遷移到這個模式，需要進行配置變更。

> 有關 compiler 版本和語言模式之間的重要區別。

Swift 6 编译器支持四種不同的語言模式：「6」、「5」、「4.2」和「4」。

> 註：這本指南仍在活躍開發中。您可以查看原始碼、查看完整代碼範例，並學習如何貢獻到 [repository][] 中。

[repository]: https://github.com/apple/swift-migration-guide

## 主題

- <doc:資料競爭安全>
- <doc:遷移策略>
- <doc:完整檢查>
- <doc:iOS 14 模式>
- <doc:常見問題>
- <doc:逐步採用>

### 快速Concurrency深入探析

-
(doc: Runtime行為)