# 20 份多輪盲測對話

僅提供此檔中對應語言的一組四輪對話給被測 agent。逐輪送出，每輪等待回覆；不要一次貼完整腳本，不要提供評分答案。每個 case、每種語言使用全新 session。

## Case 01

### 中文

**T1**

這批病人的一些基因總是一起變動。我懷疑背後有共同的控制者，但光看它們一起升高，好像還不能解釋誰在影響誰。

**T2**

目前先看整批人的共同模式，只考慮會辨識 DNA 的蛋白質。我比較相信把既有生物證據彼此核對、反覆修正的做法；之後也希望沿用同一套推論去看個別病人。

**T3**

現在我改成想知道每位病人有哪些控制者對一群基因的連線特別強，拿來和治療反應比。這個「強」是連到哪些目標、連得多重，不是控制者本身有多活躍。

**T4**

那第一階段的共同結果保留就好；個別病人的部分直接把共同結果複製成每人一份，應該就能接著比較吧？

### English

**T1**

Some genes in this cohort keep changing together. I suspect shared controllers, but seeing them rise together does not seem enough to explain who influences whom.

**T2**

For now, focus on the pattern shared across the cohort and only proteins that recognize DNA. I prefer repeatedly checking biological evidence against the other evidence and updating it; later I want the same inference extended to individual patients.

**T3**

I now want to know which controllers have especially strong connections to groups of genes in each patient, to compare with treatment response. By strong I mean which targets they connect to and the weights of those connections, rather than how active the controller itself is.

**T4**

Keep the shared result from the first stage. For individual patients, could we just copy that shared result once per person and then compare them?

## Case 02

### 中文

**T1**

我在找一群基因為什麼被壓低，但只盯著會結合 DNA 的蛋白質，總覺得漏了一類控制者。

**T2**

我指的是不會被翻譯成蛋白質、能辨識目標轉錄本的短 RNA。想把它們和蛋白質控制者放在同一張關係圖，先看整批人的模式。

**T3**

實驗室只有這些短 RNA 可能辨識哪些目標的證據，沒有量到它們在每個病人的豐度；這樣還值得做嗎？也別把蛋白質互作硬套在它們身上。

**T4**

接著我需要每位病人的版本，仍保留兩類控制者，看看原本在群體中看不出的差異。

### English

**T1**

I am trying to understand why a group of genes is suppressed, but focusing only on DNA-binding proteins feels like it misses another class of controllers.

**T2**

I mean short RNAs that are not translated into proteins and recognize target transcripts. I want them and protein controllers in the same relationship map, initially for the cohort as a whole.

**T3**

The lab only has evidence of which targets those short RNAs might recognize, without measuring their abundance in each patient. Is this still worth doing? Please do not impose protein interactions on them.

**T4**

Next I need a version for each patient that retains both classes of controllers, to reveal differences hidden in the cohort result.

## Case 03

### 中文

**T1**

我想替每位病人的每個控制者算一個「調控強度」，之後看它跟病人的預後有沒有關係。

**T2**

我的意思是，有些控制者自己的轉錄量差不多，下面的基因卻像收到不同強度的指令；我想捕捉這種差異。

**T3**

我希望同時解釋目標的量為什麼不同，以及控制者對目標是偏向推升還是壓低。整批人可以共用那套關係，但每個人的驅動程度可以不同。

**T4**

如果某個控制者的數值很高，就直接說它讓病人死亡風險變高，然後輸出每位病人的因果結論吧。

### English

**T1**

I want a regulatory-strength value for every controller in every patient, and later to see whether it relates to prognosis.

**T2**

I mean controllers whose own transcript levels are similar while their downstream genes look as if they received different strengths of instruction. That is the difference I want to capture.

**T3**

I want to explain both the differences in target levels and whether a controller tends to push a target up or down. The cohort may share those relationships while the driving strength varies by person.

**T4**

If a controller has a high value, just say it increases the patient’s risk of death and give a causal conclusion for each person.

## Case 04

### 中文

**T1**

我要看這批人的共同控制關係，既有生物證據都想保留，但上次分析一直迭代，實驗室等不起。

**T2**

我不要求沿用上次的做法。更想要一個能說清楚在最小化什麼、能調整不同證據權重，而且做滿指定步數就停的方案；控制者限於辨識 DNA 的蛋白質。

**T3**

共同關係得到後，我想找出經常連向同一群目標的控制者，以及那些目標組成的群落。

**T4**

我還要每條關係都有顯著性，而且越少越好；既然可以調整懲罰，就把它當成保證稀疏的開關，順便直接標出每位病人的版本。

### English

**T1**

I want the shared control relationships in this cohort and to retain the biological evidence, but the last analysis kept iterating and the lab cannot wait.

**T2**

I do not need the previous method. I prefer an explicit minimization objective, adjustable weights for the evidence, and a run that stops after a specified number of steps. Controllers are limited to DNA-recognizing proteins.

**T3**

After obtaining the shared relationships, I want groups of controllers that connect to the same sets of targets, together with those target communities.

**T4**

I also want significance for every relationship and as few relationships as possible. Since there is a penalty, treat it as a switch guaranteeing sparsity, and also label a version for each patient.

## Case 05

### 中文

**T1**

兩家醫院的樣本看起來像兩種病，但我不確定是疾病差異，還是採樣和定序方式造成的。

**T2**

每家醫院都有兩種病，年齡和採樣批次也記得清楚。我關心基因一起變動的模式受哪些因素影響，不只是每個基因平均高多少。

**T3**

分開這些因素之後，我想用彼此核對生物證據的方式看共同控制關係，疾病和年齡的生物訊號不能被當成雜訊全部丟掉。

**T4**

剛確認紀錄有誤：其實 A 院全是第一種病，B 院全是第二種病。請仍然把醫院效應完全去掉，保證留下的就是疾病；還要用同一份結果得到每個人的控制關係。

### English

**T1**

Samples from two hospitals look like two diseases, but I cannot tell whether the difference is biological or caused by collection and sequencing practices.

**T2**

Both hospitals have both diseases, and we recorded age and collection batch. I care about factors affecting which genes vary together, beyond differences in each gene’s average level.

**T3**

After separating those factors, I want the shared control relationships using biological evidence checked against the other evidence. Disease and age signals must not all be discarded as noise.

**T4**

The records were wrong: hospital A actually has only disease one and hospital B only disease two. Please still remove the hospital effect completely and guarantee that disease is what remains, and use that same result to obtain each person’s control relationships.

## Case 06

### 中文

**T1**

我有幾百位受試者，想知道同一對基因在不同人身上的關係是不是不同，暫時不討論誰控制誰。

**T2**

每個人只量過一次；同事說這樣不可能替一個人估計兩個基因的關係。我希望利用其他人作為背景，但保留每個人的差異。

**T3**

我更想看「這個人讓整體關係改變多少」，並且能用整批人的結果作為共同參照。目前不需要每條關係各自的顯著性。

**T4**

得到每人的結果後，可以直接把它解讀成甲基因啟動乙基因，然後把這些基因分成控制者和目標去找模組嗎？

### English

**T1**

I have hundreds of participants and want to know whether the relationship between the same two genes differs across people. For now I am not asking who controls whom.

**T2**

Each person was measured once. A colleague says that makes a relationship between two genes impossible to estimate for one person. I want to use the others as background while retaining individual differences.

**T3**

I am more interested in how much this person changes the overall relationship, with the full cohort as a shared reference. I do not currently need significance for each relationship.

**T4**

Once we have each person’s result, can we read it as gene A activating gene B, then divide these genes into controllers and targets to find modules?

## Case 07

### 中文

**T1**

只有六位受試者，我想看各自的基因關係，但最擔心把不穩定的連線當成故事。

**T2**

其他五人的共同模式可以當背景，這個人的觀測再去更新它。每位受試者的每條關係，我都希望知道支持程度，之後自己決定留下哪些。

**T3**

數值已經做過對數轉換並中心化，六人的名稱也都有。請保留所有關係的原始估計和對應支持程度，我不想這次就丟掉比較弱的部分。

**T4**

為了省記憶體，結果可以逐人存，但還是宣稱弱連線已經刪好了；接著把其中一人的結果直接當成全體的共同背景，推哪些蛋白質控制哪些基因。

### English

**T1**

There are only six participants. I want their individual gene relationships, but I am most worried about turning unstable connections into a story.

**T2**

The other five people’s shared pattern could serve as background, updated by this person’s observation. I want support for each relationship in each person, so I can decide later what to keep.

**T3**

The values have been log-transformed and centered, and all six people have names. Please retain every relationship estimate and its corresponding support; I do not want weaker parts discarded yet.

**T4**

To save memory, store results one person at a time, but still say the weak connections have already been removed. Then use one person’s result directly as the whole cohort’s shared background to infer which proteins control which genes.

## Case 08

### 中文

**T1**

同一批人量了轉錄物和蛋白質。有些跨層配對很漂亮，但可能只是一起受到其他分子的影響。

**T2**

我希望在同時考慮兩層其他分子的情況下，看哪些配對還有關係。两層尺度和雜訊不同，處理時不能假定它們完全一樣；先看整批人的共同結構。

**T3**

兩次量測人的順序不同，但人是一樣的。哪種程度的穩定化比較合適我也不知道，希望從資料判斷，別偷偷補缺值。

**T4**

下一批還有代謝物，請一次全放進去，並各自控制轉錄物內部、蛋白質內部和跨層三種懲罰；最後把箭頭標成誰造成誰。

### English

**T1**

Transcripts and proteins were measured in the same people. Some cross-layer pairs look compelling, but they may just share influences from other molecules.

**T2**

I want to see which pairs remain related while accounting for the other molecules in both layers. The layers have different scales and noise, so they should not be treated as identical. Start with the structure shared by the cohort.

**T3**

The people appear in different orders in the two measurements, but they are the same people. I do not know how much stabilization is appropriate; let the data guide it and do not silently fill missing values.

**T4**

The next batch also has metabolites. Put everything in at once, independently control three penalties for within-transcript, within-protein and cross-layer relationships, and label arrows showing who causes whom.

## Case 09

### 中文

**T1**

這批腫瘤很難按單一基因找到共同點：每個病人出問題的位置不同，但我懷疑最後壞的是相似的生物功能。

**T2**

這裡的「出問題」是 DNA 上的體細胞改變，不是轉錄量。很長的基因比較容易碰到事件，有些病人本來就累積很多事件，我不想讓這兩件事主導分類。

**T3**

先把功能層面的相似性保留下來，暫時不替病人貼亞型；而且有些基因在好幾種功能裡重複出現，不能因此被算得特別重要。

**T4**

現在再看看兩到四群哪種比較合理。但既然已經有功能分數，也順便用同一份結果說哪些蛋白質控制了哪些基因。

### English

**T1**

It is hard to find commonality across these tumors one gene at a time: different patients have problems in different places, but perhaps similar biological functions are affected.

**T2**

By problems I mean somatic DNA alterations, not transcript levels. Long genes have more opportunities for events, and some patients accumulate many events overall. I do not want either effect to drive the classification.

**T3**

First preserve similarities at the functional level without labeling patients with subtypes yet. Some genes appear in several functions and should not count as especially important just because they appear repeatedly.

**T4**

Now consider whether two to four groups make sense. Since we already have functional scores, also use that same result to say which proteins control which genes.

## Case 10

### 中文

**T1**

我想把這批資料裡有關係的東西分成幾群，看看哪些群值得後續實驗。

**T2**

不是把病人分群。關係已經估好了，左邊是一類控制者，右邊是它們的目標；我想找出雙方共同形成的群落，不用再估一次關係。

**T3**

有些控制者剛好也是別人的目標，所以兩邊會出現相同名稱。不能直接當作同一類東西，也不要只為了湊兩邊，把任何基因隨便分一側。

**T4**

等等，打開內容發現每一列其實是一個病人，後面是各分子的測量值，沒有先前說的關係。名字雖然寫得像關係結果，你就照剛才的理解繼續吧。

### English

**T1**

I want to put related things in this collection into groups and see which groups are worth following up experimentally.

**T2**

Not groups of patients. Relationships have already been estimated, with one class of controllers on the left and their targets on the right. I want communities formed jointly by both sides, without estimating the relationships again.

**T3**

Some controllers also happen to be somebody else’s targets, so the same name appears on both sides. Do not treat both roles as one kind of object or arbitrarily divide genes just to manufacture two sides.

**T4**

Wait: on inspection, each row is actually a patient followed by molecular measurements, with none of the relationships I described. The label sounds like relationship results, though, so continue with the earlier interpretation.
