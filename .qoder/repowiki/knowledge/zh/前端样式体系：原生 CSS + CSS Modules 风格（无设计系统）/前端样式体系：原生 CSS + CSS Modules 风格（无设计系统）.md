---
kind: frontend_style
name: 前端样式体系：原生 CSS + CSS Modules 风格（无设计系统）
slug: frontend_style
category: frontend_style
scope:
    - '**'
---

## 1. 使用的系统与工具

- **构建工具**：Vite 5 (`vite.config.ts`)，React 18 + TypeScript。
- **样式方案**：**原生 CSS 文件**，每个组件一个 `.css` 文件，与组件同名并放在同一目录（如 `BacktestForm.tsx` ↔ `BacktestForm.css`），通过 `import './xxx.css'` 引入。没有使用 CSS Modules、SCSS、Less、Tailwind、Styled Components 或任何 UI 组件库。
- **图表库**：`recharts`（用于回测结果可视化），图标库 `lucide-react`。
- **无第三方样式框架**：`package.json` 中未声明 Tailwind、Ant Design、MUI、Bootstrap 等依赖。

## 2. 关键文件

- `frontend/src/index.css` — 全局 reset 与基础样式（`box-sizing: border-box`、body 字体栈、背景色 `#f5f7fa`、`#root` 最小高度）。
- `frontend/src/App.css` — 应用级布局：header 渐变、主内容区 grid（`300px 1fr`）、sidebar / content-area 分区、响应式断点（`1024px`、`768px`）。
- `frontend/src/components/BacktestForm.css` — 表单区域样式（数据源选择器、输入框、提交按钮渐变、加载 spinner）。
- `frontend/src/components/StrategyList.css` — 策略卡片列表、自定义滚动条、选中态高亮。
- `frontend/src/components/BacktestResult.css` — 回测结果展示（未在读取范围内，但遵循相同命名约定）。

## 3. 架构与约定

### 3.1 文件组织
- 样式按**组件粒度**拆分，每个 React 组件对应一个同名 `.css` 文件，位于同目录下。
- 全局样式集中在 `index.css`，仅包含 reset、body 字体、根容器；页面级布局在 `App.css`。

### 3.2 命名约定
- 类名采用 **kebab-case**（如 `.backtest-form`、`.strategy-card`、`.data-source-select`），语义化命名，无 BEM 前缀、无 CSS Modules 的哈希后缀。
- 组件状态通过额外 class 控制（如 `.strategy-card.selected`、`.submit-button:disabled`），而非 CSS-in-JS 动态类名。

### 3.3 视觉主题
- **主色调**：紫色系渐变 `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`，贯穿 header、按钮、滚动条 thumb、选中态边框。
- **中性色**：背景 `#f5f7fa`，卡片白底 `white`，边框 `#e0e0e0`，文字 `#333` / `#666` / `#999`。
- **圆角**：统一使用 `8px`（输入框、卡片）和 `12px`（大区块如 sidebar-section、backtest-section）。
- **阴影**：轻量 `box-shadow: 0 2px 8px rgba(0,0,0,0.05)` 用于卡片，hover 时加深。
- **动效**：CSS `@keyframes` 定义（logo 的 `pulse`、按钮 loading 的 `spin`），transition 时长统一为 `0.3s ease`。

### 3.4 响应式策略
- 使用纯 CSS `@media (max-width: ...)` 断点：
  - `1024px`：grid 从双列切换为单列，sidebar/content-area 通过 `order` 重排。
  - `768px`：header 纵向排列、padding 缩小、表单 grid 变为单列。
- 布局主要依赖 **Flexbox** 与 **CSS Grid**（`grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))` 实现自适应网格）。

## 4. 约定与约束

- **观察到的约定**（描述性）：
  - 每个组件与其样式文件同名且同目录，通过相对路径 import。
  - 所有交互态（hover/focus/selected/disabled）通过伪类或附加 class 表达。
  - 颜色值以十六进制硬编码，未提取为 CSS 变量或设计 token。
  - 动画使用原生 `@keyframes`，无第三方动画库。
  - 滚动条通过 `::-webkit-scrollbar` 伪元素自定义（仅 WebKit 浏览器）。

- **可验证的规则**（由代码结构体现）：
  - 项目未引入任何 CSS 预处理器或原子化框架（`package.json` 无相关依赖）。
  - 样式未被封装到 JS/CSS-in-JS 中——全部是独立 `.css` 文件。
  - 不存在跨组件共享的样式变量或主题配置（无 `:root` 变量、无 `tailwind.config.js`、无 `theme.ts`）。
  - 响应式断点固定为 `1024px` 与 `768px` 两处，未见其他断点。

## 5. 总结

该前端采用**最简化的原生 CSS 方案**：无设计系统、无组件库、无构建期样式转换。样式风格由一组重复出现的视觉常量（紫色渐变、圆角、阴影、间距）构成事实上的“主题”，但这些常量并未被抽象为可复用的 token。整体适合小型内部工具，扩展性有限，新增组件需手动维护一致的视觉规范。