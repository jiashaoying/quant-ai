import { TrendingUp, TrendingDown, DollarSign, Activity, Database, AlertTriangle } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
import './BacktestResult.css'

interface BacktestResultProps {
  result: any
}

export default function BacktestResult({ result }: BacktestResultProps) {
  const { metrics, trades, equity_curve, strategy, symbol, data_source, is_mock } = result

  // 数据源名称映射
  const dataSourceNames: Record<string, string> = {
    'auto': '🤖 自动选择',
    'tencent': '🐧 腾讯财经',
    'yfinance': '🌍 YFinance',
    'akshare': '📊 AKShare',
    'baostock': '📈 BaoStock',
    'mock': '🎲 模拟数据',
  }

  // 格式化数字
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num)
  }

  // 格式化百分比
  const formatPercent = (num: number) => {
    return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`
  }

  // 准备资金曲线数据
  const equityData = equity_curve.map((item: any) => ({
    date: new Date(item.Date).toLocaleDateString(),
    equity: item.equity,
    price: item.Close,
    signal: item.signal
  }))

  return (
    <div className="backtest-result">
      {is_mock && (
        <div className="mock-data-banner">
          <AlertTriangle size={18} />
          <span>当前使用模拟数据，回测结果仅供参考。请检查网络连接或切换数据源以获取真实数据。</span>
        </div>
      )}
      <div className="result-header">
        <div className="result-header-top">
          <h3>{strategy.name} - {symbol}</h3>
          {data_source && (
            <span className="data-source-tag">
              <Database size={14} />
              {dataSourceNames[data_source] || data_source}
            </span>
          )}
        </div>
        <div className="result-summary">
          <div className={`summary-card ${metrics.total_return >= 0 ? 'positive' : 'negative'}`}>
            <TrendingUp size={24} />
            <div className="summary-content">
              <span className="summary-label">总收益率</span>
              <span className="summary-value">{formatPercent(metrics.total_return)}</span>
            </div>
          </div>
          
          <div className="summary-card">
            <DollarSign size={24} />
            <div className="summary-content">
              <span className="summary-label">最终资金</span>
              <span className="summary-value">¥{formatNumber(metrics.final_value)}</span>
            </div>
          </div>
          
          <div className="summary-card">
            <Activity size={24} />
            <div className="summary-content">
              <span className="summary-label">夏普比率</span>
              <span className="summary-value">{metrics.sharpe_ratio}</span>
            </div>
          </div>
          
          <div className={`summary-card ${metrics.max_drawdown < 0 ? 'warning' : ''}`}>
            <TrendingDown size={24} />
            <div className="summary-content">
              <span className="summary-label">最大回撤</span>
              <span className="summary-value">{formatPercent(metrics.max_drawdown)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-item">
          <span className="metric-label">年化收益率</span>
          <span className="metric-value">{formatPercent(metrics.annual_return)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">胜率</span>
          <span className="metric-value">{formatPercent(metrics.win_rate)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">总交易次数</span>
          <span className="metric-value">{metrics.total_trades}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">盈利次数</span>
          <span className="metric-value positive">{metrics.winning_trades}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">亏损次数</span>
          <span className="metric-value negative">{metrics.losing_trades}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">盈亏比</span>
          <span className="metric-value">{metrics.profit_loss_ratio}</span>
        </div>
      </div>

      <div className="charts-section">
        <div className="chart-container">
          <h4>资金曲线</h4>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={equityData}>
              <defs>
                <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#667eea" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#667eea" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" stroke="#999" fontSize={12} />
              <YAxis stroke="#999" fontSize={12} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e0e0e0',
                  borderRadius: '8px'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="equity" 
                stroke="#667eea" 
                fillOpacity={1} 
                fill="url(#colorEquity)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h4>股价走势</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={equityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" stroke="#999" fontSize={12} />
              <YAxis stroke="#999" fontSize={12} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e0e0e0',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="price" 
                stroke="#764ba2" 
                strokeWidth={2}
                dot={false}
                name="股价"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {trades.length > 0 && (
        <div className="trades-section">
          <h4>交易记录 ({trades.length} 笔)</h4>
          <div className="trades-table">
            <table>
              <thead>
                <tr>
                  <th>买入日期</th>
                  <th>卖出日期</th>
                  <th>买入价</th>
                  <th>卖出价</th>
                  <th>盈亏</th>
                  <th>收益率</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((trade: any, index: number) => (
                  <tr key={index}>
                    <td>{new Date(trade.entry_date).toLocaleDateString()}</td>
                    <td>{new Date(trade.exit_date).toLocaleDateString()}</td>
                    <td>¥{formatNumber(trade.entry_price)}</td>
                    <td>¥{formatNumber(trade.exit_price)}</td>
                    <td className={trade.pnl >= 0 ? 'positive' : 'negative'}>
                      ¥{formatNumber(trade.pnl)}
                    </td>
                    <td className={trade.pnl_pct >= 0 ? 'positive' : 'negative'}>
                      {formatPercent(trade.pnl_pct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
