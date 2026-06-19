# Data Master 前后端结构需求文档

版本：v1.0  
对应原型：`output/data-master-ui-image2.html`  
更新时间：2026-06-10

## 1. 技术边界

本文描述 Data Master 从静态原型落地为前后端系统时的结构需求、模块划分、接口职责和数据模型建议。

推荐实现形态：

- 前端：Vue 3 + TypeScript + Naive UI / Soybean Admin。
- 后端：Java Spring Boot / Node.js NestJS / Python FastAPI 均可，需提供统一 REST API。
- 数据库：PostgreSQL / MySQL。
- 文件存储：本地对象存储目录、MinIO 或云对象存储。
- 异步任务：上传识别、DQ、入库建议走任务队列。

## 2. 前端结构需求

### 2.1 路由结构

```text
/login
/calendar
/calendar/:date
/upload
/upload/result/:batchId
/monthly
/history
/metadata
/metadata/:tableId
/metadata/wizard
/users
/users/create
/users/:userId/edit
/organization
/settings
/403
/404
/500
```

路由要求：

- 登录页使用 blank layout。
- 业务页面使用 admin layout。
- 详情页、表单页隐藏在菜单外，但需要保持侧边栏 activeMenu。
- 路由 meta 需要声明权限角色。

### 2.2 前端目录建议

```text
src/
  api/
    auth.ts
    calendar.ts
    upload.ts
    metadata.ts
    history.ts
    monthly.ts
    organization.ts
    users.ts
    settings.ts
  layouts/
    BlankLayout.vue
    AdminLayout.vue
  pages/
    login/
    calendar/
    upload/
    monthly/
    history/
    metadata/
    users/
    organization/
    settings/
    error/
  components/
    DataTable/
    UploadBatch/
    TodoModal/
    ConfirmDialog/
    FieldEditModal/
    PageState/
  stores/
    auth.ts
    route.ts
    upload.ts
    metadata.ts
    pageState.ts
  types/
    auth.ts
    upload.ts
    metadata.ts
    organization.ts
    common.ts
```

### 2.3 通用前端组件

| 组件 | 说明 |
|---|---|
| ConfirmDialog | 删除、替换、取消批次、覆盖/追加等确认 |
| TodoModal | 上传异常待办处理 |
| FieldEditModal | 元数据字段新增/编辑 |
| UploadBatchPanel | 上传区域、文件列表、轮询状态 |
| DataTable | 统一表格包装，支持 loading、empty、error |
| PageSkeleton | 页面骨架屏 |
| ErrorResult | 403/404/500 和接口异常降级 |

### 2.4 前端状态管理

上传状态需要可恢复。

```ts
interface UploadState {
  batchId?: string;
  businessDate?: string;
  tableName?: string;
  replaceFileId?: string;
  files: UploadFileItem[];
  mode: 'normal' | 'prefill' | 'replace';
  polling: boolean;
}
```

要求：

- 上传页刷新后根据 `batch_id` 恢复状态。
- URL query 支持 `date`、`table`、`replace_file_id`。
- 轮询失败时展示网络恢复提示。
- 离开上传页时，如果存在未提交批次，需要提示确认。

### 2.5 权限控制

前端权限分两层：

- 菜单级权限：通过路由 meta 控制菜单展示。
- 按钮级权限：通过用户角色控制上传、替换、删除、强制解锁等动作。

按钮权限建议：

| 功能 | admin | editor | viewer |
|---|---|---|---|
| 上传数据 | 是 | 是 | 否 |
| 历史替换 | 是 | 是 | 否 |
| 删除历史文件 | 是 | 否 | 否 |
| 元数据维护 | 是 | 是 | 否 |
| 用户删除 | 是 | 否 | 否 |
| 组织架构上传 | 是 | 否 | 否 |
| 系统设置 | 是 | 否 | 否 |

## 3. 后端模块结构

### 3.1 服务模块

```text
backend/
  auth/
  users/
  calendar/
  upload/
  metadata/
  history/
  monthly/
  organization/
  settings/
  audit/
  storage/
  tasks/
```

### 3.2 模块职责

| 模块 | 职责 |
|---|---|
| auth | 登录、token、当前用户、权限 |
| users | 用户、角色、数据范围 |
| calendar | 日期完成度、日历详情 |
| upload | 文件上传、批次、识别、映射、DQ、提交入库 |
| metadata | 逻辑表、字段、写入策略、编辑锁 |
| history | 历史文件查询、下载、替换、删除 |
| monthly | 月度完成度、重复上传覆盖/追加、解锁 |
| organization | 组织架构 Excel 上传、校验、版本生效 |
| settings | 系统参数、磁盘监控、登录页联系人 |
| audit | 操作审计日志 |
| storage | 文件存储、下载链接、临时文件清理 |
| tasks | 异步任务、轮询状态、失败重试 |

## 4. 数据模型建议

### 4.1 用户与权限

```sql
users(
  id,
  username,
  display_name,
  password_hash,
  role,
  status,
  data_scope_type,
  data_scope_value,
  created_at,
  updated_at,
  deleted_at
)
```

### 4.2 逻辑表

```sql
metadata_tables(
  id,
  table_name,
  display_name,
  write_strategy,
  primary_keys,
  required_frequency,
  description,
  status,
  created_at,
  updated_at
)
```

### 4.3 字段

```sql
metadata_fields(
  id,
  table_id,
  field_name,
  display_name,
  field_type,
  is_primary_key,
  nullable,
  sort_order,
  description,
  created_at,
  updated_at
)
```

### 4.4 元数据编辑锁

```sql
metadata_locks(
  id,
  table_id,
  locked_by,
  locked_at,
  expires_at,
  status
)
```

### 4.5 上传批次

```sql
upload_batches(
  id,
  batch_no,
  business_date,
  mode,
  status,
  created_by,
  created_at,
  submitted_at,
  cancelled_at,
  superseded_by
)
```

`mode` 枚举：

- `normal`
- `prefill`
- `replace`

### 4.6 上传文件

```sql
upload_files(
  id,
  batch_id,
  original_name,
  storage_key,
  file_size,
  table_id,
  table_name,
  business_date,
  replace_file_id,
  version_no,
  status,
  row_count,
  uploaded_by,
  uploaded_at,
  replaced_at,
  deleted_at
)
```

### 4.7 上传待办

```sql
upload_todos(
  id,
  batch_id,
  file_id,
  todo_type,
  severity,
  detail_json,
  action,
  action_payload,
  status,
  handled_by,
  handled_at,
  created_at
)
```

待办 action：

- `map_existing_field`
- `create_field`
- `ignore_column`

`ignore_column` 后端要求：

- 被忽略列不入库。
- 不更新元数据。
- 记录审计日志。
- 其余字段继续 DQ 和入库。

### 4.8 组织架构

组织架构按 Excel 二维表维护，每行一个站点。

```sql
organization_versions(
  id,
  version_no,
  file_id,
  status,
  uploaded_by,
  uploaded_at,
  effective_at
)
```

```sql
organization_sites(
  id,
  version_id,
  region_name,
  city_name,
  site_name,
  site_id,
  is_mixed_delivery,
  main_site_id,
  row_no,
  validation_status,
  validation_message
)
```

字段要求：

| 字段 | 类型 | 必填 | 规则 |
|---|---|---|---|
| region_name | string | 是 | 区域名称 |
| city_name | string | 是 | 城市名称 |
| site_name | string | 是 | 站点名称 |
| site_id | string | 是 | 唯一站点 ID |
| is_mixed_delivery | boolean/string | 是 | Excel 可传 是/否 |
| main_site_id | string | 条件必填 | 混送为是时必填 |

校验规则：

- `site_id` 在同一版本内唯一。
- `is_mixed_delivery=是` 时，`main_site_id` 必填。
- `main_site_id` 必须能匹配同版本或当前有效版本中的站点。
- 区域、城市、站点名称不能为空。
- 校验失败时不允许版本生效。

### 4.9 系统设置

```sql
system_settings(
  key,
  value,
  value_type,
  description,
  updated_by,
  updated_at
)
```

关键配置：

- `upload.max_file_size_mb`
- `upload.batch_timeout_minutes`
- `dq.null_threshold_percent`
- `history.keep_versions`
- `login.admin_contact_name`
- `login.admin_contact_phone`
- `login.admin_contact_email`
- `storage.disk_warning_percent`
- `storage.disk_block_percent`

### 4.10 审计日志

```sql
audit_logs(
  id,
  actor_id,
  action,
  target_type,
  target_id,
  payload_json,
  ip,
  user_agent,
  created_at
)
```

必须记录：

- 登录失败。
- 上传批次提交/取消。
- 待办处理。
- 历史文件替换/删除。
- 元数据新增/修改/删除。
- 强制解锁。
- 用户删除。
- 组织架构上传与生效。

## 5. API 需求

### 5.1 Auth

```http
POST /api/auth/login
GET  /api/auth/me
POST /api/auth/logout
```

### 5.2 Calendar

```http
GET /api/calendar?month=2026-06
GET /api/calendar/{date}
```

日历列表返回：

```json
{
  "date": "2026-06-05",
  "status": "partial",
  "completed": 4,
  "required": 5,
  "is_future": false
}
```

### 5.3 Upload

```http
POST /api/upload/batches
POST /api/upload/batches/{batchId}/files
GET  /api/upload/batches/{batchId}
GET  /api/upload/batches/{batchId}/result
POST /api/upload/batches/{batchId}/submit
POST /api/upload/batches/{batchId}/cancel
POST /api/upload/todos/{todoId}/handle
```

创建批次请求：

```json
{
  "business_date": "2026-06-05",
  "table_name": "order_fact",
  "mode": "replace",
  "replace_file_id": "F20260605003"
}
```

### 5.4 Metadata

```http
GET    /api/metadata/tables
POST   /api/metadata/tables
GET    /api/metadata/tables/{tableId}
PUT    /api/metadata/tables/{tableId}
DELETE /api/metadata/tables/{tableId}
POST   /api/metadata/tables/{tableId}/lock
DELETE /api/metadata/tables/{tableId}/lock
POST   /api/metadata/tables/{tableId}/force-unlock
POST   /api/metadata/tables/{tableId}/fields
PUT    /api/metadata/fields/{fieldId}
DELETE /api/metadata/fields/{fieldId}
```

### 5.5 History

```http
GET    /api/history/files
GET    /api/history/files/{fileId}/download
POST   /api/history/files/{fileId}/replace
DELETE /api/history/files/{fileId}
```

替换接口可以返回上传页所需预填参数：

```json
{
  "business_date": "2026-06-05",
  "table_name": "sales_daily",
  "replace_file_id": "F20260605001"
}
```

### 5.6 Monthly

```http
GET  /api/monthly?month=2026-06
POST /api/monthly/{month}/duplicate-policy
POST /api/monthly/{month}/unlock
```

重复上传策略：

```json
{
  "policy": "cover"
}
```

`policy` 可选：

- `cover`
- `append`

### 5.7 Organization

```http
GET  /api/organization/sites
POST /api/organization/upload
GET  /api/organization/versions/latest
```

组织架构列表返回：

```json
{
  "items": [
    {
      "region_name": "华东区",
      "city_name": "上海",
      "site_name": "上海徐汇站",
      "site_id": "SH-001",
      "is_mixed_delivery": false,
      "main_site_id": null
    }
  ]
}
```

上传接口要求：

- 接收 Excel 文件。
- 校验固定列：区域名称、城市名称、站点名称、站点ID、混送（主站）、主站ID。
- 返回校验结果和最新站点表。

### 5.8 Users

```http
GET    /api/users
POST   /api/users
GET    /api/users/{userId}
PUT    /api/users/{userId}
POST   /api/users/{userId}/reset-password
POST   /api/users/{userId}/toggle-active
DELETE /api/users/{userId}
```

### 5.9 Settings

```http
GET /api/settings
PUT /api/settings
GET /api/settings/disk
```

## 6. 后端处理规则

### 6.1 上传处理

1. 创建批次。
2. 保存文件到 storage。
3. 异步识别表名。
4. 预填模式跳过表名识别。
5. 执行字段映射。
6. 生成 DQ 结果。
7. 有阻塞问题则生成待办。
8. 待办完成后允许提交。
9. 提交时按逻辑表写入策略入库。

写入策略：

- 按日期覆盖。
- 追加写入。
- 全量替换。

### 6.2 替换处理

替换只影响单个文件。

要求：

- 新上传文件必须带 `replace_file_id`。
- 提交成功后旧文件状态变为 `replaced`。
- 新文件继承原业务日期和逻辑表。
- 版本号递增。
- 保留旧文件下载能力，除非被管理员删除。

### 6.3 组织架构处理

组织架构上传不再拆分三级维护。

处理步骤：

1. 读取 Excel。
2. 按固定列解析每行站点。
3. 校验必填、唯一性、主站关联。
4. 写入 `organization_versions` 和 `organization_sites`。
5. 校验通过后更新最新版本。
6. 用户数据范围、日历缺口统计使用最新有效组织版本。

### 6.4 月度重复上传

同月重复上传时，后端必须要求用户选择策略。

- 覆盖：旧批次标记为 `superseded`。
- 追加：新文件合并到现有批次。

策略选择必须记录审计日志。

## 7. 错误码建议

| 错误码 | 说明 |
|---|---|
| AUTH_INVALID_CREDENTIALS | 账号或密码错误 |
| PERMISSION_DENIED | 无权限 |
| UPLOAD_BATCH_NOT_FOUND | 上传批次不存在 |
| UPLOAD_TODO_REQUIRED | 存在未处理待办 |
| FILE_REPLACE_TARGET_NOT_FOUND | 替换目标文件不存在 |
| METADATA_LOCKED | 元数据被其他用户锁定 |
| ORG_REQUIRED_COLUMN_MISSING | 组织架构缺少必填列 |
| ORG_SITE_ID_DUPLICATED | 站点 ID 重复 |
| ORG_MAIN_SITE_INVALID | 主站 ID 不存在 |
| USER_DELETE_SELF_FORBIDDEN | 不允许删除当前登录用户 |
| STORAGE_LIMIT_EXCEEDED | 存储空间不足 |

## 8. 非功能需求

### 8.1 性能

- 日历月视图接口响应小于 500ms。
- 历史文件查询支持分页。
- 上传处理必须异步执行。
- 大文件上传需要支持进度展示。

### 8.2 安全

- 所有接口需鉴权。
- 文件下载使用短期签名 URL 或后端流式鉴权。
- 上传文件需限制类型和大小。
- 删除、替换、强制解锁、用户删除必须审计。

### 8.3 可恢复性

- 上传批次可通过 `batch_id` 恢复。
- 异步任务失败需可重试。
- 前端刷新后能恢复上传页状态。
- 网络断连恢复后继续轮询。

### 8.4 可观测性

- 记录上传处理耗时。
- 记录识别、映射、DQ 各阶段状态。
- 记录任务失败原因。
- 暴露磁盘使用率。

## 9. 联调优先级

### P0

- 登录/当前用户。
- 数据日历与日历详情。
- 上传批次创建、上传、轮询、结果页。
- 待办处理与提交入库。
- 组织架构上传和列表展示。

### P1

- 历史下载、替换、删除。
- 元数据表和字段维护。
- 用户管理。
- 月度定版覆盖/追加。

### P2

- 系统设置。
- 磁盘监控。
- 异常页与错误降级。
- 审计日志查询。

## 10. 开发验收清单

- 前端路由与菜单和原型页面一致。
- 上传预填模式和替换模式能通过 URL 或 store 恢复。
- 组织架构页只保留一个上传按钮和固定 6 列表格。
- 后端组织架构接口按固定 Excel 列解析。
- 阻塞待办未处理时不允许提交入库。
- 替换文件只影响单个 `replace_file_id`。
- 元数据字段通过弹窗编辑，表格只读。
- 删除用户、删除历史文件、强制解锁均有确认和审计。
- 页面 loading、empty、error 状态完整。
- 权限不足时跳转 403。
