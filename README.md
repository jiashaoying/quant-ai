# 股票量化策略查看系统

一个本地运行的股票量化策略查看与回测系统，支持 **8 种量化策略**（含深度学习）、**多数据源智能切换**、**策略参数自定义**和**完整可视化回测分析**。

## ✨ 功能特性

### 策略引擎
- **8 种量化策略**：覆盖趋势跟踪、均值回归、超买超卖、通道突破、多因子模型、深度学习
- **参数自定义**：每种策略均支持在前端调整参数，实时回测
- **深度学习支持**：可选安装 PyTorch，启用 Transformer 深度学习策略

### 数据源
- **5 种数据源**：腾讯财经、YFinance、AKShare、BaoStock、模拟数据
- **智能降级**：A股自动优先使用腾讯财经，失败时逐级降级，最终兜底模拟数据
- **前端切换**：可在页面上手动选择数据源
- **模拟数据标识**：真实数据获取失败自动使用模拟数据时，回测结果会明确标注

### 回测与可视化
- **回测引擎**：计算收益率、夏普比率、最大回撤、胜率等完整指标
- **图表展示**：资金曲线图、股价走势图
- **交易记录**：详细买卖记录表
- **性能统计**：年化收益率、盈亏比、交易次数等

## 📊 策略列表

| # | 策略 | 类型 | 核心思想 |
|---|------|------|---------|
| 1 | 均线交叉策略 | 趋势跟踪 | 短期均线上穿长期均线买入（金叉），下穿卖出（死叉） |
| 2 | 动量策略 | 趋势跟踪 | 基于价格动量追涨杀跌 |
| 3 | 均值回归策略 | 均值回归 | 价格偏离均值时反向交易 |
| 4 | RSI策略 | 超买超卖 | RSI 超卖买入、超买卖出 |
| 5 | 布林带策略 | 通道突破 | 基于 %B 指标，触及下轨买入、触及上轨卖出 |
| 6 | 多因子选股策略 | 多因子模型 | 综合动量、波动率、换手率、均线偏离、RSI 五大因子加权打分 |
| 7 | Transformer价格预测策略 | 注意力机制 | 多头自注意力捕捉价格序列长距离依赖，预测未来走势 |
| 8 | Transformer深度学习策略 | 深度学习 | 基于 PyTorch 的完整 Transformer 架构（位置编码 + 多头注意力 + FFN） |

## 🌐 数据源

| 数据源 | 适用市场 | 是否需要额外安装 | 优先级 |
|--------|---------|----------------|--------|
| 🐧 腾讯财经 | A股（上证/深证）、港股 | 否（内置） | A股/港股最高 |
| 🌍 YFinance | 美股、港股 | 否（已安装） | 美股最高 |
| 📊 AKShare | A股全面数据 | 是（`pip install akshare`） | A股备用 |
| 📈 BaoStock | A股历史数据 | 是（`pip install baostock`） | A股备用 |
| 🎲 模拟数据 | 全部 | 否（内置） | 兜底 |

**智能降级策略**：
```
A股/港股:  腾讯财经 → YFinance → AKShare → BaoStock → 模拟数据
美股:      YFinance → 模拟数据
```

## 🛠 技术栈

### 后端
- **框架**：FastAPI + Uvicorn
- **数据库**：SQLite + SQLAlchemy
- **数据处理**：Pandas, NumPy
- **数据源**：腾讯财经 API（requests）、yfinance、akshare、baostock
- **深度学习**：PyTorch（可选）
- **机器学习**：scikit-learn（可选）

### 前端
- **框架**：React 18 + TypeScript
- **构建工具**：Vite
- **UI组件**：原生 CSS + Lucide 图标
- **图表库**：Recharts

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 3. 访问系统

- **前端界面**：http://localhost:3000
- **后端 API**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs

### 4.（可选）安装深度学习依赖

```bash
cd backend
source venv/bin/activate

# 安装 PyTorch CPU 版（约 200MB）
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 安装 scikit-learn
pip install scikit-learn
```

安装后即可使用"Transformer 深度学习策略"。

## 📖 使用说明

### 1. 选择策略
页面加载后自动选中第一个策略。在左侧策略列表中点击切换，列表支持滚动浏览。

### 2. 配置参数
- **股票代码**：A股上证 `600519.SS`（贵州茅台）、深证 `000858.SZ`（五粮液）；美股 `AAPL`
- **回测周期**：1个月 ~ 5年
- **初始资金**：自定义投资金额
- **数据源**：选择行情数据来源（默认自动选择）
- **策略参数**：根据所选策略调整，每个参数都有说明和取值范围

### 3. 运行回测
点击"开始回测"，系统自动获取数据 → 生成信号 → 模拟交易 → 输出报告。

### 4. 查看结果
- **性能指标**：总收益率、年化收益率、夏普比率、最大回撤
- **资金曲线**：资金变化趋势图
- **股价走势**：股票价格走势图
- **交易记录**：详细买卖记录
- **数据源标识**：显示实际使用的数据源
- **模拟数据提示**：若使用模拟数据，页面标题和结果中会明确标注

## 📁 项目结构

```
quant-ai/
├── backend/
│   ├── app/
│   │   ├── api/                    # API 路由
│   │   │   ├── backtest.py         # 回测 API
│   │   │   ├── strategies.py       # 策略列表 API
│   │   │   └── market.py           # 市场数据 API
│   │   ├── backtest/
│   │   │   └── engine.py           # 回测引擎（指标计算）
│   │   ├── core/
│   │   │   └── config.py           # 应用配置
│   │   ├── db/
│   │   │   └── database.py         # 数据库连接
│   │   ├── models/
│   │   │   └── models.py           # 数据模型
│   │   ├── services/
│   │   │   ├── market_data.py      # 市场数据服务
│   │   │   └── data_source_manager.py  # 多数据源管理器
│   │   └── strategies/
│   │       ├── engine.py           # 策略引擎（7种策略）
│   │       └── transformer_dl.py   # 深度学习策略（PyTorch）
│   ├── main.py                     # FastAPI 入口
│   └── requirements.txt            # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── StrategyList.tsx    # 策略列表（可滚动）
│   │   │   ├── BacktestForm.tsx    # 回测表单（含数据源选择 + 策略参数）
│   │   │   └── BacktestResult.tsx  # 回测结果（含模拟数据标识）
│   │   ├── App.tsx                 # 主应用
│   │   └── main.tsx                # 入口
│   ├── package.json
│   └── vite.config.ts
├── AGENTS.md                       # 开发者指南
├── QUICKSTART.md                   # 快速启动指南
└── README.md                       # 本文件
```

## ⚠️ 注意事项

1. **数据源**：A股数据优先通过腾讯财经 API 获取（免费、无需注册），需网络连接
2. **模拟数据**：所有数据源获取失败时自动降级为模拟数据，回测结果会标注"（模拟数据）"
3. **回测局限**：未考虑交易成本（手续费、滑点）、涨跌停限制，简化了交易执行逻辑
4. **深度学习**：Transformer 深度学习策略需额外安装 PyTorch，未安装时该策略不可用但其他功能不受影响
5. **风险提示**：本系统仅供学习研究，不构成任何投资建议

## 🔮 后续优化方向

- [x] 添加更多量化策略（8种已实现）
- [x] 多数据源支持（腾讯财经/YFinance/AKShare/BaoStock）
- [x] 策略参数自定义
- [x] 模拟数据自动标识
- [x] 深度学习策略（Transformer）
- [ ] 策略参数优化（网格搜索/遗传算法）
- [ ] 实时行情监控
- [ ] 自定义股票池
- [ ] 交易成本计算
- [ ] 导出回测报告（PDF/Excel）
- [ ] 策略对比功能
- [ ] 用户账户系统

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
