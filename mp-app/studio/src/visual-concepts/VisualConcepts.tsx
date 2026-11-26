import { useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useMotionPreset } from "../lib/motion";
import {
  Alert,
  Avatar,
  Badge,
  Button,
  Card,
  Divider,
  Drawer,
  Input,
  Modal,
  Progress,
  Segmented,
  Statistic,
  Tag,
  Tooltip,
  message,
} from "antd";
import {
  ArrowLeftOutlined,
  BarChartOutlined,
  BellOutlined,
  CalendarOutlined,
  CheckOutlined,
  ClockCircleOutlined,
  DashboardOutlined,
  FileSearchOutlined,
  HomeOutlined,
  MenuOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ScanOutlined,
  SearchOutlined,
  SettingOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  UserOutlined,
  WalletOutlined,
} from "@ant-design/icons";

type Direction = "arena" | "coach" | "precision";
type Screen = "landing" | "member" | "studio";
type DrawerMode = "program" | "case" | null;

type DirectionInfo = {
  id: Direction;
  number: string;
  title: string;
  short: string;
  promise: string;
  layout: string;
  motion: string;
  reuse: string;
};

const directions: DirectionInfo[] = [
  {
    id: "arena",
    number: "01",
    title: "ARENA · قدرتِ متمرکز",
    short: "سینمایی، پرکنتراست، با تمرکز روی اقدام بعدی",
    promise: "هر تمرین، قدم بعدی توست.",
    layout: "Hero تمام‌عرض + یک نقطهٔ تمرکز؛ عضو با کارت «امروز» و Studio با صف کار واضح.",
    motion: "ورود نرم 250ms، حلقهٔ پیشرفت کوتاه 450ms، hover کارت حداکثر 4px؛ بدون حرکت دائمی.",
    reuse: "Ant Design Button / Card / Progress + Motion AnimatePresence و motion؛ پالت تیرهٔ موجود.",
  },
  {
    id: "coach",
    number: "02",
    title: "TOGETHER · همراهی انسانی",
    short: "روایت‌محور، آرام‌تر، با رابطهٔ عضو و مربی در مرکز",
    promise: "یک برنامه؛ همراهیِ روشن.",
    layout: "چیدمان editorial دو ستونه؛ مسیر عضو و یادداشت مربی در کنار CTAهای نقش‌محور.",
    motion: "ورود مرحله‌ای محتوا با فاصلهٔ کوتاه؛ انتقال‌ها فقط برای نشان‌دادن رابطه/وضعیت.",
    reuse: "Ant Design Card / Avatar / Tag / Segmented + Motion؛ رنگ‌های برند حفظ می‌شوند.",
  },
  {
    id: "precision",
    number: "03",
    title: "LAB · دقت و پیشرفت",
    short: "ساختاریافته و داده‌محور؛ مناسب مرور برنامه و شاخص‌ها",
    promise: "پیشرفت را می‌شود دید.",
    layout: "شبکهٔ اطلاعاتی منظم؛ اولویت با وضعیت برنامه، دادهٔ نمونه و دسترسی سریع.",
    motion: "انتقال تب با layout indicator، نمودارهای نمونه بدون جهش؛ reduced-motion رعایت می‌شود.",
    reuse: "Ant Design Statistic / Progress / Input / Drawer + Motion؛ بدون کتابخانهٔ UI جدید.",
  },
];

const screenOptions: { label: string; value: Screen }[] = [
  { label: "Landing عمومی", value: "landing" },
  { label: "عضو · نمای موبایل", value: "member" },
  { label: "Studio · مربی/مدیر", value: "studio" },
];

const studioNav: { label: string; icon: ReactNode }[] = [
  { label: "صف کار", icon: <DashboardOutlined /> },
  { label: "اعضا", icon: <TeamOutlined /> },
  { label: "برنامه‌ها", icon: <FileSearchOutlined /> },
  { label: "کلاس‌ها", icon: <CalendarOutlined /> },
  { label: "مالی", icon: <WalletOutlined /> },
  { label: "تنظیمات", icon: <SettingOutlined /> },
];

const demoRows = [
  { name: "سارا محمدی", initials: "سم", work: "پیش‌نویس برنامهٔ ۴ هفته‌ای", status: "نیازمند بازبینی", tone: "gold" as const },
  { name: "آرمان رضایی", initials: "آر", work: "ارزیابی · دادهٔ ناقص", status: "نیازمند تکمیل", tone: "cyan" as const },
  { name: "نیلوفر احمدی", initials: "نآ", work: "برنامهٔ تأییدشده · نسخهٔ نمونه", status: "آمادهٔ مشاهده", tone: "green" as const },
];

export default function VisualConcepts() {
  const [direction, setDirection] = useState<Direction>("arena");
  const [screen, setScreen] = useState<Screen>("landing");
  const [selected, setSelected] = useState<Direction | null>(null);
  const [drawerMode, setDrawerMode] = useState<DrawerMode>(null);
  const [qrOpen, setQrOpen] = useState(false);
  const [memberTab, setMemberTab] = useState("خانه");
  const [studioPage, setStudioPage] = useState("صف کار");
  const [studioFilter, setStudioFilter] = useState("همه");
  const [memberSearch, setMemberSearch] = useState("");
  const [replayKey, setReplayKey] = useState(0);
  const [messageApi, contextHolder] = message.useMessage();
  const motionPreset = useMotionPreset();
  const info = directions.find((option) => option.id === direction)!;

  const visibleRows = useMemo(() => {
    const query = memberSearch.trim().toLocaleLowerCase("fa");
    return demoRows.filter((row) => {
      const matchesFilter = studioFilter === "همه" || row.status === studioFilter;
      const matchesQuery = !query || `${row.name} ${row.work} ${row.status}`.toLocaleLowerCase("fa").includes(query);
      return matchesFilter && matchesQuery;
    });
  }, [memberSearch, studioFilter]);

  const previewOnly = () => messageApi.info({ content: "فقط جابه‌جایی در پیش‌نمایش؛ هیچ API یا داده‌ای تغییر نمی‌کند.", duration: 2.4 });
  const openLandingScreen = (next: Screen) => {
    setScreen(next);
    if (next !== "landing") previewOnly();
  };
  const chooseDirection = () => {
    setSelected(direction);
    messageApi.info({ content: `جهت «${info.title}» در همین پیش‌نمایش علامت خورد؛ هنوز تأیید نهایی/فلوچارتی ساخته نشده است.`, duration: 3.2 });
  };

  return (
    <div className={`concept-lab concept-lab--${direction}`}>
      {contextHolder}
      <div className="lab-wrap">
        <header className="lab-header">
          <div className="lab-heading">
            <div className="lab-mark" aria-hidden="true">MP</div>
            <div>
              <div className="lab-eyebrow">MUSCLE PARADISE · DESIGN LAB</div>
              <h1>سه جهت برای رابط کاربریِ یکپارچه</h1>
              <p>گزینه‌ها را عوض کن و Landing، تجربهٔ عضو و Studio را در همان زبان طراحی ببین.</p>
            </div>
          </div>
          <div className="lab-status">
            <Tag color="green">پیش‌نمایش تعاملی</Tag>
            <span><span className="status-dot" /> بدون اتصال API</span>
          </div>
        </header>

        <section className="direction-picker" aria-label="انتخاب جهت طراحی">
          <div className="picker-heading">
            <div>
              <span className="step-label">مرحلهٔ ۱</span>
              <h2>جهت بصری را مقایسه کن</h2>
            </div>
            <span className="picker-help">هر سه گزینه RTL، واکنش‌گرا و مبتنی بر توکن‌های فعلی‌اند.</span>
          </div>
          <div className="direction-grid">
            {directions.map((option) => (
              <button
                key={option.id}
                type="button"
                className={`direction-choice ${direction === option.id ? "is-active" : ""}`}
                aria-pressed={direction === option.id}
                onClick={() => setDirection(option.id)}
              >
                <span className="direction-number">{option.number}</span>
                <span className="direction-copy">
                  <strong>{option.title}</strong>
                  <small>{option.short}</small>
                </span>
                {direction === option.id && (
                  <motion.span
                    layoutId={motionPreset.reduced ? undefined : "active-direction"}
                    className="active-marker"
                    transition={
                      motionPreset.reduced
                        ? { duration: 0 }
                        : { type: "spring", stiffness: 260, damping: 24 }
                    }
                  />
                )}
                {selected === option.id && <CheckOutlined className="chosen-check" aria-label="علامت‌خورده در این پیش‌نمایش" />}
              </button>
            ))}
          </div>
        </section>

        <div className="workspace-grid">
          <main className="preview-column">
            <div className="preview-toolbar">
              <div>
                <span className="step-label">مرحلهٔ ۲</span>
                <h2>نمونهٔ صفحه</h2>
              </div>
              <div className="toolbar-actions">
                <Segmented
                  aria-label="انتخاب صفحهٔ پیش‌نمایش"
                  options={screenOptions}
                  value={screen}
                  onChange={(value) => setScreen(value as Screen)}
                />
                <Tooltip title="اجرای دوبارهٔ حرکت ورود؛ در حالت کاهش حرکت خاموش می‌ماند">
                  <Button
                    aria-label="اجرای دوبارهٔ حرکت ورود"
                    icon={<PlayCircleOutlined />}
                    onClick={() => setReplayKey((value) => value + 1)}
                  >
                    نمایش موشن
                  </Button>
                </Tooltip>
                <Button type="primary" icon={<CheckOutlined />} onClick={chooseDirection}>
                  انتخاب این جهت
                </Button>
              </div>
            </div>

            <div className="viewport-label-row">
              <span>{info.number} / {info.title}</span>
              <Tag color="gold">همهٔ اعداد و اسامی داخل mockup ساختگی‌اند</Tag>
            </div>

            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={`${direction}-${screen}-${replayKey}`}
                className={`mock-viewport mock-viewport--${direction} mock-viewport--${screen}`}
                {...(motionPreset.reduced ? motionPreset.fade : motionPreset.rise)}
                exit={
                  motionPreset.reduced
                    ? { opacity: 0, transition: motionPreset.fade.transition }
                    : { opacity: 0, y: -8 }
                }
              >
                {screen === "landing" && <LandingPreview direction={direction} onScreen={openLandingScreen} onMessage={previewOnly} />}
                {screen === "member" && (
                  <MemberPreview
                    direction={direction}
                    activeTab={memberTab}
                    onTab={setMemberTab}
                    onProgram={() => setDrawerMode("program")}
                    onQr={() => setQrOpen(true)}
                    onMessage={previewOnly}
                  />
                )}
                {screen === "studio" && (
                  <StudioPreview
                    direction={direction}
                    page={studioPage}
                    onPage={setStudioPage}
                    filter={studioFilter}
                    onFilter={setStudioFilter}
                    query={memberSearch}
                    onQuery={setMemberSearch}
                    rows={visibleRows}
                    onCase={() => setDrawerMode("case")}
                    onMessage={previewOnly}
                  />
                )}
              </motion.div>
            </AnimatePresence>
          </main>

          <aside className="design-notes" aria-label="مشخصات جهت طراحی">
            <Card className="note-card" bordered={false}>
              <div className="note-kicker"><span className="note-spark" /> جهت انتخاب‌شده</div>
              <h2>{info.title}</h2>
              <p className="note-promise">«{info.promise}»</p>
              <Divider />
              <dl className="spec-list">
                <div><dt>چیدمان</dt><dd>{info.layout}</dd></div>
                <div><dt>موشن</dt><dd>{info.motion}</dd></div>
                <div><dt>بازیافت کد</dt><dd>{info.reuse}</dd></div>
              </dl>
              <Alert
                className="guardrail-alert"
                type="info"
                showIcon
                message="مرز پیش‌نمایش"
                description="CTAها فقط بین نماهای این نمونه جابه‌جا می‌شوند. تأیید برنامه، پرداخت، حضور، QR و ذخیره‌سازی به سرویس وصل نیستند."
              />
            </Card>

            <Card className="reuse-card" bordered={false}>
              <div className="note-kicker">استفادهٔ مجدد از منابع آزاد</div>
              <ul className="reuse-list">
                <li><span className="reuse-icon">A</span><span><strong>Ant Design · MIT</strong><small>دکمه، کارت، Segmented، Progress، Drawer، Modal و Input؛ از dependency موجود Studio.</small></span></li>
                <li><span className="reuse-icon reuse-icon--motion">M</span><span><strong>Motion · MIT</strong><small>AnimatePresence، حرکت صفحه و helper مشترک reduced-motion؛ همان پکیج framer-motion فعلی.</small></span></li>
                <li><span className="reuse-icon reuse-icon--guide">✓</span><span><strong>راهنماها، نه dependency</strong><small>Vercel Web Interface Guidelines و Chrome Modern Web Guidance برای دسترس‌پذیری و رفتار وب.</small></span></li>
              </ul>
              <div className="source-links">
                <a href="https://github.com/ant-design/ant-design" target="_blank" rel="noreferrer">Ant Design ↗</a>
                <a href="https://github.com/motiondivision/motion" target="_blank" rel="noreferrer">Motion ↗</a>
                <a href="https://github.com/vercel-labs/web-interface-guidelines" target="_blank" rel="noreferrer">Vercel Guidelines ↗</a>
                <a href="https://github.com/GoogleChrome/modern-web-guidance" target="_blank" rel="noreferrer">Chrome Guidance ↗</a>
              </div>
            </Card>
          </aside>
        </div>

        <footer className="lab-footer">
          <span>مبنای بصری مشترک: <code>#0B0F14</code> · <code>#00B86A</code> · <code>#FFD700</code> · Vazirmatn · RTL</span>
          <span>عضو: مبنای Android/Flutter · Studio: React/Vite · این صفحه فقط concept است.</span>
        </footer>
      </div>

      <Drawer
        title={drawerMode === "case" ? "پروندهٔ نمونه · بازبینی" : "پیش‌نمایش برنامهٔ امروز"}
        open={drawerMode !== null}
        onClose={() => setDrawerMode(null)}
        placement="left"
        width={440}
        className="preview-drawer"
      >
        {drawerMode === "case" ? (
          <div className="drawer-content">
            <Tag color="gold">نیازمند بازبینی · دادهٔ نمایشی</Tag>
            <h3>سارا محمدی</h3>
            <p>نسخهٔ نمونهٔ برنامه برای نمایش ساختار کنترل‌هاست؛ وضعیت و محتوای واقعی عضو نیست.</p>
            <Card size="small" className="drawer-info-card">
              <strong>گیت داده</strong>
              <p>پروفایل ← ارزیابی ← پیش‌نویس ← بازبینی مربی ← تأیید سرور</p>
            </Card>
            <Alert
              type="warning"
              showIcon
              message="نوشتن غیرفعال است"
              description="دکمه‌های تأیید/رد عمداً غیرفعال‌اند؛ این prototype سرویس یا مجوز واقعی ندارد و نباید موفقیت ساختگی نشان دهد."
            />
            <div className="drawer-actions">
              <Tooltip title="تا اتصال endpoint، مجوز و ثبت Audit فعال نمی‌شود"><span><Button type="primary" disabled>تأیید برنامه</Button></span></Tooltip>
              <Tooltip title="تا اتصال endpoint و قرارداد خطا فعال نمی‌شود"><span><Button danger disabled>بازگرداندن برای اصلاح</Button></span></Tooltip>
            </div>
          </div>
        ) : (
          <div className="drawer-content">
            <Tag color="green">نسخهٔ نمایشی · بدون دادهٔ سرور</Tag>
            <h3>جلسهٔ قدرت A</h3>
            <p>این پنل صرفاً چیدمان خلاصهٔ برنامه، وضعیت تأیید و اقدام بعدی را نشان می‌دهد.</p>
            <div className="exercise-row"><span>۱</span><div><strong>پرس سینه</strong><small>۳ ست · ۱۰ تکرار · مثال نمایشی</small></div><Tag>نمونه</Tag></div>
            <div className="exercise-row"><span>۲</span><div><strong>پارویی سیم‌کش</strong><small>۳ ست · ۱۲ تکرار · مثال نمایشی</small></div><Tag>نمونه</Tag></div>
            <div className="exercise-row"><span>۳</span><div><strong>پرس سرشانه</strong><small>۳ ست · ۸ تکرار · مثال نمایشی</small></div><Tag>نمونه</Tag></div>
            <Alert className="drawer-alert" type="info" showIcon message="هیچ تمرینی ثبت یا شروع نمی‌شود" description="دکمه‌های این پیش‌نمایش فقط برای سنجش ظاهر و مسیر کلیک‌اند." />
            <Button block onClick={() => setDrawerMode(null)}>بستن پنل</Button>
          </div>
        )}
      </Drawer>

      <Modal
        title="پیش‌نمایش QR حضور"
        open={qrOpen}
        onCancel={() => setQrOpen(false)}
        footer={<Button onClick={() => setQrOpen(false)}>بستن</Button>}
        centered
      >
        <div className="fake-qr" aria-label="نماد نمایشی و غیرقابل اسکن"><span>MP</span><small>نماد غیرواقعی</small></div>
        <Alert type="warning" showIcon message="QR واقعی ساخته نشده است" description="این کادر قابل اسکن نیست و به حضور/عضویت متصل نیست؛ فقط نمونهٔ نمایش جایگاه QR در رابط است." />
      </Modal>

    </div>
  );
}

type LandingPreviewProps = {
  direction: Direction;
  onScreen: (screen: Screen) => void;
  onMessage: () => void;
};

function LandingPreview({ direction, onScreen, onMessage }: LandingPreviewProps) {
  const motionPreset = useMotionPreset();
  const progress = direction === "arena" ? 72 : direction === "coach" ? 58 : 84;
  return (
    <div className={`product-surface product-surface--${direction}`}>
      <nav className="product-nav" aria-label="ناوبری نمونهٔ Landing">
        <button className="product-brand" type="button" onClick={() => onScreen("landing")}>
          <span className="product-mark">MP</span>
          <span><strong>MUSCLE</strong><small>PARADISE</small></span>
        </button>
        <div className="product-links">
          <button type="button" onClick={() => onScreen("landing")}>خانه</button>
          <button type="button" onClick={() => onScreen("member")}>تجربهٔ عضو</button>
          <button type="button" onClick={() => onScreen("studio")}>برای مربی</button>
        </div>
        <Button type="primary" onClick={() => onScreen("member")}>ورود اعضا <ArrowLeftOutlined /></Button>
      </nav>

      <section className={`landing-hero landing-hero--${direction}`}>
        <div className="hero-copy">
          <div className="hero-eyebrow"><span className="hero-eyebrow-dot" /> تجربهٔ تمرین، روشن و قابل پیگیری</div>
          <h2>{direction === "arena" ? <>هر تمرین،<br /><em>قدم بعدی توست.</em></> : direction === "coach" ? <>یک برنامه؛<br /><em>همراهیِ روشن.</em></> : <>پیشرفت را<br /><em>می‌شود دید.</em></>}</h2>
          <p>{direction === "arena" ? "برنامهٔ امروز، بازخورد مربی و مسیر پیشرفت را در تجربه‌ای یکپارچه کنار هم ببین." : direction === "coach" ? "عضو و مربی در یک مسیر؛ از ارزیابی تا بازبینی برنامه، با نقش‌ها و وضعیت‌های روشن." : "اطلاعات مهم در جای درست؛ وضعیت برنامه و اقدام بعدی را بدون شلوغی پیدا کن."}</p>
          <div className="hero-cta">
            <Button type="primary" size="large" onClick={() => onScreen("member")}>نمای عضو <ArrowLeftOutlined /></Button>
            <Button size="large" onClick={() => onScreen("studio")}>نمای مربی / مدیر</Button>
          </div>
          <div className="hero-footnote"><span>✦</span> نمونهٔ طراحی · بدون ادعای قیمت، آمار یا سرویس فعال</div>
        </div>

        <div className={`hero-visual hero-visual--${direction}`}>
          {direction === "arena" && (
            <motion.div
              className="arena-orbit"
              initial={motionPreset.reduced ? motionPreset.fade.initial : { scale: 0.94, opacity: 0 }}
              animate={motionPreset.reduced ? motionPreset.fade.animate : { scale: 1, opacity: 1 }}
              transition={
                motionPreset.reduced
                  ? motionPreset.fade.transition
                  : { duration: 0.45, ease: "easeOut" }
              }
            >
              <div className="orbit-line orbit-line--one" /><div className="orbit-line orbit-line--two" />
              <div className="orbit-core"><Progress type="circle" percent={progress} size={174} strokeColor="#00B86A" trailColor="rgba(255,255,255,.08)" strokeWidth={5} format={(value) => <span className="ring-label"><b>{value}%</b><small>نمونهٔ پیشرفت</small></span>} /></div>
              <div className="orbit-chip orbit-chip--top"><ThunderboltOutlined /> امروز · ۱ اقدام</div>
              <div className="orbit-chip orbit-chip--bottom"><CheckOutlined /> مسیر روشن</div>
            </motion.div>
          )}
          {direction === "coach" && (
            <motion.div
              className="coach-art"
              initial={motionPreset.reduced ? motionPreset.fade.initial : { x: 12, opacity: 0 }}
              animate={motionPreset.reduced ? motionPreset.fade.animate : { x: 0, opacity: 1 }}
              transition={
                motionPreset.reduced ? motionPreset.fade.transition : { duration: 0.35 }
              }
            >
              <Card className="coach-note-card" bordered={false}>
                <div className="coach-note-head"><Avatar style={{ background: "#00B86A", color: "#06130d" }}>م</Avatar><div><strong>یادداشت مربی</strong><small>نمونهٔ نمایشی · ۲ دقیقه پیش</small></div><Badge status="processing" /></div>
                <p>«حرکت را کنترل‌شده اجرا کن؛ اگر خستگی داشتی، بازخوردت را ثبت کن.»</p>
                <div className="coach-note-foot"><Tag color="green">بازبینی انسانی</Tag><span>گفت‌وگوی نمونه</span></div>
              </Card>
              <div className="coach-journey"><span className="journey-line" /><div className="journey-step is-done"><i>✓</i><span><b>ارزیابی</b><small>دادهٔ نمونه</small></span></div><div className="journey-step is-current"><i>2</i><span><b>بازبینی مربی</b><small>پیش از انتشار</small></span></div><div className="journey-step"><i>3</i><span><b>برنامهٔ عضو</b><small>بعد از تأیید</small></span></div></div>
            </motion.div>
          )}
          {direction === "precision" && (
            <motion.div
              className="precision-art"
              initial={motionPreset.reduced ? motionPreset.fade.initial : { y: 10, opacity: 0 }}
              animate={motionPreset.reduced ? motionPreset.fade.animate : { y: 0, opacity: 1 }}
              transition={
                motionPreset.reduced ? motionPreset.fade.transition : { duration: 0.35 }
              }
            >
              <div className="precision-card precision-card--large"><div className="precision-card-heading"><span>خلاصهٔ هفته</span><Tag color="cyan">نمونه</Tag></div><div className="precision-stats"><Statistic title="جلسهٔ برنامه‌ریزی‌شده" value={4} suffix="جلسه" /><Statistic title="بازخورد ثبت‌شده" value={3} suffix="مورد" /></div><div className="mini-bars" aria-label="نمودار تزئینی دادهٔ نمونه">{[36, 55, 44, 74, 60, 86, 68].map((height, index) => <span key={index} style={{ height: `${height}%` } as CSSProperties} />)}</div><div className="precision-axis"><span>شنبه</span><span>دوشنبه</span><span>چهارشنبه</span><span>جمعه</span></div></div>
              <div className="precision-chip"><span className="chip-pulse" /> دادهٔ نمایشی · بدون اتصال</div>
            </motion.div>
          )}
        </div>
      </section>

      <section className="landing-feature-row" aria-label="نمونهٔ بخش‌های محصول">
        <FeatureTile icon={<CalendarOutlined />} title="برنامهٔ امروز" text="اقدام بعدی عضو، واضح و نزدیک." onClick={() => onScreen("member")} />
        <FeatureTile icon={<FileSearchOutlined />} title="بازبینی برنامه" text="پیش‌نویس از نسخهٔ تأییدشده جداست." onClick={() => onScreen("studio")} />
        <FeatureTile icon={<BarChartOutlined />} title="پیشرفت قابل پیگیری" text="فقط دادهٔ معتبر؛ وضعیت نمونه برچسب دارد." onClick={onMessage} />
      </section>
    </div>
  );
}

function FeatureTile({ icon, title, text, onClick }: { icon: ReactNode; title: string; text: string; onClick: () => void }) {
  const motionPreset = useMotionPreset();
  return (
    <motion.div
      whileHover={
        motionPreset.hover.whileHover
          ? { ...motionPreset.hover.whileHover, transition: { duration: 0.15 } }
          : undefined
      }
    >
      <button className="feature-tile" type="button" onClick={onClick}>
        <span className="feature-icon">{icon}</span><span><strong>{title}</strong><small>{text}</small></span><ArrowLeftOutlined className="feature-arrow" />
      </button>
    </motion.div>
  );
}

type MemberPreviewProps = {
  direction: Direction;
  activeTab: string;
  onTab: (tab: string) => void;
  onProgram: () => void;
  onQr: () => void;
  onMessage: () => void;
};

function MemberPreview({ direction, activeTab, onTab, onProgram, onQr, onMessage }: MemberPreviewProps) {
  const memberNav = [
    { label: "خانه", icon: <HomeOutlined /> },
    { label: "برنامه", icon: <ThunderboltOutlined /> },
    { label: "کلاس‌ها", icon: <CalendarOutlined /> },
    { label: "پروفایل", icon: <UserOutlined /> },
  ];
  return (
    <div className={`member-workspace member-workspace--${direction}`}>
      <div className="screen-intro">
        <Tag color="green">عضو · نمای موبایل</Tag>
        <h2>{direction === "coach" ? "همراهی در دل تجربه" : direction === "precision" ? "خانهٔ عضو؛ داده در جای درست" : "امروز، فقط قدم بعدی"}</h2>
        <p>نمای مرورگر، فقط برای مقایسهٔ UI است؛ مبنای پلتفرم عضو همچنان Android/Flutter است.</p>
      </div>
      <div className="phone-frame">
        <div className="phone-status"><span>۹:۴۱</span><span>●●● 5G</span></div>
        <div className="member-app-header">
          <div><small>شنبه · دادهٔ ساختگی</small><h3>سلام، سارا</h3></div>
          <Badge dot color="#00B86A"><Button shape="circle" aria-label="اعلان‌های نمونه" icon={<BellOutlined />} onClick={onMessage} /></Badge>
        </div>
        <Card className="today-card" bordered={false}>
          <div className="today-card-top"><Tag color="green">برنامهٔ نمونه</Tag><span className="status-label"><span /> وضعیت: تأییدشدهٔ نمایشی</span></div>
          <div className="today-title-row"><div><h4>جلسهٔ قدرت A</h4><p>نسخهٔ نمونه · هیچ داده‌ای ذخیره نمی‌شود</p></div><div className="today-icon"><ThunderboltOutlined /></div></div>
          <div className="today-metrics"><span><b>۵</b><small>تمرینِ نمونه</small></span><span><b>۴۵′</b><small>زمانِ نمونه</small></span><span><b>۱</b><small>یادداشت</small></span></div>
          <Progress percent={direction === "precision" ? 84 : direction === "coach" ? 58 : 72} showInfo={false} strokeColor="#00B86A" trailColor="rgba(255,255,255,.08)" size="small" />
          <Button type="primary" block icon={<PlayCircleOutlined />} onClick={onProgram}>مشاهدهٔ جلسه</Button>
        </Card>
        <div className="member-section-heading"><strong>{direction === "coach" ? "یادداشت مربی" : "حضور و برنامهٔ نزدیک"}</strong><Button type="link" onClick={onMessage}>همه</Button></div>
        {direction === "coach" ? (
          <Card className="member-coach-card" size="small"><div className="member-coach-row"><Avatar style={{ background: "#00B86A", color: "#07130c" }}>م</Avatar><div><strong>بازخورد مربی · نمونه</strong><small>«ریتم را ثابت نگه‌دار و بعد از جلسه بازخورد بده.»</small></div></div></Card>
        ) : (
          <div className="member-shortcuts">
            <Card className="shortcut-card" size="small"><div className="shortcut-icon"><CalendarOutlined /></div><strong>کلاس‌های نزدیک</strong><small>اطلاعات نمونه</small><Button type="link" onClick={onMessage}>مشاهده</Button></Card>
            <Card className="shortcut-card" size="small"><div className="shortcut-icon shortcut-icon--gold"><ScanOutlined /></div><strong>QR حضور</strong><small>بدون اعتبار واقعی</small><Button type="link" onClick={onQr}>پیش‌نمایش</Button></Card>
          </div>
        )}
        {direction === "coach" && <div className="member-shortcuts member-shortcuts--single"><Card className="shortcut-card" size="small"><div className="shortcut-icon shortcut-icon--gold"><ScanOutlined /></div><strong>QR حضور</strong><small>نماد غیرقابل اسکن</small><Button type="link" onClick={onQr}>پیش‌نمایش</Button></Card><Card className="shortcut-card" size="small"><div className="shortcut-icon"><CalendarOutlined /></div><strong>کلاس‌های نزدیک</strong><small>وضعیت نمونه</small><Button type="link" onClick={onMessage}>مشاهده</Button></Card></div>}
        <nav className="member-bottom-nav" aria-label="ناوبری نمونهٔ عضو">
          {memberNav.map((item) => <button key={item.label} type="button" aria-current={activeTab === item.label ? "page" : undefined} className={activeTab === item.label ? "is-active" : ""} onClick={() => { onTab(item.label); onMessage(); }}>{item.icon}<small>{item.label}</small></button>)}
        </nav>
      </div>
    </div>
  );
}

type DemoRow = (typeof demoRows)[number];
type StudioPreviewProps = {
  direction: Direction;
  page: string;
  onPage: (page: string) => void;
  filter: string;
  onFilter: (filter: string) => void;
  query: string;
  onQuery: (query: string) => void;
  rows: DemoRow[];
  onCase: () => void;
  onMessage: () => void;
};

function StudioPreview({ direction, page, onPage, filter, onFilter, query, onQuery, rows, onCase, onMessage }: StudioPreviewProps) {
  const title = page === "صف کار" ? "سلام، مربی" : page;
  return (
    <div className={`studio-workspace studio-workspace--${direction}`}>
      <aside className="studio-sidebar">
        <div className="studio-brand"><span className="product-mark">MP</span><span><strong>MP STUDIO</strong><small>پنل مربی / مدیر · نمونه</small></span></div>
        <div className="studio-nav-label">فضای کار</div>
        <nav aria-label="ناوبری Studio">
          {studioNav.map((item) => <button key={item.label} type="button" className={page === item.label ? "is-active" : ""} onClick={() => onPage(item.label)}>{item.icon}<span>{item.label}</span>{page === item.label && <span className="studio-active-dot" />}</button>)}
        </nav>
        <div className="studio-role"><Avatar size={34} style={{ background: "rgba(0,184,106,.18)", color: "#34D399" }}>م</Avatar><div><strong>مربی نمونه</strong><small>دادهٔ غیرواقعی</small></div><MenuOutlined /></div>
      </aside>
      <section className="studio-main">
        <header className="studio-topbar">
          <div className="studio-crumb">Studio <span>/</span> {page}</div>
          <div className="studio-tools"><Input aria-label="جست‌وجوی نمونه" placeholder="جست‌وجوی عضو یا برنامه" prefix={<SearchOutlined />} value={query} onChange={(event) => onQuery(event.target.value)} /><Button shape="circle" aria-label="اعلان‌ها" icon={<BellOutlined />} onClick={onMessage} /><Avatar size={34} style={{ background: "#23352d", color: "#b5f4d2" }}>م</Avatar></div>
        </header>
        <div className="studio-title-row"><div><div className="studio-title-kicker"><span className="status-dot" /> WORKSPACE · DEMO</div><h2>{title}</h2><p>{direction === "coach" ? "اول صف کار؛ بعد پروندهٔ عضو و تصمیم مربی." : direction === "precision" ? "وضعیت‌ها، فیلترها و اقدام بعدی در یک نمای فشرده." : "از صف کار تا جزئیات؛ هر اقدام با مرز مشخص."}</p></div><Button type="primary" icon={<PlusOutlined />} onClick={onMessage}>مورد تازه · نمایشی</Button></div>
        <div className="studio-kpis">
          <Kpi label="نیازمند بازبینی" value="۰۷" hint="عدد ساختگی" icon={<FileSearchOutlined />} />
          <Kpi label="پیام‌های خوانده‌نشده" value="۰۳" hint="عدد ساختگی" icon={<BellOutlined />} />
          <Kpi label="جلسه‌های امروز" value="۱۲" hint="عدد ساختگی" icon={<CalendarOutlined />} />
          <Kpi label="موارد نیازمند داده" value="۰۲" hint="عدد ساختگی" icon={<ClockCircleOutlined />} />
        </div>
        <Card className="queue-card" bordered={false}>
          <div className="queue-heading"><div><h3>{direction === "coach" ? "صف بررسی مربی" : "کارهای اخیر"}</h3><small>همهٔ ردیف‌ها نمونه‌اند؛ هیچ عضو واقعی وجود ندارد.</small></div><Tag color="gold">فقط خواندنی</Tag></div>
          <div className="queue-controls">
            <Segmented
              aria-label="فیلتر ردیف‌های نمایشی"
              value={filter}
              options={["همه", "نیازمند بازبینی", "نیازمند تکمیل"]}
              onChange={(value) => onFilter(String(value))}
            />
            <Button icon={<ArrowLeftOutlined />} onClick={onMessage}>نمایش گزارش</Button>
          </div>
          <div className="queue-list">
            {rows.length === 0 ? <div className="empty-state"><SearchOutlined /><strong>نتیجه‌ای در نمونه پیدا نشد</strong><small>عبارت جست‌وجو یا فیلتر را تغییر بده.</small></div> : rows.map((row) => (
              <div className="queue-row" key={row.name}>
                <Avatar style={{ background: row.tone === "gold" ? "rgba(255,215,0,.14)" : row.tone === "cyan" ? "rgba(56,189,248,.14)" : "rgba(0,184,106,.16)", color: row.tone === "gold" ? "#FDE68A" : row.tone === "cyan" ? "#7DD3FC" : "#34D399" }}>{row.initials}</Avatar>
                <div className="queue-person"><strong>{row.name}</strong><small>{row.work}</small></div>
                <Tag color={row.tone}>{row.status}</Tag>
                <Button onClick={onCase}>بازکردن پرونده</Button>
              </div>
            ))}
          </div>
          <div className="queue-foot"><span><span className="status-dot" /> نوشتن واقعی غیرفعال است</span><Button type="link" onClick={onMessage}>راهنمای وضعیت‌ها</Button></div>
        </Card>
      </section>
    </div>
  );
}

function Kpi({ label, value, hint, icon }: { label: string; value: string; hint: string; icon: ReactNode }) {
  return <Card className="kpi-card" bordered={false}><div className="kpi-top"><span>{icon}</span><small>{hint}</small></div><strong>{value}</strong><span>{label}</span></Card>;
}
