# 切块预览模块优化方案

## 一、当前系统分析

### 1.1 现有架构

```
上传文件 → 解析(PDF/PPT/TXT) → 清洗 → 切分(RecursiveCharacterTextSplitter) → 向量化 → 存储
```

### 1.2 核心代码

**解析器** (`app/rag/parsers.py`)：
- PDF：使用 `pypdf` 逐页提取纯文本
- PPT：使用 `python-pptx` 提取文本
- TXT/MD：直接读取文件

**切分器** (`ingestion/chunker.py`)：
- 使用 LangChain 的 `RecursiveCharacterTextSplitter`
- 分隔符优先级：`\n\n` → `\n` → `。` → `!` → `?` → `;` → ` ` → ``
- 支持父子分块（父块存上下文，子块做检索）

### 1.3 现有问题

| 问题 | 影响 | 严重程度 |
|------|------|----------|
| **PDF 解析粗糙** | 使用 `pypdf` 仅提取纯文本，丢失表格、图片、版面结构 | 🔴 高 |
| **扫描件不支持** | 注释写了"扫描件需 OCR"，但未实现 | 🔴 高 |
| **表格处理缺失** | 表格被拆成零散文本，语义丢失 | 🔴 高 |
| **图片忽略** | 图片类型直接跳过，不做 OCR | 🟡 中 |
| **版面信息丢失** | 不区分标题、正文、页眉页脚 | 🟡 中 |
| **切块预览缺失** | 用户无法在上传前预览切块效果 | 🟡 中 |
| **DOCX 支持弱** | 使用 `docx2txt`，丢失格式信息 | 🟢 低 |

---

## 二、开源方案对比

### 2.1 MinerU（上海人工智能实验室）

**项目信息**
- GitHub：[opendatalab/MinerU](https://github.com/opendatalab/MinerU)
- Stars：25K+
- 许可证：AGPL-3.0

**核心能力**

| 功能 | 说明 |
|------|------|
| 版面分析 | 识别标题、正文、页眉页脚、脚注、页码 |
| 表格识别 | 保留表格结构，输出 Markdown 表格 |
| OCR 支持 | 扫描件、图片 PDF 自动 OCR（PaddleOCR） |
| 公式识别 | 数学公式转 LaTeX |
| 多列布局 | 正确处理多栏排版 |
| 输出格式 | Markdown、JSON |

**技术栈**
- PyTorch（深度学习框架）
- PaddleOCR（OCR 引擎）
- LayoutLMv3（版面分析模型）
- TableRec（表格识别模型）

**安装方式**
```bash
# 基础安装
pip install magic-pdf[full]

# Docker
docker pull opendatalab/mineru
```

**使用示例**
```python
from magic_pdf.data.data_reader_writer import FileBasedDataWriter
from magic_pdf.pipe.UNIPipe import UNIPipe

# 解析 PDF
pipe = UNIPipe(pdf_path, [], [], is_debug=False)
pipe.pipe_classify()
pipe.pipe_analyze()
pipe.pipe_parse()

# 获取 Markdown
md_content = pipe.pipe_mk_markdown()

# 获取结构化数据
content_list = pipe.pipe_mk_content_list()
```

**优势**
- 表格识别精度最高（~95%）
- 公式识别能力强（学术文档）
- 版面分析最详细
- 社区活跃，更新频繁

**劣势**
- 依赖较重（PyTorch + PaddleOCR，约 2GB）
- 仅支持 PDF，不支持 DOCX/PPTX
- 部署需要 GPU 加速（CPU 很慢，约 5s/页）
- 配置相对复杂
- AGPL 许可证（商用需注意）

---

### 2.2 Docling（IBM）

**项目信息**
- GitHub：[docling-project/docling](https://github.com/docling-project/docling)
- Stars：12K+
- 许可证：MIT

**核心能力**

| 功能 | 说明 |
|------|------|
| 多格式支持 | PDF、DOCX、PPTX、图片、HTML |
| 表格识别 | TableFormer 模型，高精度表格提取 |
| OCR 支持 | 内置 OCR 引擎 |
| 元数据提取 | 标题、作者、日期等 |
| 结构化输出 | Markdown、JSON、HTML、Doctags |
| 版面分析 | 识别标题、段落、列表、表格 |

**技术栈**
- PyTorch
- LayoutLMv3（版面分析）
- TableFormer（表格识别）
- EasyOCR（OCR 引擎）

**安装方式**
```bash
# 基础安装
pip install docling

# Docker
docker pull ghcr.io/docling-project/docling
```

**使用示例**
```python
from docling.document_converter import DocumentConverter

# 解析文档
converter = DocumentConverter()
result = converter.convert("document.pdf")

# 获取 Markdown
md_content = result.document.export_to_markdown()

# 获取表格
tables = result.document.tables
for table in tables:
    df = table.export_to_dataframe()

# 获取结构化数据
doc_json = result.document.export_to_dict()
```

**优势**
- 多格式支持（PDF/DOCX/PPTX/图片/HTML）
- 部署简单，依赖较轻（约 1GB）
- API 设计友好，易于集成
- 表格识别效果好（~90%）
- MIT 许可证（商用友好）
- 有官方 Docker 镜像

**劣势**
- 公式识别不如 MinerU
- 某些复杂版面效果略逊
- CPU 推理速度一般（约 2s/页）

---

### 2.3 对比总结

| 维度 | MinerU | Docling | 当前系统 |
|------|--------|---------|----------|
| **PDF 解析** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **表格识别** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| **OCR 支持** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| **版面分析** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| **公式识别** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ |
| **多列布局** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| **DOCX 支持** | ❌ | ⭐⭐⭐⭐ | ⭐⭐ |
| **PPTX 支持** | ❌ | ⭐⭐⭐⭐ | ⭐⭐ |
| **图片支持** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| **部署难度** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **依赖大小** | ~2GB | ~1GB | ~100MB |
| **CPU 速度** | ~5s/页 | ~2s/页 | ~0.1s/页 |
| **GPU 速度** | ~0.5s/页 | ~1s/页 | N/A |
| **许可证** | AGPL-3.0 | MIT | - |

---

## 三、推荐方案

### 3.1 方案对比

| 方案 | 适用场景 | 优势 | 劣势 |
|------|----------|------|------|
| **方案 A：仅 Docling** | 多格式文档、无 GPU、快速集成 | 简单、多格式、MIT | PDF 效果略逊 |
| **方案 B：仅 MinerU** | PDF 为主、有 GPU、追求质量 | PDF 最强、公式识别 | 依赖重、仅 PDF |
| **方案 C：混合方案** | 多格式 + 高质量 PDF | 灵活、最佳效果 | 复杂度高 |

### 3.2 推荐：方案 A（Docling）

**理由**
1. **多格式支持**：PDF/DOCX/PPTX/图片/HTML 一站式解决
2. **部署简单**：依赖较轻，无需 GPU
3. **MIT 许可证**：商用友好
4. **API 友好**：易于集成到现有系统
5. **表格识别好**：满足大多数场景

**适用场景**
- 企业文档（PDF/DOCX/PPTX 混合）
- 无 GPU 资源
- 快速上线

---

## 四、架构设计

### 4.1 解析器抽象层

```python
# app/rag/parsers_v2.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ParseResult:
    """解析结果"""
    markdown: str                    # Markdown 格式内容
    plain_text: str                  # 纯文本内容
    tables: List[dict]               # 表格列表
    images: List[dict]               # 图片列表
    metadata: dict                   # 元数据（标题、作者等）
    pages: List[str]                 # 按页内容
    has_tables: bool                 # 是否包含表格
    has_images: bool                 # 是否包含图片

class BaseParser(ABC):
    """解析器基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        """解析文档"""
        pass
    
    @abstractmethod
    def supported_types(self) -> List[str]:
        """支持的文件类型"""
        pass

class DoclingParser(BaseParser):
    """Docling 解析器"""
    
    def parse(self, file_path: str) -> ParseResult:
        from docling.document_converter import DocumentConverter
        
        converter = DocumentConverter()
        result = converter.convert(file_path)
        doc = result.document
        
        # 提取表格
        tables = []
        for table in doc.tables:
            tables.append({
                "content": table.export_to_markdown(),
                "dataframe": table.export_to_dataframe().to_dict(),
            })
        
        # 提取图片
        images = []
        for img in doc.pictures:
            images.append({
                "caption": img.caption if hasattr(img, 'caption') else None,
                "bbox": img.bbox if hasattr(img, 'bbox') else None,
            })
        
        return ParseResult(
            markdown=doc.export_to_markdown(),
            plain_text=doc.export_to_markdown(),  # 简化处理
            tables=tables,
            images=images,
            metadata=doc.metadata.__dict__ if hasattr(doc, 'metadata') else {},
            pages=[],  # Docling 不直接支持按页输出
            has_tables=len(tables) > 0,
            has_images=len(images) > 0,
        )
    
    def supported_types(self) -> List[str]:
        return ["pdf", "docx", "pptx", "png", "jpg", "jpeg", "html"]

class MinerUParser(BaseParser):
    """MinerU 解析器（可选，需要 GPU）"""
    
    def parse(self, file_path: str) -> ParseResult:
        from magic_pdf.pipe.UNIPipe import UNIPipe
        
        pipe = UNIPipe(file_path, [], [], is_debug=False)
        pipe.pipe_classify()
        pipe.pipe_analyze()
        pipe.pipe_parse()
        
        md_content = pipe.pipe_mk_markdown()
        content_list = pipe.pipe_mk_content_list()
        
        # 提取表格
        tables = [item for item in content_list if item.get("type") == "table"]
        
        return ParseResult(
            markdown=md_content,
            plain_text=md_content,
            tables=tables,
            images=[],
            metadata={},
            pages=[],
            has_tables=len(tables) > 0,
            has_images=False,
        )
    
    def supported_types(self) -> List[str]:
        return ["pdf"]

class ParserFactory:
    """解析器工厂"""
    
    _parsers = {
        "docling": DoclingParser,
        "mineru": MinerUParser,
    }
    
    @classmethod
    def get_parser(cls, engine: str = "auto", file_type: str = "") -> BaseParser:
        """获取解析器"""
        if engine == "auto":
            # 自动选择：PDF 优先 MinerU（如有），其他用 Docling
            if file_type == "pdf":
                try:
                    return cls._parsers["mineru"]()
                except ImportError:
                    return cls._parsers["docling"]()
            return cls._parsers["docling"]()
        
        if engine not in cls._parsers:
            raise ValueError(f"不支持的解析引擎: {engine}")
        
        return cls._parsers[engine]()
```

### 4.2 切块预览 API

```python
# app/api/preview.py

from fastapi import APIRouter, UploadFile, File, Query
from app.rag.parsers_v2 import ParserFactory

router = APIRouter(prefix="/preview", tags=["预览"])

@router.post("/chunks", summary="预览切块效果")
async def preview_chunks(
    file: UploadFile = File(...),
    chunk_size: int = Query(500, ge=100, le=2000, description="子块大小"),
    chunk_overlap: int = Query(50, ge=0, le=200, description="重叠大小"),
    parent_chunk_size: int = Query(2000, ge=500, le=5000, description="父块大小"),
    parser_engine: str = Query("auto", description="解析引擎：auto/docling/mineru"),
):
    """上传文件后预览切块效果，不实际入库"""
    import tempfile
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # 1. 解析文件
        file_type = file.filename.split(".")[-1].lower()
        parser = ParserFactory.get_parser(parser_engine, file_type)
        result = parser.parse(tmp_path)
        
        # 2. 父子切分
        separators = ["\n\n", "\n", "。", "!", "?", ";", " ", ""]
        
        parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
        )
        parents = parent_splitter.split_text(result.markdown)
        
        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
        )
        
        # 3. 构建预览数据
        preview_data = []
        total_children = 0
        for i, parent_text in enumerate(parents):
            children = child_splitter.split_text(parent_text) or [parent_text]
            total_children += len(children)
            preview_data.append({
                "parent_index": i,
                "parent_content": parent_text[:500] + ("..." if len(parent_text) > 500 else ""),
                "parent_length": len(parent_text),
                "children_count": len(children),
                "children_preview": [
                    {
                        "index": j,
                        "content": c[:200] + ("..." if len(c) > 200 else ""),
                        "length": len(c),
                    }
                    for j, c in enumerate(children[:3])  # 只预览前3个子块
                ],
            })
        
        return {
            "filename": file.filename,
            "file_type": file_type,
            "parser_engine": parser_engine,
            "total_parents": len(parents),
            "total_children": total_children,
            "has_tables": result.has_tables,
            "has_images": result.has_images,
            "tables_count": len(result.tables),
            "markdown_preview": result.markdown[:1000] + ("..." if len(result.markdown) > 1000 else ""),
            "chunks_preview": preview_data[:10],  # 只预览前10个父块
            "settings": {
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "parent_chunk_size": parent_chunk_size,
            },
        }
    
    finally:
        import os
        os.unlink(tmp_path)
```

### 4.3 前端预览组件

```vue
<!-- frontend/src/views/admin/ChunkPreview.vue -->

<template>
  <div class="chunk-preview">
    <!-- 上传区域 -->
    <el-card class="upload-card">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :before-upload="beforeUpload"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF / DOCX / PPTX / 图片</div>
        </template>
      </el-upload>
    </el-card>

    <!-- 参数设置 -->
    <el-card class="settings-card" v-if="file">
      <template #header>
        <span>切块参数</span>
      </template>
      <el-form :model="settings" label-width="120px">
        <el-form-item label="子块大小">
          <el-slider v-model="settings.chunk_size" :min="100" :max="2000" :step="50" show-input />
        </el-form-item>
        <el-form-item label="重叠大小">
          <el-slider v-model="settings.chunkOverlap" :min="0" :max="200" :step="10" show-input />
        </el-form-item>
        <el-form-item label="父块大小">
          <el-slider v-model="settings.parentChunkSize" :min="500" :max="5000" :step="100" show-input />
        </el-form-item>
        <el-form-item label="解析引擎">
          <el-select v-model="settings.parserEngine">
            <el-option label="自动" value="auto" />
            <el-option label="Docling" value="docling" />
            <el-option label="MinerU" value="mineru" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="previewChunks" :loading="loading">
            预览切块
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 预览结果 -->
    <el-card class="result-card" v-if="previewResult">
      <template #header>
        <div class="result-header">
          <span>切块预览</span>
          <el-tag type="info">父块: {{ previewResult.total_parents }}</el-tag>
          <el-tag type="success">子块: {{ previewResult.total_children }}</el-tag>
          <el-tag v-if="previewResult.has_tables" type="warning">
            表格: {{ previewResult.tables_count }}
          </el-tag>
        </div>
      </template>

      <!-- Markdown 预览 -->
      <el-collapse>
        <el-collapse-item title="Markdown 预览" name="markdown">
          <div class="markdown-preview">{{ previewResult.markdown_preview }}</div>
        </el-collapse-item>
      </el-collapse>

      <!-- 切块列表 -->
      <div class="chunks-list">
        <div v-for="chunk in previewResult.chunks_preview" :key="chunk.parent_index" class="chunk-item">
          <div class="chunk-header">
            <el-tag>父块 #{{ chunk.parent_index }}</el-tag>
            <span class="chunk-length">{{ chunk.parent_length }} 字符</span>
            <span class="children-count">{{ chunk.children_count }} 个子块</span>
          </div>
          <div class="chunk-content">{{ chunk.parent_content }}</div>
          <div class="children-list" v-if="chunk.children_preview.length">
            <div v-for="child in chunk.children_preview" :key="child.index" class="child-item">
              <el-tag size="small" type="info">子块 {{ child.index }}</el-tag>
              <span class="child-length">{{ child.length }} 字符</span>
              <div class="child-content">{{ child.content }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import http from '@/api'

const file = ref<File | null>(null)
const loading = ref(false)
const previewResult = ref<any>(null)

const settings = reactive({
  chunkSize: 500,
  chunkOverlap: 50,
  parentChunkSize: 2000,
  parserEngine: 'auto',
})

const handleFileChange = (uploadFile: any) => {
  file.value = uploadFile.raw
}

const beforeUpload = (rawFile: File) => {
  const allowedTypes = ['pdf', 'docx', 'pptx', 'png', 'jpg', 'jpeg']
  const ext = rawFile.name.split('.').pop()?.toLowerCase()
  if (!ext || !allowedTypes.includes(ext)) {
    ElMessage.error('不支持的文件格式')
    return false
  }
  return true
}

const previewChunks = async () => {
  if (!file.value) {
    ElMessage.warning('请先上传文件')
    return
  }

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file.value)

    const response = await http.post('/preview/chunks', formData, {
      params: {
        chunk_size: settings.chunkSize,
        chunk_overlap: settings.chunkOverlap,
        parent_chunk_size: settings.parentChunkSize,
        parser_engine: settings.parserEngine,
      },
    })

    previewResult.value = response.data
    ElMessage.success('预览生成成功')
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error('预览生成失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.chunk-preview {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.upload-card {
  margin-bottom: 0;
}
.settings-card {
  margin-bottom: 0;
}
.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.markdown-preview {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  white-space: pre-wrap;
  font-family: monospace;
  max-height: 300px;
  overflow-y: auto;
}
.chunks-list {
  margin-top: 16px;
}
.chunk-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
.chunk-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.chunk-length, .children-count {
  color: #909399;
  font-size: 12px;
}
.chunk-content {
  background: #f0f9ff;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 8px;
}
.children-list {
  padding-left: 20px;
}
.child-item {
  border-left: 2px solid #409eff;
  padding-left: 12px;
  margin-bottom: 8px;
}
.child-length {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}
.child-content {
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  margin-top: 4px;
  font-size: 13px;
}
</style>
```

---

## 五、实施计划

### 5.1 阶段一：基础集成（1-2天）

**目标**：集成 Docling，替换现有 PDF 解析

**任务**
1. 添加 Docling 依赖到 `pyproject.toml`
2. 实现 `DoclingParser` 类
3. 修改 `app/rag/parsers.py`，使用 Docling 解析 PDF
4. 测试解析效果

**改动文件**
- `pyproject.toml`
- `app/rag/parsers.py`
- `Dockerfile`

### 5.2 阶段二：切块预览（1-2天）

**目标**：实现切块预览功能

**任务**
1. 实现解析器抽象层 `parsers_v2.py`
2. 实现预览 API `app/api/preview.py`
3. 实现前端预览组件
4. 注册路由

**改动文件**
- `app/rag/parsers_v2.py`
- `app/api/preview.py`
- `app/main.py`
- `frontend/src/views/admin/ChunkPreview.vue`
- `frontend/src/router/index.ts`

### 5.3 阶段三：高级功能（2-3天）

**目标**：表格单独处理、图片 OCR

**任务**
1. 表格提取并单独存储
2. 图片 OCR 文本提取
3. 解析结果缓存
4. 解析质量评估

### 5.4 阶段四：可选优化（按需）

**目标**：集成 MinerU（有 GPU 时）

**任务**
1. 实现 `MinerUParser` 类
2. 配置 GPU 环境
3. 性能调优

---

## 六、部署说明

### 6.1 依赖变更

```toml
# pyproject.toml 新增
"docling>=1.0.0",
```

### 6.2 Docker 变更

```dockerfile
# Dockerfile 新增
RUN pip install docling
```

### 6.3 环境变量

```bash
# .env 新增
PARSER_ENGINE=auto  # auto/docling/mineru
```

---

## 七、风险评估

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| Docling 依赖冲突 | 安装失败 | 使用独立虚拟环境 |
| 解析速度变慢 | 用户体验下降 | 异步解析 + 进度提示 |
| 内存占用增加 | OOM | 限制并发数 + 分页处理 |
| 表格识别不准 | 数据质量下降 | 人工校验 + 修正功能 |

---

## 八、参考资料

1. [MinerU GitHub](https://github.com/opendatalab/MinerU)
2. [Docling GitHub](https://github.com/docling-project/docling)
3. [6 大 RAG PDF 文档处理工具对比](https://cloud.tencent.cn/developer/article/2501272)
4. [MinerU 技术原理深度解析](https://blog.csdn.net/luomao2012/article/details/147661442)
5. [Docling Technical Report](https://arxiv.org/html/2408.09869v4)
