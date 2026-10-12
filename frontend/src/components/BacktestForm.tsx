import { useState } from 'react'
import { Play, Loader, Database } from 'lucide-react'
import './BacktestForm.css'

interface BacktestFormProps {
  selectedStrategy: string | null
  onSubmit: (params: any) => void
  loading: boolean
}

// 数据源配置
const DATA_SOURCES = [
  { value: 'auto', label: '自动选择', desc: '根据股票市场自动选择最佳数据源', icon: '🤖' },
  { value: 'tencent', label: '腾讯财经', desc: 'A股/港股实时数据，免费快速', icon: '🐧' },
  { value: 'yfinance', label: 'YFinance', desc: '美股/港股/全球市场数据', icon: '🌍' },
  { value: 'akshare', label: 'AKShare', desc: 'A股全面数据，需安装依赖', icon: '📊' },
  { value: 'baostock', label: 'BaoStock', desc: 'A股历史数据，需安装依赖', icon: '📈' },
  { value: 'mock', label: '模拟数据', desc: '无需网络，用于测试演示', icon: '🎲' },
]

export default function BacktestForm({ selectedStrategy, onSubmit, loading }: BacktestFormProps) {
  const [symbol, setSymbol] = useState('600519.SS')
  const [period, setPeriod] = useState('1y')
  const [initialCapital, setInitialCapital] = useState(100000)
  const [dataSource, setDataSource] = useState('auto')
  const [parameters, setParameters] = useState<Record<string, any>>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedStrategy) {
      alert('请先选择一个策略')
      return
    }

    onSubmit({
      strategy_id: selectedStrategy,
      symbol,
      period,
      initial_capital: initialCapital,
      source: dataSource,
      parameters
    })
  }

  const handleParameterChange = (key: string, value: any) => {
    setParameters(prev => ({ ...prev, [key]: value }))
  }

  return (
    <form className="backtest-form" onSubmit={handleSubmit}>
      <div className="form-grid">
        <div className="form-group">
          <label>股票代码</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="例如: 600519.SS, AAPL"
            required
          />
          <small>A股: 600519.SS(上证) / 000858.SZ(深证) | 美股: AAPL</small>
        </div>

        <div className="form-group">
          <label>回测周期</label>
          <select value={period} onChange={(e) => setPeriod(e.target.value)}>
            <option value="1mo">1个月</option>
            <option value="3mo">3个月</option>
            <option value="6mo">6个月</option>
            <option value="1y">1年</option>
            <option value="2y">2年</option>
            <option value="5y">5年</option>
          </select>
        </div>

        <div className="form-group">
          <label>初始资金 (元)</label>
          <input
            type="number"
            value={initialCapital}
            onChange={(e) => setInitialCapital(Number(e.target.value))}
            min="10000"
            step="10000"
            required
          />
        </div>

        <div className="form-group">
          <label>
            <Database size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
            行情数据源
          </label>
          <select 
            value={dataSource} 
            onChange={(e) => setDataSource(e.target.value)}
            className="data-source-select"
          >
            {DATA_SOURCES.map(src => (
              <option key={src.value} value={src.value}>
                {src.icon} {src.label}
              </option>
            ))}
          </select>
          <small className="source-desc">
            {DATA_SOURCES.find(s => s.value === dataSource)?.desc}
          </small>
        </div>
      </div>

      {selectedStrategy && (
        <div className="strategy-params-form">
          <h4>策略参数</h4>
          <div className="params-grid">
            {selectedStrategy === 'ma_cross' && (
              <>
                <div className="param-group">
                  <label>短期均线周期</label>
                  <input
                    type="number"
                    value={parameters.short_window || 5}
                    onChange={(e) => handleParameterChange('short_window', Number(e.target.value))}
                    min="2"
                    max="50"
                  />
                </div>
                <div className="param-group">
                  <label>长期均线周期</label>
                  <input
                    type="number"
                    value={parameters.long_window || 20}
                    onChange={(e) => handleParameterChange('long_window', Number(e.target.value))}
                    min="10"
                    max="200"
                  />
                </div>
              </>
            )}

            {selectedStrategy === 'momentum' && (
              <>
                <div className="param-group">
                  <label>回看周期</label>
                  <input
                    type="number"
                    value={parameters.lookback_period || 20}
                    onChange={(e) => handleParameterChange('lookback_period', Number(e.target.value))}
                    min="5"
                    max="100"
                  />
                </div>
                <div className="param-group">
                  <label>阈值</label>
                  <input
                    type="number"
                    value={parameters.threshold || 0.05}
                    onChange={(e) => handleParameterChange('threshold', Number(e.target.value))}
                    min="0.01"
                    max="0.2"
                    step="0.01"
                  />
                </div>
              </>
            )}

            {selectedStrategy === 'mean_reversion' && (
              <>
                <div className="param-group">
                  <label>窗口周期</label>
                  <input
                    type="number"
                    value={parameters.window || 20}
                    onChange={(e) => handleParameterChange('window', Number(e.target.value))}
                    min="10"
                    max="100"
                  />
                </div>
                <div className="param-group">
                  <label>标准差倍数</label>
                  <input
                    type="number"
                    value={parameters.num_std || 2.0}
                    onChange={(e) => handleParameterChange('num_std', Number(e.target.value))}
                    min="1.0"
                    max="3.0"
                    step="0.1"
                  />
                </div>
              </>
            )}

            {selectedStrategy === 'rsi' && (
              <>
                <div className="param-group">
                  <label>RSI周期</label>
                  <input
                    type="number"
                    value={parameters.period || 14}
                    onChange={(e) => handleParameterChange('period', Number(e.target.value))}
                    min="5"
                    max="30"
                  />
                </div>
                <div className="param-group">
                  <label>超卖线</label>
                  <input
                    type="number"
                    value={parameters.oversold || 30}
                    onChange={(e) => handleParameterChange('oversold', Number(e.target.value))}
                    min="10"
                    max="40"
                  />
                </div>
                <div className="param-group">
                  <label>超买线</label>
                  <input
                    type="number"
                    value={parameters.overbought || 70}
                    onChange={(e) => handleParameterChange('overbought', Number(e.target.value))}
                    min="60"
                    max="90"
                  />
                </div>
              </>
            )}

            {selectedStrategy === 'bollinger_bands' && (
              <>
                <div className="param-group">
                  <label>布林带周期</label>
                  <input
                    type="number"
                    value={parameters.window || 20}
                    onChange={(e) => handleParameterChange('window', Number(e.target.value))}
                    min="10"
                    max="60"
                  />
                </div>
                <div className="param-group">
                  <label>标准差倍数</label>
                  <input
                    type="number"
                    value={parameters.num_std || 2.0}
                    onChange={(e) => handleParameterChange('num_std', Number(e.target.value))}
                    min="1.0"
                    max="3.0"
                    step="0.1"
                  />
                </div>
                <div className="param-group">
                  <label>买入阈值 (%B 下限)</label>
                  <input
                    type="number"
                    value={parameters.buy_threshold || 0.05}
                    onChange={(e) => handleParameterChange('buy_threshold', Number(e.target.value))}
                    min="0"
                    max="0.3"
                    step="0.01"
                  />
                </div>
                <div className="param-group">
                  <label>卖出阈值 (%B 上限)</label>
                  <input
                    type="number"
                    value={parameters.sell_threshold || 0.95}
                    onChange={(e) => handleParameterChange('sell_threshold', Number(e.target.value))}
                    min="0.7"
                    max="1.0"
                    step="0.01"
                  />
                </div>
              </>
            )}

            {selectedStrategy === 'multi_factor' && (
              <>
                <div className="param-group">
                  <label>动量周期</label>
                  <input
                    type="number"
                    value={parameters.momentum_window || 20}
                    onChange={(e) => handleParameterChange('momentum_window', Number(e.target.value))}
                    min="5"
                    max="60"
                  />
                  <small>计算收益率动量的回看天数</small>
                </div>
                <div className="param-group">
                  <label>波动率周期</label>
                  <input
                    type="number"
                    value={parameters.volatility_window || 20}
                    onChange={(e) => handleParameterChange('volatility_window', Number(e.target.value))}
                    min="10"
                    max="60"
                  />
                  <small>计算波动率因子的窗口</small>
                </div>
                <div className="param-group">
                  <label>均线周期</label>
                  <input
                    type="number"
                    value={parameters.ma_window || 20}
                    onChange={(e) => handleParameterChange('ma_window', Number(e.target.value))}
                    min="10"
                    max="60"
                  />
                  <small>均线偏离因子参考均线</small>
                </div>
                <div className="param-group">
                  <label>RSI周期</label>
                  <input
                    type="number"
                    value={parameters.rsi_period || 14}
                    onChange={(e) => handleParameterChange('rsi_period', Number(e.target.value))}
                    min="5"
                    max="30"
                  />
                  <small>RSI因子的计算周期</small>
                </div>
                <div className="param-group">
                  <label>买入阈值</label>
                  <input
                    type="number"
                    value={parameters.buy_score || 0.6}
                    onChange={(e) => handleParameterChange('buy_score', Number(e.target.value))}
                    min="0.5"
                    max="0.9"
                    step="0.05"
                  />
                  <small>综合得分高于此值买入</small>
                </div>
                <div className="param-group">
                  <label>卖出阈值</label>
                  <input
                    type="number"
                    value={parameters.sell_score || 0.4}
                    onChange={(e) => handleParameterChange('sell_score', Number(e.target.value))}
                    min="0.1"
                    max="0.5"
                    step="0.05"
                  />
                  <small>综合得分低于此值卖出</small>
                </div>
              </>
            )}

            {selectedStrategy === 'transformer_predict' && (
              <>
                <div className="param-group">
                  <label>序列长度</label>
                  <input
                    type="number"
                    value={parameters.seq_length || 20}
                    onChange={(e) => handleParameterChange('seq_length', Number(e.target.value))}
                    min="10"
                    max="60"
                  />
                  <small>输入注意力机制的历史天数</small>
                </div>
                <div className="param-group">
                  <label>预测天数</label>
                  <input
                    type="number"
                    value={parameters.pred_horizon || 5}
                    onChange={(e) => handleParameterChange('pred_horizon', Number(e.target.value))}
                    min="1"
                    max="20"
                  />
                  <small>预测未来价格走势的天数</small>
                </div>
                <div className="param-group">
                  <label>注意力头数</label>
                  <input
                    type="number"
                    value={parameters.n_heads || 4}
                    onChange={(e) => handleParameterChange('n_heads', Number(e.target.value))}
                    min="2"
                    max="8"
                  />
                  <small>多头注意力的头数</small>
                </div>
                <div className="param-group">
                  <label>交易阈值</label>
                  <input
                    type="number"
                    value={parameters.threshold || 0.02}
                    onChange={(e) => handleParameterChange('threshold', Number(e.target.value))}
                    min="0.005"
                    max="0.1"
                    step="0.005"
                  />
                  <small>预测分数超过此值产生信号</small>
                </div>
                <div className="param-group">
                  <label>训练窗口</label>
                  <input
                    type="number"
                    value={parameters.lookback_train || 100}
                    onChange={(e) => handleParameterChange('lookback_train', Number(e.target.value))}
                    min="50"
                    max="200"
                  />
                  <small>滚动训练使用的历史天数</small>
                </div>
              </>
            )}

            {selectedStrategy === 'transformer_dl' && (
              <>
                <div className="param-group">
                  <label>序列长度</label>
                  <input
                    type="number"
                    value={parameters.seq_length || 30}
                    onChange={(e) => handleParameterChange('seq_length', Number(e.target.value))}
                    min="10"
                    max="60"
                  />
                  <small>输入序列的历史天数</small>
                </div>
                <div className="param-group">
                  <label>预测天数</label>
                  <input
                    type="number"
                    value={parameters.pred_horizon || 5}
                    onChange={(e) => handleParameterChange('pred_horizon', Number(e.target.value))}
                    min="1"
                    max="20"
                  />
                </div>
                <div className="param-group">
                  <label>模型维度 (d_model)</label>
                  <input
                    type="number"
                    value={parameters.d_model || 64}
                    onChange={(e) => handleParameterChange('d_model', Number(e.target.value))}
                    min="32"
                    max="128"
                    step="32"
                  />
                  <small>Transformer隐藏层维度</small>
                </div>
                <div className="param-group">
                  <label>注意力头数</label>
                  <input
                    type="number"
                    value={parameters.n_heads || 4}
                    onChange={(e) => handleParameterChange('n_heads', Number(e.target.value))}
                    min="2"
                    max="8"
                  />
                </div>
                <div className="param-group">
                  <label>编码器层数</label>
                  <input
                    type="number"
                    value={parameters.n_layers || 2}
                    onChange={(e) => handleParameterChange('n_layers', Number(e.target.value))}
                    min="1"
                    max="4"
                  />
                  <small>Transformer编码器层数</small>
                </div>
                <div className="param-group">
                  <label>训练轮数 (Epochs)</label>
                  <input
                    type="number"
                    value={parameters.epochs || 50}
                    onChange={(e) => handleParameterChange('epochs', Number(e.target.value))}
                    min="10"
                    max="100"
                  />
                  <small>每次训练的迭代次数</small>
                </div>
                <div className="param-group">
                  <label>买入阈值</label>
                  <input
                    type="number"
                    value={parameters.buy_threshold || 0.02}
                    onChange={(e) => handleParameterChange('buy_threshold', Number(e.target.value))}
                    min="0.005"
                    max="0.05"
                    step="0.005"
                  />
                  <small>预测收益率高于此值买入</small>
                </div>
                <div className="param-group">
                  <label>卖出阈值</label>
                  <input
                    type="number"
                    value={parameters.sell_threshold || -0.02}
                    onChange={(e) => handleParameterChange('sell_threshold', Number(e.target.value))}
                    min="-0.05"
                    max="-0.005"
                    step="0.005"
                  />
                  <small>预测收益率低于此值卖出</small>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <button type="submit" className="submit-button" disabled={loading}>
        {loading ? (
          <>
            <Loader className="spinner" size={20} />
            回测中...
          </>
        ) : (
          <>
            <Play size={20} />
            开始回测
          </>
        )}
      </button>
    </form>
  )
}
