# 03 — Massive Data Infrastructure

## 1. 目标

将 Massive 设为正式实验的默认金融数据源，替代 yfinance 作为主要历史数据路径。

MCP 用于文档和小样本验证；大规模数据通过 Python API、REST、Flat Files 和本地不可变缓存进入实验。

## 2. MCP 配置

检查：

```bash
claude mcp list
```

若不存在：

```bash
claude mcp add --transport http massive https://mcp.massive.com/
```

需要 OAuth 时暂停，提示用户：

```text
/mcp → massive → Authenticate
```

这是允许的人工停止点。

## 3. API key 安全

检查环境变量：

```bash
test -n "$MASSIVE_API_KEY"
```

若不存在，提示用户在启动 Claude Code 的 shell 中安全设置。

禁止：

- 打印或 echo key；
- 写入 Git；
- 写入 YAML；
- 写入普通 `.env`；
- 写入 fixture、日志或报告；
- 放入 prompt。

代码只能从 `MASSIVE_API_KEY` 环境变量读取。

## 4. 权益审计

真实验证：

- daily aggregates；
- minute aggregates；
- ticker reference；
- splits；
- dividends；
- market calendar/status；
- historical news；
- historical trades/quotes；
- 其他资产类别仅在实验需要且套餐支持时验证。

不要假设“10 年”适用于所有端点。

生成：

```text
docs/data/MASSIVE_ENTITLEMENT_AUDIT.md
```

记录：

- endpoint；
- earliest/latest accessible date；
- granularity；
- rate limit；
- pagination；
- sample schema；
- entitlement；
- PIT suitability。

不得记录密钥。

## 5. Provider 架构

实现或适配等价结构：

```text
data/providers/base.py
data/providers/massive_provider.py
data/providers/cache.py
data/providers/normalization.py
data/manifests/
```

要求：

- Massive 为默认 provider；
- yfinance 仅显式 fallback 或数据对照；
- 正式实验默认不使用 yfinance；
- raw 与 normalized 分层；
- 本地缓存不可静默覆盖；
- 保存请求参数、抓取时间、时间范围、checksum、调整模式、provider/version；
- 所有 adapter 和 evaluator 尽可能读取相同快照。

```text
Raw Massive snapshot
        ↓
validated normalized dataset
        ↓
immutable experiment dataset version
```

## 6. 大规模数据传输

MCP 只用于：

- 搜索 endpoint；
- 阅读文档；
- 小样本调用；
- 核验字段。

大规模数据使用：

- Python/REST 分页；
- Flat Files；
- Parquet 或等价列式存储；
-共享缓存。

禁止把多年全量数据通过 Claude 上下文传输，也禁止每个 adapter 各自重新下载。

## 7. 数据质量

至少验证：

- corporate actions；
- adjusted/unadjusted 价格定义；
- ticker changes；
- delisting；
- trading calendar；
- timezone；
- duplicate bars；
- missing bars；
- news `published_at`；
- universe membership 的时间有效性。

生成：

```text
docs/data/MASSIVE_DATA_PROVIDER.md
```

## 8. 通过条件

- MCP 已认证或可用；
- entitlement 已实测；
- provider 单元和集成测试通过；
- 数据可缓存、校验和复现；
- yfinance 不再是默认正式实验路径；
- 小规模 immutable dataset 已生成；
- final-test 数据仍受防火墙控制。
