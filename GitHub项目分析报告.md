# GitHub 项目拉取与分析报告

## 1. 拉取结果

已将 4 个分支分别克隆到当前文件夹 `C:\Users\xxzx-admin\Desktop\CCF` 下的独立目录中：

| 本地目录 | 仓库 / 分支 | HEAD |
|---|---|---|
| `C:\Users\xxzx-admin\Desktop\CCF\xingmeng-main` | `xingmeng / main` | `40ffd1516435bee8dd6b06e1487d206e89bc2374` |
| `C:\Users\xxzx-admin\Desktop\CCF\xingmeng-d` | `xingmeng / d` | `66d54931d78bd299fa16491da9c2ec2ef362d7fb` |
| `C:\Users\xxzx-admin\Desktop\CCF\xingmeng-ht-yun` | `xingmeng / ht-yun` | `199d1dcb74a2195871cc37bb31a4f5f507f8fa65` |
| `C:\Users\xxzx-admin\Desktop\CCF\Dyslexia-main` | `Dyslexia / main` | `199d1dcb74a2195871cc37bb31a4f5f507f8fa65` |

说明：

- `xingmeng-ht-yun` 和 `Dyslexia-main` 的提交哈希完全一致，说明这两份代码是同一个快照。
- 这 4 个分支最终可以归纳为 3 套不同技术体系的项目。

## 2. 总体结论

| 分支 | 技术体系 | 业务定位 | 完整度判断 |
|---|---|---|---|
| `xingmeng / main` | FastAPI + SQLAlchemy + SQLite + uni-app | 面向儿童筛查、家长、咨询师、管理后台的完整平台 | 结构最完整，业务面最广 |
| `xingmeng / d` | Next.js + Prisma + SQLite | 咨询师工作台 / 门店管理后台 | 功能比较集中，很多页面和接口已实现，部分能力仍是模拟数据 |
| `xingmeng / ht-yun` | Vite + React + Express + JSON DB | 儿童识字训练游戏系统 | 游戏闭环完整，偏本地化、轻量化 |
| `Dyslexia / main` | 与 `xingmeng / ht-yun` 完全相同 | 同上 | 与 `xingmeng / ht-yun` 相同代码 |

## 3. 分支分析

### 3.1 `xingmeng / main`

#### 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic、JWT、bcrypt、Alembic
- 数据库：SQLite
- 前端：uni-app 工作区
- 前端组织：`frontend/apps/child`、`frontend/apps/parent`、`frontend/apps/counselor`、`frontend/apps/admin`
- 公共代码：`frontend/shared`

#### 目录结构

- `backend/app/core`：配置、数据库、鉴权、依赖注入
- `backend/app/models`：ORM 数据模型
- `backend/app/routers`：实际业务路由
- `backend/app/api/v1`：版本化路由和健康检查占位
- `frontend/apps/*`：四端子应用
- `frontend/shared/*`：接口封装、常量、工具方法

#### 核心功能

- 儿童端
  - 趣味化关卡入口
  - 游戏过程数据采集
  - 关卡配置获取
  - 过程 telemetry 上传
- 家长端
  - 儿童档案管理
  - 筛查报告查看
  - 家长问卷补充
  - AI 问答历史查看
  - 咨询预约
- 咨询师端
  - 订单列表查看
  - 排班时间查看
- 管理端
  - 用户管理
  - 咨询师审核
  - 游戏关卡管理
  - 内容管理
  - 订单管理
  - 大屏统计
  - AI 知识上传

#### 主要数据表

- 用户与权限：`users`、`user_parent`、`counselor_profile`、`sys_role`、`sys_permission`、`sys_role_permission`
- 儿童与筛查：`children`、`game_level`、`game_session`、`game_telemetry_log`、`biz_screening_report`
- 家长业务：`biz_parent_questionnaire`、`ai_chat_session`、`ai_chat_message`
- 咨询业务：`counselor_schedule`、`biz_consult_order`、`biz_intervention_plan`
- 平台管理：`content_article`、`sys_audit_log`、`finance_transaction`

#### 已占用接口

实际运行时由 `backend/app/main.py` 挂载的接口前缀主要是：

- `/api/v1/auth`
- `/api/v1/admin/users`
- `/api/v1/admin/games`
- `/api/v1/admin/counselors`
- `/api/v1/admin/articles`
- `/api/v1/admin/ai`
- `/api/v1/admin/orders`
- `/api/v1/admin/dashboard`
- `/api/v1/child`
- `/api/v1/counselor`
- `/api/v1/common`
- `/api/v1/parent`

典型接口示例：

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register/parent`
- `GET /api/v1/auth/me`
- `GET /api/v1/child/level/config`
- `POST /api/v1/child/session/start`
- `PUT /api/v1/child/session/end`
- `POST /api/v1/child/telemetry`
- `GET /api/v1/parent/reports`
- `GET /api/v1/parent/chat/history`
- `GET /api/v1/counselor/orders`
- `GET /api/v1/counselor/schedules`
- `GET /api/v1/admin/users/list`
- `PUT /api/v1/admin/users/{user_id}/status`
- `GET /api/v1/admin/orders/`
- `POST /api/v1/admin/orders/{order_id}/refund`
- `GET /api/v1/admin/dashboard/overview`
- `GET /api/v1/admin/dashboard/trends`
- `GET /api/v1/admin/dashboard/risk-distribution`
- `GET /api/v1/admin/dashboard/screen-data`

#### 需要特别说明的点

- `backend/app/api/router.py` 定义了一个 `api_router`，但当前 `main.py` 没有挂载它，属于未启用/遗留结构。
- `backend/app/api/v1/admin.py`、`child.py`、`counselor.py` 里只有健康检查接口，当前也没有作为主业务路由挂载。
- 数据层同时存在新旧两套实现：`backend/app/database.py` 是 async 写法，`backend/app/core/database.py` 是同步写法，代码里混用了两种风格。
- `dashboard`、`risk-distribution`、`screen-data` 等接口里有明显的 mock 数据，属于演示型实现。
- `parent/chat/history` 只返回历史记录，没有真正的在线大模型问答生成逻辑。

### 3.2 `xingmeng / d`

#### 技术栈

- 前端 / 后端：Next.js 14 App Router
- ORM：Prisma 5
- 数据库：SQLite
- 身份认证：`jose` + Cookie JWT
- 内容解析：`mammoth`、`pdf-parse`
- 样式：CSS Modules
- 其他：`bcryptjs`

#### 目录结构

- `src/app/(auth)`：登录 / 注册页
- `src/app/(dashboard)`：咨询师工作台
- `src/app/api`：所有业务接口
- `src/components`：侧边栏、顶部栏、聊天组件
- `src/lib`：Prisma、鉴权、AI 引擎
- `prisma`：schema 和 seed 脚本
- `scratch`：调试脚本

#### 核心功能

- 咨询师账号登录 / 注册
- 儿童档案管理
- 筛查报告生成与查看
- 订单管理与状态流转
- 干预方案创建与历史追踪
- 知识库文章上传、PDF / Word 解析
- AI 聊天问答
- AI 转人工咨询单
- 通知中心
- 设置页持久化
- 统计汇总与初始化数据

#### 主要数据模型

- `Consultant`
- `ChildProfile`
- `ScreeningData`
- `Order`
- `InterventionPlan`
- `InterventionTemplate`
- `KnowledgeArticle`
- `SystemNotification`

#### 已占用接口

`src/app/api` 中实际占用的接口如下：

- `POST /api/auth/login`
- `POST /api/auth/register`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/profiles`
- `POST /api/profiles`
- `DELETE /api/profiles/{id}`
- `GET /api/screening`
- `POST /api/screening`
- `GET /api/orders`
- `POST /api/orders`
- `PATCH /api/orders/{id}`
- `GET /api/interventions`
- `POST /api/interventions`
- `GET /api/interventions/templates`
- `GET /api/knowledge`
- `POST /api/knowledge`
- `POST /api/ai/chat`
- `POST /api/ai/transfer`
- `GET /api/notifications`
- `PATCH /api/notifications`
- `POST /api/notifications`
- `GET /api/statistics/summary`
- `GET /api/settings`
- `PUT /api/settings`
- `GET /api/init`

#### 需要特别说明的点

- `screening` 接口会随机生成风险报告，并把结构化报告暂存在 `reportUrl` 字段中，属于模拟实现。
- `ai/chat` 不是接第三方大模型，而是 `ai-engine.js` 里的关键词检索 + 模板化生成。
- `settings` 同时写 JSON 文件和同步数据库中的咨询师信息。
- `knowledge` 支持 PDF / DOCX 解析，说明这个分支已经具备“上传文档自动抽取知识内容”的能力。
- `init` 接口会初始化演示数据，适合本地演示和快速体验。

### 3.3 `xingmeng / ht-yun`

#### 技术栈

- 前端：Vite + React 19 + Framer Motion + Zustand
- 样式：Tailwind CSS v4
- 后端：Express 4
- 存储：`server/db.json` 文件型数据库
- 认证：JWT
- 交互：Web Speech API、`canvas-confetti`

#### 目录结构

- `server`：Express API、JSON 数据存储、路由定义
- `src/components/games`：各类小游戏组件
- `src/components`：星图、等级选择、成就提示、落叶背景
- `src/store`：关卡、奖励、年龄组状态管理
- `src/hooks`：telemetry 采集
- `src/services`：语音播报
- `src/api`：Axios 接口封装

#### 核心功能

- 儿童识字训练游戏大厅
- 按年龄段切换关卡难度
- 关卡地图式选择
- 多种小游戏编排执行
- 游戏过程 telemetry 采集
- 游戏完成后自动解锁后续关卡
- 奖励状态查询与解锁
- 语音引导和读音播报

#### 游戏类型

`server/db.js` 和 `GameSequencer.jsx` 中能看到这些小游戏类型：

- `rhyme_match`
- `syllable_clap`
- `phoneme_hunt`
- `find_odd_char`
- `char_puzzle`
- `word_train`
- `rapid_naming`
- `color_stroop`
- `memory_chain`
- `echo_sentence`
- `sentence_complete`
- `story_quiz`

#### 已占用接口

后端 `server` 实际暴露的接口如下：

- `POST /api/auth/switch`
- `GET /api/games/levels`
- `GET /api/games/config/:levelId`
- `POST /api/games/records/sync`
- `POST /api/games/records/pause`
- `GET /api/rewards/status`
- `POST /api/rewards/unlock`

#### 需要特别说明的点

- 这个项目的状态数据主要保存在 `server/db.json`，不是数据库。
- `db.js` 中预置了儿童、关卡、奖励和 telemetry 结构，属于本地演示/轻量部署方案。
- 前端用 `localStorage` 保存 `child_token`、`age_group`、`pending_telemetry`。
- `useTelemetry` 会在离线时回退到本地缓存，之后再补传。

### 3.4 `Dyslexia / main`

这个分支和 `xingmeng / ht-yun` 完全一致，HEAD 相同，属于同一份代码快照。

#### 结论

- 技术栈相同：Vite + React + Express + JSON DB
- 功能相同：儿童识字训练游戏、telemetry、奖励系统、语音引导
- 接口相同：`/api/auth/switch`、`/api/games/*`、`/api/rewards/*`
- 目录结构相同：`server`、`src/components/games`、`src/store`、`src/hooks`、`src/services`

## 4. 对比总结

| 维度 | `xingmeng / main` | `xingmeng / d` | `xingmeng / ht-yun` / `Dyslexia / main` |
|---|---|---|---|
| 核心场景 | 平台级筛查与管理 | 咨询师工作台 | 儿童识字游戏训练 |
| 前端框架 | uni-app | Next.js | React + Vite |
| 后端框架 | FastAPI | Next.js API Route + Prisma | Express |
| 数据库 / 存储 | SQLite | SQLite | `db.json` |
| 业务重点 | 家长、孩子、咨询师、管理员闭环 | 咨询师订单 / 内容 / 知识 / AI | 游戏、语音、Telemetry、奖励 |
| 实现形态 | 真实接口 + 少量 mock | 真实 CRUD + 模拟 AI / 报告 | 本地游戏引擎 + 文件型后端 |

## 5. 最终结论

如果只从“能做什么”来概括：

- `xingmeng / main` 更像一套完整的儿童阅读障碍筛查平台原型，覆盖家长、咨询师和后台管理。
- `xingmeng / d` 更像一套咨询师工作台，重点在档案、订单、知识库和 AI 辅助。
- `xingmeng / ht-yun` 以及 `Dyslexia / main` 是同一套儿童识字游戏系统，重点在训练、数据采集和解锁奖励。

