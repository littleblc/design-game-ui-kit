# Murdoku案例上下文

本例来自此用户已完成的一套游戏UI流程。只在继续该游戏或参考上次产物时使用，先检查文件是否仍存在，勿假设绝对路径永远有效。

- 游戏资产根目录：`E:/unityworkspace/Murdoku/MurdokuProject/Assets`。
- 玩法/表现脚本：`GameScripts/HotFix/GameLogic/Murdoku/Core` 与 `Presentation`。
- 已确认视觉稿：`E:/Remotion/design/murdoku-home-settings-v1/home-settings-concept.png`。
- 制作工作目录：`E:/Remotion/design/murdoku-home-settings-ready`。
- 当前交付包：`E:/Remotion/design/murdoku-home-settings-Unity-ready.zip`。
- 半身人物试稿：`E:/Remotion/design/murdoku-portraits-12`，原游戏头像另在 `E:/Remotion/design/murdoku-ui-v2/10-project-original-portraits`。

玩法是读人物证词并推理摆位：轻触候选、长按确认；每行每列最多一个人，家具占用格不能站人；最后重建现场验证并识别凶手。设置音效/音乐/振动与语言，主页包含开始、选关、任务、设置。相关属性以当前代码为准。

画风：暖纸色、深青绿、少量琥珀/珊瑚红，扁平侦探档案元素。主页面Logo为MURDOKU/格中疑云，O结合放大镜和网格；720×1280竖屏基准。不要把这些作为所有新游戏的默认风格。

已发现的重要约束：PortraitGameLayout会在运行时重排证词、棋盘与操作区域，并写入部分固定高度/offset。任何新的Unity布局接入应检查当前版本，避免Inspector摆放被覆盖。

用户明确的质量偏好：先看示意图再决定拆分；一旦同意拆分，要求真正可用的透明独立元素，不能用局部矩形截图或简化重画敷衍。半身头像不要带卡框或底色。动态文字与UI皮肤分开；生成图里的棋盘格需检查是否真Alpha。前次38张PNG中的主档案插画是整幅装饰层，不代表内部照片和道具已独立。

可参考现有制作脚本，但它们包含该图专用坐标、抠图阈值和路径；不得直接作为新图的通用工具。先检查结果再改用当前任务适合的方法。
