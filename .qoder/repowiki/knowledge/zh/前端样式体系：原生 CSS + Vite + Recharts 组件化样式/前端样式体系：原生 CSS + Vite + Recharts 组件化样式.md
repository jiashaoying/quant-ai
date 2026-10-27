---
kind: frontend_style
name: 前端样式体系：原生 CSS + Vite + Recharts 组件化样式
category: frontend_style
scope:
    - '**'
source_files:
    - frontend/package.json
    - frontend/src/index.css
    - frontend/src/App.css
    - frontend/src/components/BacktestForm.css
    - frontend/src/components/StrategyList.css
    - frontend/src/components/BacktestResult.css
---

## 1. 采用的系统与工具

- **构建与开发**：Vite 5（`vite.config.ts`），配合 `@vitejs/plugin-react`，通过 `npm run dev / build / preview` 启动。
- **语言**：React 18 + TypeScript，样式使用 **原生 CSS 文件**（每个 `.tsx` 组件旁配一个同名 `.css`），未引入任何 CSS-in-JS、CSS Modules、SCSS/Sass、Tailwind 或 UI 组件库。
- **图标**：`lucide-react`（0.312.0）作为统一图标来源。
- **图表**：`recharts`（2.10.4）负责回测结果可视化；Recharts 的默认主题通过 CSS 变量覆盖。
- **HTTP 客户端**：`axios`，与样式无关但属于前端依赖的一部分。

## 2. 关键文件

- `frontend/package.json`：声明所有前端依赖与脚本。
- `frontend/src/index.css`：全局 reset、字体栈、背景色 `#f5f7fa`、`#root` 最小高度。
- `frontend/src/App.css`：应用级布局（header、sidebar、content-grid）、主色调渐变、响应式断点。
- `frontend/src/components/BacktestForm.css`：回测表单、数据源选择器、参数输入、提交按钮。
- `frontend/src/components/StrategyList.css`：策略卡片列表、自定义滚动条、选中态。
- `frontend/src/components/BacktestResult.css`：回测结果摘要卡片、指标网格、交易表格、图表容器。

## 3. 架构与约定

### 3.1 样式组织方式
- 采用 **按组件拆分 CSS 文件** 的方式：每个 React 组件目录内同时存在 `.tsx` 与同名 `.css`，例如 `BacktestForm.tsx` ↔ `BacktestForm.css`。没有统一的 tokens 文件或主题配置。
- 全局样式集中在 `index.css`，仅做基础 reset（`box-sizing: border-box`）、字体栈、背景色和 `#root` 高度。
- 应用骨架在 `App.css` 中定义：
  - 顶部 header 使用 `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` 紫色渐变。
  - 主体采用 `display: grid; grid-template-columns: 300px 1fr` 的双栏布局（左侧 sidebar + 右侧 content-area）。
  - 侧边栏区块使用白色圆角卡片（`border-radius: 12px` + `box-shadow: 0 2px 8px rgba(0,0,0,0.05)`）。

### 3.2 设计令牌（隐式）
仓库中没有显式的 design token 文件，但通过重复出现的值形成隐式规范：
- **主色**：`#667eea`（蓝紫）与 `#764ba2`（深紫）构成渐变主题。
- **中性色**：背景 `#f5f7fa`，卡片白 `#fff`，边框 `#e0e0e0`，次要文字 `#666` / `#999`，标题 `#333`。
- **语义色**：正数 `#10b981`（绿），负数 `#ef4444`（红），警告/提示用橙色系（`#fb923c`、`#c2410c`）。
- **阴影与圆角**：卡片普遍使用 `border-radius: 8px~12px`，hover 时添加 `transform: translateY(-2px)` 与 `box-shadow`。
- **过渡**：交互元素统一 `transition: all 0.3s ease`。

### 3.3 响应式策略
- 使用 CSS `@media` 查询，两个主要断点：`1024px`（平板）和 `768px`（手机）。
- 在 `1024px` 以下：`grid-template-columns` 从双栏切换为单栏，sidebar 通过 `order` 上移。
- 在 `768px` 以下：header 内容纵向排列、padding 缩小、表单/指标网格变为单列。
- 组件内部也各自维护响应式（如 `BacktestForm.css`、`BacktestResult.css` 中的 `auto-fit` + `minmax` 网格）。

### 3.4 动画与状态
- 头部 logo 图标使用 `@keyframes pulse` 实现呼吸缩放。
- 提交按钮禁用态使用 `opacity: 0.6` + `cursor: not-allowed`。
- 加载 spinner 使用 `@keyframes spin` 旋转。
- 策略卡片选中态通过 `.selected` 类名切换边框颜色与半透明渐变背景。

### 3.5 图表样式
- 基于 Recharts 的默认主题，通过 CSS 变量（如 `--chart-background`、`--fontFamily`）进行覆盖，见 `BacktestResult.css` 中对 `.chart-container` 的样式封装。

## 4. 约定与约束

- **样式文件命名**：组件样式与组件同名并放在同一目录下（`.tsx` ↔ `.css`），这是仓库中已观察到的模式。
- **不使用 CSS Modules / CSS-in-JS**：所有样式均为普通 CSS，类名直接由组件 JSX 的 `className` 引用，无模块作用域隔离。
- **不引入第三方 UI 框架**：未发现 Ant Design、MUI、Chakra、Tailwind 等依赖，全部手写 CSS。
- **渐变主题一致性**：主渐变色 `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` 在 header、submit button、scrollbar thumb、data-source-select hover 等处重复出现，构成视觉一致性的核心手段。
- **响应式断点集中**：全仓统一使用 `1024px` 与 `768px` 两个断点，未见其他断点。
- **无设计令牌系统**：颜色、间距、字号等值以硬编码形式散布在各 CSS 文件中，没有 `:root` 变量或共享常量文件——这既是现状也是扩展点。
- **滚动条定制**：仅在 `StrategyList.css` 中使用 `::-webkit-scrollbar` 伪元素对策略列表滚动条做了品牌色渐变处理，其余区域使用浏览器默认滚动条。

## 5. 总结

该前端是一个轻量级的 React + Vite 项目，样式完全基于原生 CSS，按组件拆分文件，通过重复的蓝紫渐变主色、统一的圆角/阴影/过渡动效以及 1024px/768px 双断点响应式策略维持视觉一致性。当前没有设计令牌、CSS 变量主题或组件库，未来如需扩展可考虑将隐式令牌抽取到 `:root` 变量或引入 Tailwind 以收敛样式规范。