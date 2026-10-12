import { useState } from 'react'
import { TrendingUp, BarChart3, Settings, Play } from 'lucide-react'
import StrategyList from './components/StrategyList'
import BacktestForm from './components/BacktestForm'
import BacktestResult from './components/BacktestResult'
import './App.css'

function App() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null)
  const [backtestResult, setBacktestResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleBacktest = async (params: any) => {
    setLoading(true)
    try {
      const response = await fetch('/api/backtest/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      })
      
      if (!response.ok) {
        throw new Error('回测失败')
      }
      
      const result = await response.json()
      setBacktestResult(result)
    } catch (error) {
      console.error('回测错误:', error)
      alert('回测失败，请检查参数')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <TrendingUp size={32} className="logo-icon" />
            <h1>量化策略查看系统</h1>
          </div>
          <div className="header-stats">
            <div className="stat-item">
              <BarChart3 size={20} />
              <span>4 个策略</span>
            </div>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="content-grid">
          <aside className="sidebar">
            <div className="sidebar-section">
              <h2 className="section-title">
                <Settings size={20} />
                可用策略
              </h2>
              <StrategyList 
                selectedStrategy={selectedStrategy}
                onSelectStrategy={setSelectedStrategy}
              />
            </div>
          </aside>

          <div className="content-area">
            <section className="backtest-section">
              <h2 className="section-title">
                <Play size={20} />
                策略回测
              </h2>
              <BacktestForm 
                selectedStrategy={selectedStrategy}
                onSubmit={handleBacktest}
                loading={loading}
              />
            </section>

            {backtestResult && (
              <section className="result-section">
                <h2 className="section-title">
                  <BarChart3 size={20} />
                  {backtestResult.is_mock ? '回测结果（模拟数据）' : '回测结果'}
                </h2>
                <BacktestResult result={backtestResult} />
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
