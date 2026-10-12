import { useEffect, useState } from 'react'
import './StrategyList.css'

interface Strategy {
  id: string
  name: string
  description: string
  parameters: Record<string, any>
}

interface StrategyListProps {
  selectedStrategy: string | null
  onSelectStrategy: (strategyId: string) => void
}

export default function StrategyList({ selectedStrategy, onSelectStrategy }: StrategyListProps) {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStrategies()
  }, [])

  // 加载完成后默认选中第一个策略
  useEffect(() => {
    if (strategies.length > 0 && !selectedStrategy) {
      onSelectStrategy(strategies[0].id)
    }
  }, [strategies])

  const fetchStrategies = async () => {
    try {
      const response = await fetch('/api/strategies/')
      const data = await response.json()
      setStrategies(data)
    } catch (error) {
      console.error('获取策略列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">加载中...</div>
  }

  return (
    <div className="strategy-list">
      {strategies.map(strategy => (
        <div
          key={strategy.id}
          className={`strategy-card ${selectedStrategy === strategy.id ? 'selected' : ''}`}
          onClick={() => onSelectStrategy(strategy.id)}
        >
          <h3 className="strategy-name">{strategy.name}</h3>
          <p className="strategy-description">{strategy.description}</p>
          <div className="strategy-params">
            {Object.entries(strategy.parameters).map(([key, value]) => (
              <span key={key} className="param-tag">
                {key}: {String(value.default)}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
