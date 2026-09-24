import { Typography } from 'antd'

export function ProductBrand({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`product-brand${compact ? ' product-brand-compact' : ''}`}>
      <img
        src="/wafer-intelligence.svg"
        className="product-brand-icon"
        alt=""
        aria-hidden="true"
      />
      {!compact && (
        <div className="product-brand-copy">
          <Typography.Text strong>Wafer Intelligence</Typography.Text>
          <Typography.Text type="secondary" className="product-brand-subtitle">
            晶圆智能分析平台
          </Typography.Text>
        </div>
      )}
    </div>
  )
}
