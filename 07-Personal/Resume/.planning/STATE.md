# STATE — Personal / Resume

## Current Task
## 任務：CK SRE Resume 2026 英文版翻譯
- 目標：依 `CK-SRE-Resume-2026.md` 產出可投遞的英文版履歷。
- 方法：以既有英文版為基礎，重新對照中文原文，保留職涯時間線、量化成果與主要技術關鍵字，改寫為自然英文。
- 驗證：英文版需涵蓋專業摘要、核心技能、主要工作經驗、認證、教育與量化亮點，且與中文原文一致。
- 影響範圍：`CK-SRE-Resume-2026-EN.md`、`.planning/STATE.md`、`.planning/ROADMAP.md`、`.planning/CONTEXT.md`

## User Story
身為求職中的資深 SRE / DevOps / Platform Engineering 候選人，我希望將目前的中文履歷翻譯成專業英文版，以便投遞外商或英文職缺。

## Acceptance Criteria
1. 英文版保留原始中文履歷的主要經歷、職稱、公司、時間與量化成果。
2. 英文表述自然、專業，適合招聘主管與 ATS 閱讀。
3. 不修改原中文履歷，僅更新英文版檔案。

## API / Data Notes
- Input: `CK-SRE-Resume-2026.md`
- Output: `CK-SRE-Resume-2026-EN.md`, `CK-SRE-Resume-2026-EN-Full-v2.md`
- Data Structure Changes: None
- Estimated Impact: Small
- Downstream Affected Use Cases: English job applications, ATS submission, recruiter sharing
- Required Verification: Manual review

### [2026-05-12 12:35] — 新增 Full detail 英文完整版任務
- **Phase**: Phase 1 — Resume Translation and Alignment
- **Status**: Complete
- **Done**: 讀取既有 Full 版英文履歷與目前規劃，並新增 `CK-SRE-Resume-2026-EN-Full-v2.md`，作為比精簡版保留更多經歷細節與量化成果的英文長版履歷。
- **Next**: 可再依投遞需求將 `EN.md` 作為 ATS 精簡版、`EN-Full-v2.md` 作為長版說明版，或再客製 SRE / Platform Engineering Manager / DevOps Manager 版本。
- **Blocker**: 無

### [2026-05-12 12:20] — 初始化 Resume 子專案 planning 並建立翻譯規格
- **Phase**: Phase 1 — Resume Translation and Alignment
- **Status**: Complete
- **Done**: 讀取中文履歷與現有英文版，建立 `.planning/CONTEXT.md`、`ROADMAP.md`，並完成更新 `CK-SRE-Resume-2026-EN.md` 為可投遞的英文版，保留主要經歷、量化成果與 ATS 友善結構。
- **Next**: 可再依投遞需求拆分為 2-page ATS 版、Full detail 版或針對特定職缺的 SRE / Platform Engineering Manager 客製版。
- **Blocker**: 無
