---
kind: external_dependency
name: 腾讯财经 K 线接口
slug: 腾讯财经-k-线接口
category: external_dependency
scope:
    - '**'
---

A 股/港股优先数据源，直接 HTTP GET https://web.ifzq.gtimg.cn/appstock/app/fqkline/get，参数格式 param={market}{code},day,{start},{end},{count},qfq，返回 data.code==0 且 data.data.{sh|sz|bj|hk}{code}.qfqday/day 为 OHLCV 数组。User-Agent 和 Referer 必须携带，否则可能被拒绝。代码转换规则：600519.SS→sh600519、000858.SZ→sz000858、00700.HK→hk00700、北交所 BJ→bj{code}。