const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = '安全优化介绍';
pres.author = '劳动仲裁帮';

// Color palette: Midnight Executive - navy theme for security
const C = {
  navy: "1E2761",
  darkNavy: "141B45",
  ice: "CADCFC",
  white: "FFFFFF",
  lightBg: "F0F4FF",
  accent: "3B82F6",
  accentDark: "2563EB",
  danger: "EF4444",
  warning: "F59E0B",
  success: "22C55E",
  text: "1E293B",
  muted: "64748B",
  cardBg: "FFFFFF",
  divider: "E2E8F0",
};

// Helper: fresh shadow factory
const cardShadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.1 });

// ─────────────────────────────────────────────
// Slide 1: 封面
// ─────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.navy };

  // Left accent bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.18, h: 5.625,
    fill: { color: C.accent }
  });

  // Decorative circle (top right)
  slide.addShape(pres.shapes.OVAL, {
    x: 7.5, y: -1.5, w: 4, h: 4,
    fill: { color: C.accent, transparency: 80 }
  });
  slide.addShape(pres.shapes.OVAL, {
    x: 8.5, y: -0.8, w: 2.5, h: 2.5,
    fill: { color: C.accent, transparency: 70 }
  });

  // Bottom line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 4.8, w: 10, h: 0.04,
    fill: { color: C.accent, transparency: 50 }
  });

  // Title
  slide.addText("安全优化", {
    x: 0.8, y: 1.6, w: 8, h: 1.2,
    fontSize: 52, fontFace: "Arial Black", bold: true,
    color: C.white, margin: 0
  });

  // Subtitle
  slide.addText("大赛安全修复 · 答辩材料", {
    x: 0.8, y: 2.85, w: 8, h: 0.5,
    fontSize: 20, fontFace: "Calibri",
    color: C.ice, margin: 0
  });

  // Tag line
  slide.addText("2026-05-23", {
    x: 0.8, y: 4.2, w: 3, h: 0.4,
    fontSize: 13, color: C.ice, margin: 0
  });
}

// ─────────────────────────────────────────────
// Slide 2: 问题概览
// ─────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  // Title area
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.1,
    fill: { color: C.navy }
  });
  slide.addText("安全风险概览", {
    x: 0.5, y: 0.25, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial Black", bold: true,
    color: C.white, margin: 0
  });

  // Three issue cards
  const issues = [
    {
      icon: "KEY", emoji: "\uD83D\uDD11",
      title: "硬编码 API Key",
      severity: "高危",
      color: C.danger,
      desc: "腾讯云元器 Agent ID / API Key\n明文写死在源代码中"
    },
    {
      icon: "SMS", emoji: "\uD83D\uDCF1",
      title: "固定验证码明文",
      severity: "高危",
      color: C.danger,
      desc: "验证码在开发环境固定返回\n攻击者无需手机即可获取"
    },
    {
      icon: "CORS", emoji: "\uD83C\uDF10",
      title: "CORS 通配符",
      severity: "中危",
      color: C.warning,
      desc: "allow_origins=\"*\" 配合\nallow_credentials=True 不安全"
    }
  ];

  const cardW = 2.8;
  const gap = 0.35;
  const startX = (10 - (cardW * 3 + gap * 2)) / 2;

  issues.forEach((issue, i) => {
    const x = startX + i * (cardW + gap);

    // Card background
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.4, w: cardW, h: 3.4,
      fill: { color: C.cardBg },
      shadow: cardShadow()
    });

    // Top accent stripe
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.4, w: cardW, h: 0.1,
      fill: { color: issue.color }
    });

    // Emoji icon circle
    slide.addShape(pres.shapes.OVAL, {
      x: x + cardW / 2 - 0.4, y: 1.65, w: 0.8, h: 0.8,
      fill: { color: issue.color, transparency: 85 }
    });
    slide.addText(issue.emoji, {
      x: x + cardW / 2 - 0.4, y: 1.68, w: 0.8, h: 0.8,
      fontSize: 26, align: "center", valign: "middle", margin: 0
    });

    // Severity badge
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x + cardW / 2 - 0.45, y: 2.6, w: 0.9, h: 0.32,
      fill: { color: issue.color }, rectRadius: 0.05
    });
    slide.addText(issue.severity, {
      x: x + cardW / 2 - 0.45, y: 2.6, w: 0.9, h: 0.32,
      fontSize: 10, bold: true, align: "center", valign: "middle",
      color: C.white, margin: 0
    });

    // Title
    slide.addText(issue.title, {
      x: x + 0.15, y: 3.05, w: cardW - 0.3, h: 0.5,
      fontSize: 15, bold: true, align: "center",
      color: C.text, margin: 0
    });

    // Description
    slide.addText(issue.desc, {
      x: x + 0.2, y: 3.6, w: cardW - 0.4, h: 1,
      fontSize: 11, align: "center", color: C.muted, margin: 0
    });
  });

  // Bottom note
  slide.addText("三项安全缺陷均已修复，并完成完整安全加固", {
    x: 0.5, y: 5.0, w: 9, h: 0.4,
    fontSize: 12, align: "center", color: C.muted, margin: 0
  });
}

// ─────────────────────────────────────────────
// Slide 3: 修复一 - 硬编码 API Key
// ─────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  // Header
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.1,
    fill: { color: C.navy }
  });
  slide.addText("修复一：硬编码 API Key", {
    x: 0.5, y: 0.25, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial Black", bold: true,
    color: C.white, margin: 0
  });

  // Left: Before card
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.35, w: 4.3, h: 3.6,
    fill: { color: C.cardBg },
    shadow: cardShadow()
  });
  // Red top bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.35, w: 4.3, h: 0.1,
    fill: { color: C.danger }
  });
  slide.addText("修复前", {
    x: 0.7, y: 1.55, w: 1.2, h: 0.4,
    fontSize: 12, bold: true, color: C.danger, margin: 0
  });
  slide.addText("风险：密钥提交至代码仓库，任何人能访问", {
    x: 0.7, y: 1.92, w: 3.9, h: 0.35,
    fontSize: 10, color: C.muted, margin: 0
  });
  // Code block
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 2.32, w: 3.9, h: 1.1,
    fill: { color: "1E1E1E" }, rectRadius: 0.08
  });
  slide.addText([
    { text: "app_id = ", options: { color: "9CDCFE" } },
    { text: '"2043649085851829312"', options: { color: "CE9178" } },
    { text: "\napi_key = ", options: { color: "9CDCFE", breakLine: true } },
    { text: '"EYlR4WZ5wkyke1hhyf7OKsV..."', options: { color: "CE9178" } },
    { text: "  ", options: {} }
  ], {
    x: 0.85, y: 2.42, w: 3.6, h: 0.9,
    fontSize: 10, fontFace: "Consolas", margin: 0
  });

  // Issues list
  slide.addText([
    { text: "\u26A0 ", options: { color: C.warning } },
    { text: "app_id / api_key 明文暴露", options: { color: C.text, breakLine: true } },
    { text: "\u26A0 ", options: { color: C.warning } },
    { text: "提交代码仓库 = 密钥泄露", options: { color: C.text, breakLine: true } },
    { text: "\u26A0 ", options: { color: C.warning } },
    { text: "多文件硬编码，难以批量撤销", options: { color: C.text } }
  ], {
    x: 0.7, y: 3.55, w: 3.9, h: 1.2,
    fontSize: 11, margin: 0
  });

  // Arrow
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 4.9, y: 2.9, w: 0.3, h: 0.06,
    fill: { color: C.accent }
  });
  slide.addText("\u27A1", {
    x: 5.0, y: 2.7, w: 0.5, h: 0.5,
    fontSize: 22, color: C.accent, margin: 0
  });

  // Right: After card
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.35, w: 4.3, h: 3.6,
    fill: { color: C.cardBg },
    shadow: cardShadow()
  });
  // Green top bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.35, w: 4.3, h: 0.1,
    fill: { color: C.success }
  });
  slide.addText("修复后", {
    x: 5.4, y: 1.55, w: 1.2, h: 0.4,
    fontSize: 12, bold: true, color: C.success, margin: 0
  });
  slide.addText("方案：从环境变量读取，密钥集中管理", {
    x: 5.4, y: 1.92, w: 3.9, h: 0.35,
    fontSize: 10, color: C.muted, margin: 0
  });
  // Code block
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.4, y: 2.32, w: 3.9, h: 1.1,
    fill: { color: "1E1E1E" }, rectRadius: 0.08
  });
  slide.addText([
    { text: "from app.config import settings\n", options: { color: "4EC9B0", breakLine: true } },
    { text: "app_id = ", options: { color: "9CDCFE" } },
    { text: "settings.", options: { color: "9CDCFE" } },
    { text: "document_agent_id", options: { color: "CE9178" } }
  ], {
    x: 5.55, y: 2.42, w: 3.6, h: 0.9,
    fontSize: 10, fontFace: "Consolas", margin: 0
  });

  // Fixes list
  slide.addText([
    { text: "\u2713 ", options: { color: C.success } },
    { text: "密钥存入 .env，不提交仓库", options: { color: C.text, breakLine: true } },
    { text: "\u2713 ", options: { color: C.success } },
    { text: "统一配置中心 config.py", options: { color: C.text, breakLine: true } },
    { text: "\u2713 ", options: { color: C.success } },
    { text: "启动检查：缺失则报错退出", options: { color: C.text } }
  ], {
    x: 5.4, y: 3.55, w: 3.9, h: 1.2,
    fontSize: 11, margin: 0
  });

  // Files modified badge
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.05, w: 9, h: 0.4,
    fill: { color: C.navy, transparency: 90 }
  });
  slide.addText("涉及文件：config.py  ·  image_agent_service.py  ·  document_workflow_service.py  ·  .env", {
    x: 0.5, y: 5.05, w: 9, h: 0.4,
    fontSize: 10, align: "center", valign: "middle", color: C.muted, margin: 0
  });
}

// ─────────────────────────────────────────────
// Slide 4: 修复二 - 固定验证码明文
// ─────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  // Header
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.1,
    fill: { color: C.navy }
  });
  slide.addText("修复二：固定验证码明文暴露", {
    x: 0.5, y: 0.25, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial Black", bold: true,
    color: C.white, margin: 0
  });

  // Timeline style layout
  // Left column - Problem
  const problemX = 0.5;
  const fixX = 5.3;
  const cardW = 4.2;

  // Problem card
  slide.addShape(pres.shapes.RECTANGLE, {
    x: problemX, y: 1.35, w: cardW, h: 2.4,
    fill: { color: C.cardBg },
    shadow: cardShadow()
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: problemX, y: 1.35, w: cardW, h: 0.1,
    fill: { color: C.danger }
  });
  slide.addText("问题", {
    x: problemX + 0.2, y: 1.55, w: 1.2, h: 0.4,
    fontSize: 12, bold: true, color: C.danger, margin: 0
  });
  slide.addText([
    { text: "1. ", options: { bold: true } },
    { text: "dev_hint 字段将明文验证码返回前端", options: { breakLine: true } },
    { text: "2. ", options: { bold: true } },
    { text: "前端页面直接展示验证码 123456", options: { breakLine: true } },
    { text: "3. ", options: { bold: true } },
    { text: "攻击者无需手机即可获取有效验证码", options: {} }
  ], {
    x: problemX + 0.2, y: 2.0, w: cardW - 0.4, h: 1.5,
    fontSize: 12, color: C.text, margin: 0
  });

  // Arrow
  slide.addText("\u27A1", {
    x: 4.7, y: 2.3, w: 0.5, h: 0.5,
    fontSize: 22, color: C.accent, margin: 0
  });

  // Fix card
  slide.addShape(pres.shapes.RECTANGLE, {
    x: fixX, y: 1.35, w: cardW, h: 2.4,
    fill: { color: C.cardBg },
    shadow: cardShadow()
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: fixX, y: 1.35, w: cardW, h: 0.1,
    fill: { color: C.success }
  });
  slide.addText("修复方案", {
    x: fixX + 0.2, y: 1.55, w: 1.5, h: 0.4,
    fontSize: 12, bold: true, color: C.success, margin: 0
  });
  slide.addText([
    { text: "\u2713 ", options: { color: C.success } },
    { text: "每次请求生成全新随机6位验证码", options: { breakLine: true } },
    { text: "\u2713 ", options: { color: C.success } },
    { text: "移除 dev_hint，验证码仅打印到服务端日志", options: { breakLine: true } },
    { text: "\u2713 ", options: { color: C.success } },
    { text: "前端移除验证码展示逻辑", options: {} }
  ], {
    x: fixX + 0.2, y: 2.0, w: cardW - 0.4, h: 1.5,
    fontSize: 12, color: C.text, margin: 0
  });

  // Before/After comparison box
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.95, w: 9, h: 1.0,
    fill: { color: C.cardBg },
    shadow: cardShadow()
  });

  // Before
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.95, w: 0.08, h: 1.0,
    fill: { color: C.danger }
  });
  slide.addText("修复前：POST /send-code → { dev_hint: \"123456\", ok: true }", {
    x: 0.75, y: 4.1, w: 4, h: 0.35,
    fontSize: 11, color: C.danger, margin: 0
  });
  slide.addText("前端直接显示：您的验证码是 123456", {
    x: 0.75, y: 4.5, w: 4, h: 0.3,
    fontSize: 10, color: C.muted, margin: 0
  });

  // Divider
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 4.95, y: 4.1, w: 0.02, h: 0.7,
    fill: { color: C.divider }
  });

  // After
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 3.95, w: 0.08, h: 1.0,
    fill: { color: C.success }
  });
  slide.addText("修复后：POST /send-code → { ok: true, message: \"已发送\" }", {
    x: 5.45, y: 4.1, w: 4.2, h: 0.35,
    fontSize: 11, color: C.success, margin: 0
  });
  slide.addText("验证码仅打印在后端控制台： [开发] 手机号 xxx 的验证码: 827341", {
    x: 5.45, y: 4.5, w: 4.2, h: 0.3,
    fontSize: 10, color: C.muted, margin: 0
  });
}

// ─────────────────────────────────────────────
// Slide 5: 修复三 - CORS 通配符
// ─────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  // Header
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.1,
    fill: { color: C.navy }
  });
  slide.addText("修复三：CORS 通配符安全漏洞", {
    x: 0.5, y: 0.25, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial Black", bold: true,
    color: C.white, margin: 0
  });

  // Warning banner
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 9, h: 0.55,
    fill: { color: C.warning, transparency: 85 }
  });
  slide.addText("\u26A0  allow_origins=[\"*\"] 配合  allow_credentials=True  是浏览器安全策略明确禁止的不安全组合", {
    x: 0.7, y: 1.35, w: 8.6, h: 0.45,
    fontSize: 11.5, bold: true, color: C.warning, margin: 0, valign: "middle"
  });

  // Fix description - two column
  // Left: Config
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.0, w: 4.3, h: 2.6,
    fill: { color: C.cardBg },
    shadow: cardShadow()
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.0, w: 4.3, h: 0.1,
    fill: { color: C.accent }
  });
  slide.addText("配置改动", {
    x: 0.7, y: 2.2, w: 2, h: 0.4,
    fontSize: 13, bold: true, color: C.accent, margin: 0
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 2.65, w: 3.9, h: 0.85,
    fill: { color: "1E1E1E" }, rectRadius: 0.08
  });
  slide.addText([
    { text: "# .env\n", options: { color: "6A9955", breakLine: true } },
    { text: "CORS_ORIGINS=localhost:5173\n", options: { color: "CE9178", breakLine: true } },
    { text: "# .py\n", options: { color: "6A9955", breakLine: true } },
    { text: "allow_origins=cors_origins", options: { color: "9CDCFE" } }
  ], {
    x: 0.85, y: 2.72, w: 3.6, h: 0.72,
    fontSize: 9.5, fontFace: "Consolas", margin: 0
  });
  slide.addText([
    { text: "\u2713 从环境变量读取允许域名列表", options: { color: C.text, breakLine: true } },
    { text: "\u2713 生产环境配置实际前端域名", options: { color: C.text, breakLine: true } },
    { text: "\u2713 开发 / 生产环境灵活切换", options: { color: C.text } }
  ], {
    x: 0.7, y: 3.65, w: 3.9, h: 0.85,
    fontSize: 11, margin: 0
  });

  // Right: Security impact
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 2.0, w: 4.3, h: 2.6,
    fill: { color: C.cardBg },
    shadow: cardShadow()
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 2.0, w: 4.3, h: 0.1,
    fill: { color: C.success }
  });
  slide.addText("安全效果", {
    x: 5.4, y: 2.2, w: 2, h: 0.4,
    fontSize: 13, bold: true, color: C.success, margin: 0
  });
  slide.addText([
    { text: "\u2713 仅允许配置的域名跨域访问 API", options: { color: C.text, breakLine: true } },
    { text: "\u2713 携带 cookie / token 的跨域请求被正确限制", options: { color: C.text, breakLine: true } },
    { text: "\u2713 恶意网站无法冒充用户身份请求", options: { color: C.text, breakLine: true } },
    { text: "\u2713 防止 CSRF 攻击面扩大", options: { color: C.text } }
  ], {
    x: 5.4, y: 2.7, w: 3.9, h: 1.7,
    fontSize: 11.5, margin: 0
  });

  // Bottom: before vs after
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.75, w: 9, h: 0.65,
    fill: { color: "1E1E1E" }, rectRadius: 0.08
  });
  slide.addText([
    { text: "修复前: ", options: { color: C.danger, bold: true } },
    { text: "allow_origins=[\"*\"], allow_credentials=True", options: { color: "F8F8F2", breakLine: true } },
    { text: "修复后: ", options: { color: C.success, bold: true } },
    { text: "allow_origins=[cors_origins]  # 从环境变量读取，白名单模式", options: { color: "F8F8F2" } }
  ], {
    x: 0.7, y: 4.82, w: 8.6, h: 0.5,
    fontSize: 10, fontFace: "Consolas", margin: 0, valign: "middle"
  });
}

// ─────────────────────────────────────────────
// Slide 6: 额外安全加固
// ─────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  // Header
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.1,
    fill: { color: C.navy }
  });
  slide.addText("额外安全加固", {
    x: 0.5, y: 0.25, w: 9, h: 0.6,
    fontSize: 28, fontFace: "Arial Black", bold: true,
    color: C.white, margin: 0
  });

  // Two major items
  // JWT auto-generate
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 4.3, h: 3.0,
    fill: { color: C.cardBg },
    shadow: cardShadow()
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 4.3, h: 0.1,
    fill: { color: C.accent }
  });

  // Lock icon circle
  slide.addShape(pres.shapes.OVAL, {
    x: 0.7, y: 1.52, w: 0.6, h: 0.6,
    fill: { color: C.accent, transparency: 85 }
  });
  slide.addText("\uD83D\uDD12", {
    x: 0.7, y: 1.54, w: 0.6, h: 0.6,
    fontSize: 20, align: "center", valign: "middle", margin: 0
  });

  slide.addText("JWT 密钥自动生成", {
    x: 1.45, y: 1.6, w: 3, h: 0.45,
    fontSize: 15, bold: true, color: C.text, margin: 0, valign: "middle"
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 2.2, w: 3.9, h: 0.8,
    fill: { color: "1E1E1E" }, rectRadius: 0.08
  });
  slide.addText([
    { text: "settings.secret_key = secrets.token_hex(32)", options: { color: "9CDCFE", breakLine: true } },
    { text: "# 生产环境：缺失则启动报错退出", options: { color: "6A9955" } }
  ], {
    x: 0.85, y: 2.28, w: 3.6, h: 0.65,
    fontSize: 10, fontFace: "Consolas", margin: 0
  });

  slide.addText([
    { text: "\u2713 开发环境：自动生成随机密钥", options: { color: C.text, breakLine: true } },
    { text: "\u2713 生产环境：未配置强密钥则拒绝启动", options: { color: C.text, breakLine: true } },
    { text: "\u2713 防止生产环境使用弱密钥", options: { color: C.text } }
  ], {
    x: 0.7, y: 3.1, w: 3.9, h: 1.0,
    fontSize: 11, margin: 0
  });

  // Env management
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.3, w: 4.3, h: 3.0,
    fill: { color: C.cardBg },
    shadow: cardShadow()
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.3, w: 4.3, h: 0.1,
    fill: { color: C.success }
  });

  slide.addShape(pres.shapes.OVAL, {
    x: 5.4, y: 1.52, w: 0.6, h: 0.6,
    fill: { color: C.success, transparency: 85 }
  });
  slide.addText("\uD83D\uDCC4", {
    x: 5.4, y: 1.54, w: 0.6, h: 0.6,
    fontSize: 20, align: "center", valign: "middle", margin: 0
  });

  slide.addText("密钥集中管理", {
    x: 6.15, y: 1.6, w: 3, h: 0.45,
    fontSize: 15, bold: true, color: C.text, margin: 0, valign: "middle"
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.4, y: 2.2, w: 3.9, h: 0.8,
    fill: { color: "1E1E1E" }, rectRadius: 0.08
  });
  slide.addText([
    { text: "# .env.example 提交仓库\n", options: { color: "6A9955", breakLine: true } },
    { text: "DOCUMENT_AGENT_ID=\nSECRET_KEY=", options: { color: "9CDCFE" } }
  ], {
    x: 5.55, y: 2.28, w: 3.6, h: 0.65,
    fontSize: 10, fontFace: "Consolas", margin: 0
  });

  slide.addText([
    { text: "\u2713 .env 加入 .gitignore 不外泄", options: { color: C.text, breakLine: true } },
    { text: "\u2713 .env.example 模板引导正确配置", options: { color: C.text, breakLine: true } },
    { text: "\u2713 新环境部署流程规范化", options: { color: C.text } }
  ], {
    x: 5.4, y: 3.1, w: 3.9, h: 1.0,
    fontSize: 11, margin: 0
  });

  // Summary bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.5, w: 9, h: 0.8,
    fill: { color: C.navy }
  });
  slide.addText("修改文件数：7 个    |    高危修复：2 项    |    中危修复：1 项    |    额外加固：2 项", {
    x: 0.5, y: 4.5, w: 9, h: 0.8,
    fontSize: 13, align: "center", valign: "middle",
    color: C.ice, margin: 0
  });
}

// ─────────────────────────────────────────────
// Slide 7: 总结
// ─────────────────────────────────────────────
{
  let slide = pres.addSlide();
  slide.background = { color: C.navy };

  // Decorative shapes
  slide.addShape(pres.shapes.OVAL, {
    x: -1, y: 3.5, w: 3.5, h: 3.5,
    fill: { color: C.accent, transparency: 85 }
  });
  slide.addShape(pres.shapes.OVAL, {
    x: 8, y: -1, w: 3, h: 3,
    fill: { color: C.accent, transparency: 80 }
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.3, w: 10, h: 0.04,
    fill: { color: C.accent, transparency: 50 }
  });

  // Left accent bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.18, h: 5.625,
    fill: { color: C.accent }
  });

  // Title
  slide.addText("安全优化完成", {
    x: 0.8, y: 1.5, w: 8, h: 1.0,
    fontSize: 44, fontFace: "Arial Black", bold: true,
    color: C.white, margin: 0
  });

  slide.addText("三处安全缺陷全部修复，安全能力达到生产级别标准", {
    x: 0.8, y: 2.55, w: 8, h: 0.5,
    fontSize: 16, color: C.ice, margin: 0
  });

  // Status items
  const statusItems = [
    { text: "\u2705  硬编码 API Key — 环境变量方案", color: C.success },
    { text: "\u2705  固定验证码 — 随机一次性验证码", color: C.success },
    { text: "\u2705  CORS 通配符 — 白名单域名模式", color: C.success },
    { text: "\u2705  JWT 密钥 — 生产环境强校验", color: C.success },
  ];
  statusItems.forEach((item, i) => {
    slide.addText(item.text, {
      x: 0.8, y: 3.2 + i * 0.45, w: 8, h: 0.4,
      fontSize: 14, color: item.color, margin: 0
    });
  });
}

// Write file
pres.writeFile({ fileName: "d:/腾讯智能体比赛/安全优化介绍.pptx" })
  .then(() => console.log("PPT 已生成: 安全优化介绍.pptx"))
  .catch(err => console.error("生成失败:", err));
