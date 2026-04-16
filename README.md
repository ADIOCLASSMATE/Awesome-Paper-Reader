# Awesome Paper Reader

LLM 时代的论文阅读与知识管理工具包，基于 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 构建。

核心流程：**每日论文筛选 → 深度阅读 → 跨论文综合洞察**

```
daily-papers → read-paper → synthesize
```

## 特性

- **每日论文追踪** — 自动抓取 arXiv LLM 相关论文，按相关度分级（MUST_READ / INTERESTING / MARGINAL / SKIP），自动排除 CV / 音频 / 机器人等无关方向
- **LaTeX 源码深度阅读** — 下载 arXiv 论文 LaTeX 源码而非 PDF，逐节递归阅读，输出结构化笔记（问题 / 方法 / 实验 / 洞察 / 关联）
- **本地 PDF 解析** — 基于 [docling](https://github.com/docling-project/docling) 解析本地 PDF，适用于无 LaTeX 源码的论文
- **跨论文综合** — 自动分类论文到研究领域，生成趋势分析、研究空白与机会识别
- **知识库搜索** — 跨所有笔记、综合报告、每日列表进行全文搜索

## 快速开始

### 前置要求

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) 包管理器

### 安装

```bash
git clone https://github.com/ADIOCLASSMATE/Awesome-Paper-Reader.git
cd Awesome-Paper-Reader
uv sync
```

### 使用

在项目目录下启动 Claude Code，通过技能命令操作：

```
/daily-papers          # 抓取并筛选今日 LLM 论文
/read-paper 2604.xxxxx # 深度阅读 arXiv 论文（LaTeX 源码）
/read-pdf /path/to/paper.pdf  # 解析本地 PDF
/synthesize            # 跨论文综合分析
/arxiv <keyword>       # 搜索 arXiv 并下载 LaTeX 源码
/search-knowledge      # 搜索本地知识库
/review                # 对论文/草稿进行对抗性评审
```

## 项目结构

```
.
├── tools/                    # Python 工具脚本
│   ├── arxiv_fetch.py        # arXiv 搜索 + LaTeX 源码下载
│   ├── daily_papers.py       # 每日 LLM 论文抓取与筛选（OpenAlex，免费无需 key）
│   └── pdf_parse.py          # PDF 解析（docling，仅本地文件）
├── templates/                # 模板文件（init 时复制到项目根目录）
│   ├── RESEARCH.md.template  # 研究状态追踪文档
│   ├── LESSON.md.template    # 每次会话的学习记录
│   └── skills.yaml.template  # 技能配置模板
├── skillpacks/               # 技能包配置
│   ├── skill_dictionary.yaml # 技能字典
│   └── presets/              # 预设方案
│       ├── core-only.yaml        # 仅核心技能
│       ├── balanced.yaml         # 均衡配置
│       ├── academic-rigor.yaml   # 学术严谨模式
│       ├── literature-heavy.yaml # 文献综述优先
│       ├── experiment-heavy.yaml # 实验分析优先
│       └── low-dependency.yaml   # 最小依赖
├── CLAUDE.md                 # Claude Code 项目指令
└── pyproject.toml            # Python 项目配置
```

### 数据目录（.gitignore，用户本地生成）

```
knowledge/                   # 知识库
├── inbox/                   # 新论文笔记
├── archive/                 # 已综合分类的笔记
├── syntheses/               # 综合分析报告
└── daily/                   # 每日论文列表

papers/                      # 论文源文件
├── inbox/                   # 未分类论文（LaTeX / PDF）
└── archive/                 # 按领域归档的论文
```

## PDF 政策

- **远程 PDF 禁止下载** — arXiv 论文统一使用 LaTeX 源码（`https://arxiv.org/e-print/ID`），不下载 PDF
- **本地 PDF 允许解析** — 对于无 LaTeX 源码的论文（如扫描版），使用 `/read-pdf` 解析本地文件

## 工具依赖

| 工具 | 依赖 | 说明 |
|------|------|------|
| `arxiv_fetch.py` | Python stdlib | 无额外依赖 |
| `daily_papers.py` | Python stdlib + OpenAlex API | 免费，无需 API key |
| `pdf_parse.py` | docling | `uv sync` 自动安装 |

## License

MIT
