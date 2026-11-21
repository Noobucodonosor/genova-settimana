"""Shared vanilla CSS bundle replacing external tailwindcss.min.js (ADR-0002 / TASK-CSS-01)."""

VANILLA_CSS = r"""
:root {
  --background: #0f172a;
  --foreground: #f8fafc;
  --card: #1e293b;
  --content: #0b1220;
  --border: #334155;
  --primary: #f59e0b;
  --primary-foreground: #0f172a;
  --muted-foreground: #94a3b8;
}
*, *::before, *::after { box-sizing: border-box; }
html { line-height: 1.5; -webkit-text-size-adjust: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body { margin: 0; font-size: 14px; background: var(--background); color: var(--foreground); -webkit-font-smoothing: antialiased; }
h1, h2, h3, h4, p { margin: 0; }
button, input, select { font: inherit; color: inherit; }
button { background: transparent; border: 0; cursor: pointer; }
a { color: inherit; text-decoration: none; }
.antialiased { -webkit-font-smoothing: antialiased; }

/* Display & Layout */
.hidden { display: none !important; }
.block { display: block; }
.inline-block { display: inline-block; }
.flex { display: flex; }
.inline-flex { display: inline-flex; }
.grid { display: grid; }
.flex-col { flex-direction: column; }
.flex-wrap { flex-wrap: wrap; }
.flex-1 { flex: 1 1 0%; }
.shrink-0 { flex-shrink: 0; }
.items-start { align-items: flex-start; }
.items-center { align-items: center; }
.items-baseline { align-items: baseline; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }
.justify-end { justify-content: flex-end; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-7 { grid-template-columns: repeat(7, minmax(0, 1fr)); }
.col-span-2 { grid-column: span 2 / span 2; }
.gap-1 { gap: 0.25rem; }
.gap-1\.5 { gap: 0.375rem; }
.gap-2 { gap: 0.5rem; }
.gap-2\.5 { gap: 0.625rem; }
.gap-3 { gap: 0.75rem; }
.gap-3\.5 { gap: 0.875rem; }
.gap-4 { gap: 1rem; }
.space-y-0\.5 > :not([hidden]) ~ :not([hidden]) { margin-top: 0.125rem; }
.space-y-1 > :not([hidden]) ~ :not([hidden]) { margin-top: 0.25rem; }
.space-y-1\.5 > :not([hidden]) ~ :not([hidden]) { margin-top: 0.375rem; }
.space-y-2 > :not([hidden]) ~ :not([hidden]) { margin-top: 0.5rem; }
.space-y-2\.5 > :not([hidden]) ~ :not([hidden]) { margin-top: 0.625rem; }
.space-y-3 > :not([hidden]) ~ :not([hidden]) { margin-top: 0.75rem; }
.space-y-4 > :not([hidden]) ~ :not([hidden]) { margin-top: 1rem; }
.space-y-5 > :not([hidden]) ~ :not([hidden]) { margin-top: 1.25rem; }

/* Positioning */
.relative { position: relative; }
.absolute { position: absolute; }
.fixed { position: fixed; }
.sticky { position: sticky; }
.inset-0 { inset: 0; }
.top-0 { top: 0; }
.right-0 { right: 0; }
.z-20 { z-index: 20; }
.z-30 { z-index: 30; }
.z-40 { z-index: 40; }
.z-50 { z-index: 50; }

/* Sizing */
.w-full { width: 100%; }
.w-10 { width: 2.5rem; }
.w-8 { width: 2rem; }
.w-7 { width: 1.75rem; }
.w-5 { width: 1.25rem; }
.w-4 { width: 1rem; }
.w-3 { width: 0.75rem; }
.w-2\.5 { width: 0.625rem; }
.h-full { height: 100%; }
.h-10 { height: 2.5rem; }
.h-8 { height: 2rem; }
.h-7 { height: 1.75rem; }
.h-5 { height: 1.25rem; }
.h-4 { height: 1rem; }
.h-3 { height: 0.75rem; }
.h-2\.5 { height: 0.625rem; }
.h-\[390px\] { height: 390px; }
.min-h-screen { min-height: 100vh; }
.min-h-\[94px\] { min-height: 94px; }
.min-w-\[64px\] { min-width: 64px; }
.min-w-\[140px\] { min-width: 140px; }
.max-w-\[1440px\] { max-width: 1440px; }
.max-w-\[1600px\] { max-width: 1600px; }
.max-w-\[500px\] { max-width: 500px; }
.max-w-\[250px\] { max-width: 250px; }
.max-w-\[65\%\] { max-width: 65%; }

/* Spacing */
.mx-auto { margin-left: auto; margin-right: auto; }
.ml-auto { margin-left: auto; }
.ml-1 { margin-left: 0.25rem; }
.mr-1 { margin-right: 0.25rem; }
.mt-0\.5 { margin-top: 0.125rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-1\.5 { margin-top: 0.375rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.p-0\.5 { padding: 0.125rem; }
.p-1 { padding: 0.25rem; }
.p-2 { padding: 0.5rem; }
.p-2\.5 { padding: 0.625rem; }
.p-3 { padding: 0.75rem; }
.p-3\.5 { padding: 0.875rem; }
.p-4 { padding: 1rem; }
.p-6 { padding: 1.5rem; }
.px-1\.5 { padding-left: 0.375rem; padding-right: 0.375rem; }
.px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
.px-2\.5 { padding-left: 0.625rem; padding-right: 0.625rem; }
.px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
.px-3\.5 { padding-left: 0.875rem; padding-right: 0.875rem; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }
.px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
.py-0\.2 { padding-top: 0.05rem; padding-bottom: 0.05rem; }
.py-0\.5 { padding-top: 0.125rem; padding-bottom: 0.125rem; }
.py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
.py-1\.5 { padding-top: 0.375rem; padding-bottom: 0.375rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
.py-2\.5 { padding-top: 0.625rem; padding-bottom: 0.625rem; }
.py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }
.pt-1 { padding-top: 0.25rem; }
.pt-1\.5 { padding-top: 0.375rem; }
.pt-2 { padding-top: 0.5rem; }
.pt-3 { padding-top: 0.75rem; }
.pb-0\.5 { padding-bottom: 0.125rem; }
.pb-1 { padding-bottom: 0.25rem; }
.pb-3 { padding-bottom: 0.75rem; }
.pb-6 { padding-bottom: 1.5rem; }

/* Typography */
.text-\[11px\] { font-size: 11px; line-height: 1.35; }
.text-xs { font-size: 0.75rem; line-height: 1rem; }
.text-sm { font-size: 0.875rem; line-height: 1.25rem; }
.text-base { font-size: 1rem; line-height: 1.5rem; }
.text-lg { font-size: 1.125rem; line-height: 1.75rem; }
.text-xl { font-size: 1.25rem; line-height: 1.75rem; }
.text-2xl { font-size: 1.5rem; line-height: 2rem; }
.font-normal { font-weight: 400; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }
.font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
.uppercase { text-transform: uppercase; }
.tracking-tight { letter-spacing: -0.025em; }
.tracking-wide { letter-spacing: 0.025em; }
.tracking-wider { letter-spacing: 0.05em; }
.leading-tight { line-height: 1.25; }
.leading-snug { line-height: 1.375; }
.leading-relaxed { line-height: 1.625; }
.text-center { text-align: center; }
.underline { text-decoration: underline; }
.whitespace-nowrap { white-space: nowrap; }
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* Colors */
.bg-transparent { background-color: transparent; }
.bg-\[var\(--background\)\] { background-color: var(--background); }
.bg-\[var\(--background\)\]\/95 { background-color: rgba(15, 23, 42, 0.95); }
.bg-\[var\(--card\)\] { background-color: var(--card); }
.bg-\[var\(--card\)\]\/95 { background-color: rgba(30, 41, 59, 0.95); }
.bg-\[var\(--content\)\] { background-color: var(--content); }
.bg-\[var\(--content\)\]\/30 { background-color: rgba(11, 18, 32, 0.3); }
.bg-\[var\(--content\)\]\/50 { background-color: rgba(11, 18, 32, 0.5); }
.bg-\[var\(--content\)\]\/70 { background-color: rgba(11, 18, 32, 0.7); }
.bg-\[var\(--primary\)\] { background-color: var(--primary); }
.bg-\[var\(--primary\)\]\/10 { background-color: rgba(245, 158, 11, 0.1); }
.bg-amber-500 { background-color: #f59e0b; }
.bg-amber-500\/10 { background-color: rgba(245, 158, 11, 0.1); }
.bg-amber-500\/15 { background-color: rgba(245, 158, 11, 0.15); }
.bg-amber-500\/20 { background-color: rgba(245, 158, 11, 0.2); }
.bg-emerald-500\/10 { background-color: rgba(16, 185, 129, 0.1); }
.bg-emerald-500\/15 { background-color: rgba(16, 185, 129, 0.15); }
.bg-emerald-500\/20 { background-color: rgba(16, 185, 129, 0.2); }
.bg-emerald-600 { background-color: #059669; }
.bg-emerald-600\/20 { background-color: rgba(5, 150, 105, 0.2); }
.bg-blue-500\/10 { background-color: rgba(59, 130, 246, 0.1); }
.bg-red-500\/15 { background-color: rgba(239, 68, 68, 0.15); }
.bg-red-500\/20 { background-color: rgba(239, 68, 68, 0.2); }
.bg-slate-700 { background-color: #334155; }
.bg-black\/40 { background-color: rgba(0, 0, 0, 0.4); }

.text-\[var\(--foreground\)\] { color: var(--foreground); }
.text-\[var\(--muted-foreground\)\] { color: var(--muted-foreground); }
.text-\[var\(--primary\)\] { color: var(--primary); }
.text-\[var\(--primary-foreground\)\] { color: var(--primary-foreground); }
.text-white { color: #ffffff; }
.text-slate-950 { color: #020617; }
.text-slate-300 { color: #cbd5e1; }
.text-slate-400 { color: #94a3b8; }
.text-amber-400 { color: #fbbf24; }
.text-amber-500 { color: #f59e0b; }
.text-amber-600 { color: #d97706; }
.text-emerald-300 { color: #6ee7b7; }
.text-emerald-400 { color: #34d399; }
.text-emerald-500 { color: #10b981; }
.text-emerald-600 { color: #059669; }
.text-blue-400 { color: #60a5fa; }
.text-blue-500 { color: #3b82f6; }
.text-red-300 { color: #fca5a5; }
.text-red-400 { color: #f87171; }
.placeholder\:text-\[var\(--muted-foreground\)\]::placeholder { color: var(--muted-foreground); }
.accent-\[var\(--primary\)\] { accent-color: var(--primary); }
.accent-amber-500 { accent-color: #f59e0b; }
.accent-emerald-500 { accent-color: #10b981; }

/* Borders, Radius, Shadows */
.border { border: 1px solid var(--border); }
.border-2 { border: 2px solid var(--border); }
.border-t { border-top: 1px solid var(--border); }
.border-b { border-bottom: 1px solid var(--border); }
.border-l { border-left: 1px solid var(--border); }
.border-r { border-right: 1px solid var(--border); }
.border-\[var\(--border\)\] { border-color: var(--border); }
.border-\[var\(--primary\)\] { border-color: var(--primary); }
.border-amber-400 { border-color: #fbbf24; }
.border-amber-500 { border-color: #f59e0b; }
.border-amber-500\/30 { border-color: rgba(245, 158, 11, 0.3); }
.border-amber-500\/40 { border-color: rgba(245, 158, 11, 0.4); }
.border-amber-500\/50 { border-color: rgba(245, 158, 11, 0.5); }
.border-emerald-500\/30 { border-color: rgba(16, 185, 129, 0.3); }
.border-emerald-500\/40 { border-color: rgba(16, 185, 129, 0.4); }
.border-blue-500\/25 { border-color: rgba(59, 130, 246, 0.25); }
.border-red-500\/30 { border-color: rgba(239, 68, 68, 0.3); }
.last\:border-0:last-child { border-width: 0; }
.rounded { border-radius: 0.25rem; }
.rounded-md { border-radius: 0.375rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }
.rounded-2xl { border-radius: 1rem; }
.rounded-full { border-radius: 9999px; }
.ring-1 { box-shadow: 0 0 0 1px var(--primary); }
.ring-2 { box-shadow: 0 0 0 2px var(--primary); }
.ring-\[var\(--primary\)\] { box-shadow: 0 0 0 2px var(--primary); }
.ring-amber-400 { box-shadow: 0 0 0 2px #fbbf24; }
.shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.25); }
.shadow-md { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); }
.shadow-lg { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.35); }
.shadow-2xl { box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }

/* Misc & Interaction */
.opacity-40 { opacity: 0.4; }
.overflow-hidden { overflow: hidden; }
.overflow-x-auto { overflow-x: auto; }
.overflow-y-auto { overflow-y: auto; }
.backdrop-blur { backdrop-filter: blur(8px); }
.backdrop-blur-xs { backdrop-filter: blur(4px); }
.cursor-pointer { cursor: pointer; }
.cursor-grab { cursor: grab; }
.active\:cursor-grabbing:active { cursor: grabbing; }
.select-none { user-select: none; }
.pointer-events-none { pointer-events: none; }
.transition { transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1); }
.transition-all { transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1); }
.hover\:opacity-90:hover { opacity: 0.9; }
.hover\:opacity-95:hover { opacity: 0.95; }
.hover\:underline:hover { text-decoration: underline; }
.hover\:bg-\[var\(--content\)\]:hover { background-color: var(--content); }
.hover\:bg-\[var\(--content\)\]\/60:hover { background-color: rgba(11, 18, 32, 0.6); }
.hover\:bg-\[var\(--primary\)\]:hover { background-color: var(--primary); }
.hover\:bg-amber-500:hover { background-color: #f59e0b; }
.hover\:bg-emerald-600:hover { background-color: #059669; }
.hover\:bg-red-500:hover { background-color: #ef4444; }
.hover\:border-\[var\(--primary\)\]:hover { border-color: var(--primary); }
.hover\:border-amber-500\/60:hover { border-color: rgba(245, 158, 11, 0.6); }
.hover\:text-\[var\(--foreground\)\]:hover { color: var(--foreground); }
.hover\:text-\[var\(--primary-foreground\)\]:hover { color: var(--primary-foreground); }
.hover\:text-amber-400:hover { color: #fbbf24; }
.hover\:text-slate-950:hover { color: #020617; }
.hover\:text-white:hover { color: #ffffff; }
.focus\:outline-none:focus { outline: none; }
.focus\:border-\[var\(--primary\)\]:focus { border-color: var(--primary); }
.focus\:border-amber-400:focus { border-color: #fbbf24; }

/* Responsive Breakpoints */
@media (min-width: 640px) {
  .sm\:inline { display: inline; }
  .sm\:items-center { align-items: center; }
  .sm\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sm\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .sm\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .sm\:grid-cols-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }
  .sm\:h-\[450px\] { height: 450px; }
  .sm\:text-sm { font-size: 0.875rem; line-height: 1.25rem; }
  .sm\:text-base { font-size: 1rem; line-height: 1.5rem; }
  .sm\:text-lg { font-size: 1.125rem; line-height: 1.75rem; }
}
@media (min-width: 768px) {
  .md\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .md\:grid-cols-12 { grid-template-columns: repeat(12, minmax(0, 1fr)); }
  .md\:col-span-2 { grid-column: span 2 / span 2; }
  .md\:col-span-3 { grid-column: span 3 / span 3; }
  .md\:col-span-4 { grid-column: span 4 / span 4; }
  .md\:col-span-5 { grid-column: span 5 / span 5; }
}
@media (min-width: 1024px) {
  .lg\:grid-cols-7 { grid-template-columns: repeat(7, minmax(0, 1fr)); }
  .lg\:grid-cols-12 { grid-template-columns: repeat(12, minmax(0, 1fr)); }
  .lg\:col-span-4 { grid-column: span 4 / span 4; }
  .lg\:col-span-5 { grid-column: span 5 / span 5; }
  .lg\:col-span-7 { grid-column: span 7 / span 7; }
  .lg\:col-span-8 { grid-column: span 8 / span 8; }
  .lg\:sticky { position: sticky; }
  .lg\:top-\[168px\] { top: 168px; }
}
@media (min-width: 1280px) {
  .xl\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .xl\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .xl\:grid-cols-7 { grid-template-columns: repeat(7, minmax(0, 1fr)); }
}
"""
