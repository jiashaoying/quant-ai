# 多数据源支持 - 更新说明

## 🎉 新功能

系统现已支持**多数据源自动切换**，包括：

### 1️⃣ AKShare（推荐用于A股）
- **优势**：免费、无需注册、数据全面
- **支持**：A股、基金、期货、债券等
- **安装**：`pip install akshare`

### 2️⃣ BaoStock（A股专业数据）
- **优势**：免费、专业A股数据、历史数据丰富
- **支持**：A股日K、周K、月K线
- **安装**：`pip install baostock`

### 3️⃣ YFinance（美股/港股）
- **优势**：全球市场数据
- **支持**：美股、港股、指数等
- **已安装**：✓

### 4️⃣ 模拟数据（备用）
- **优势**：无需网络、立即可用
- **用途**：测试、演示

## 📦 安装新数据源

### 方式1：安装全部（推荐）
```bash
cd backend
source venv/bin/activate
pip install akshare baostock
```

### 方式2：只安装 AKShare（A股推荐）
```bash
pip install akshare
```

### 方式3：只安装 BaoStock
```bash
pip install baostock
```

## 🔄 工作原理

系统会**自动选择最佳数据源**：

```
1. 检测股票市场
   ├─ A股（.SS/.SZ）→ 优先 AKShare → BaoStock → YFinance → 模拟数据
   ├─ 港股（.HK）→ YFinance → 模拟数据
   └─ 美股 → YFinance → 模拟数据

2. 智能降级
   - 如果某个数据源失败，自动尝试下一个
   - 最终兜底：模拟数据
```

## 💡 使用示例

### A股测试（安装AKShare后）

```python
# 股票代码格式
600519.SS  # 贵州茅台（上证）
000858.SZ  # 五粮液（深证）
601318.SS  # 中国平安
000001.SZ  # 平安银行
```

### 美股测试

```python
AAPL  # 苹果
GOOGL # 谷歌
MSFT  # 微软
TSLA  # 特斯拉
```

## 🔧 手动指定数据源

在API调用时可以指定数据源：

```python
POST /api/backtest/run
{
  "strategy_id": "ma_cross",
  "symbol": "600519.SS",
  "period": "1y",
  "source": "akshare"  # 可选：auto, yfinance, akshare, baostock, mock
}
```

## 📊 数据源对比

| 数据源 | A股 | 美股 | 港股 | 速度 | 稳定性 | 需要网络 |
|--------|-----|------|------|------|--------|----------|
| AKShare | ✅ | ❌ | ❌ | 快 | 高 | 是 |
| BaoStock | ✅ | ❌ | ❌ | 中 | 高 | 是 |
| YFinance | ❌ | ✅ | ✅ | 慢 | 中 | 是 |
| 模拟数据 | ✅ | ✅ | ✅ | 极快 | 100% | 否 |

## ⚠️ 注意事项

1. **不安装新数据源**：系统继续使用 YFinance + 模拟数据，功能完全正常
2. **安装AKShare**：A股数据质量大幅提升，获取真实历史数据
3. **安装BaoStock**：作为AKShare的备用数据源

## 🚀 立即测试

无论是否安装新数据源，系统都可以正常工作：

```bash
# 刷新浏览器
http://localhost:3000

# 输入股票代码
AAPL 或 600519.SS

# 点击回测
```

系统会自动选择最佳数据源并显示数据来源！
