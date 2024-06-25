#untime行為

了解 SwiftConcurrency的執行語義如何不同於您可能熟悉的其他執行環境，以及 Familiarize yourself with common patterns to achieve similar end results in terms of execution semantics。

SwiftConcurrency模型的強大特點是async/await、actors和tasks，這意味著其他程式庫或執行環境中的某些模式無法直接翻譯為這個新的模型。在本節中，我們將探討common patterns 和 runtime 行為的差異，讓您了解如何在遷移到 SwiftConcurrency 時Address 這些差異。

## 限制並發使用 Task Groups


有時你可能會遇到大量工作需要處理。



雖然可以直接將所有工作項目 enqueue 到一個task組中，但是這種做法可能會創造數千個任務，對於系統性能產生影響。
```swift
// 潛在的浪費 —— 也許這裡創造了數千個任務 (?!)
let lotsOfWork: [Work] = ...
await withTaskGroup(of: Something.self) { group in
    for work in lotsOfWork {
        // 如果這是數千個項目，我們可能會創造大量任務。
        group.addTask {
            await work.work()
        }
    }

    for await result in group {
        process(result) // 處理結果，根據需要
    }
}
```



如果你預期處理數百或數千個項目，可以將所有工作項目 enqueue 的做法視為無效的。創建一個task (在 `addTask` 中) 將分配記憶體用於中止和執行任務。
因為每個任務的記憶體需求不是太大，但是在創造數千個任務時，記憶體分配可以導致性能下降。


當面對這種情況，你可以手動控制task組中的.concurrently added tasks 的數量，以以下方式進行：
```swift
let lotsOfWork: [Work] = ...
let maxConcurrentWorkTasks = min(lotsOfWork.count, 10)
assert(maxConcurrentWorkTasks > 0)
await withTaskGroup(of: Something.self) { group in
    var submittedWork = 0
    for _ in 0..<maxConcurrentWorkTasks {
        group.addTask { // 或 'addTaskUnlessCancelled'
            await lotsOfWork[submittedWork].work()
        }
        submittedWork += 1
    }

    for await result in group {
        process(result) // 處理結果，根據需要

        // 每次我們回傳結果後，就檢查是否有更多工作要提交，並進行提交。
        if submittedWork < lotsOfWork.count, let remainingWorkItem = lotsOfWork[submittedWork] {
            group.addTask { // 或 'addTaskUnlessCancelled'
                await remainingWorkItem.work()
            }
            submittedWork += 1
        }
    }
}
```