import os
import re

html_path = r"C:\Users\saidm\OneDrive\Desktop\SHIFTSYNC\shiftsync_core_system.html"
backup_path = r"C:\Users\saidm\OneDrive\Desktop\SHIFTSYNC\shiftsync_core_system.html.bak"

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Make backup
with open(backup_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Original length: {len(content)}")

# 1. Update Tailwind config colors
old_tailwind_colors = """            brand: {
              50: '#f0f4f8',
              100: '#d9e2ec',
              500: '#1e293b',
              600: '#0f172a',
              700: '#020617',
            }"""

new_tailwind_colors = """            brand: {
              50: '#fef2f2',
              100: '#fee2e2',
              500: '#C8102E',
              600: '#A60C25',
              700: '#7F091C',
            },
            kq: {
              red: '#C8102E',
              darkred: '#990B22',
              green: '#007A3D',
              darkgreen: '#00582B',
              black: '#111827',
              gold: '#D97706',
            }"""

content = content.replace(old_tailwind_colors, new_tailwind_colors)

# 2. Update CSS styles (body, sidebar-active, badges)
old_styles = """.sidebar-active { background-color: #f1f5f9; color: #0f172a; font-weight: 600; border-left: 3px solid #0f172a; }
    .badge-critical { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    .badge-high { background-color: #ffedd5; color: #c2410c; border: 1px solid #fdba74; }
    .badge-medium { background-color: #fef9c3; color: #a16207; border: 1px solid #fde047; }
    .badge-low { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .badge-completed { background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; }
    .badge-pending { background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
    .badge-inprogress { background-color: #fef3c7; color: #b45309; border: 1px solid #fcd34d; }"""

new_styles = """.sidebar-active { background-color: #fef2f2; color: #C8102E; font-weight: 700; border-left: 4px solid #C8102E; }
    .kenya-flag-ribbon {
      background: linear-gradient(to right, #111827 0%, #111827 31%, #ffffff 31%, #ffffff 34%, #C8102E 34%, #C8102E 66%, #ffffff 66%, #ffffff 69%, #007A3D 69%, #007A3D 100%);
    }
    .kq-card-accent {
      border-top: 3px solid #C8102E;
    }
    .badge-critical { background-color: #fee2e2; color: #C8102E; border: 1px solid #fca5a5; font-weight: 700; }
    .badge-high { background-color: #ffedd5; color: #c2410c; border: 1px solid #fdba74; font-weight: 700; }
    .badge-medium { background-color: #fef9c3; color: #854d0e; border: 1px solid #fde047; font-weight: 600; }
    .badge-low { background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }
    .badge-completed { background-color: #ecfdf5; color: #007A3D; border: 1px solid #6ee7b7; font-weight: 700; }
    .badge-pending { background-color: #f8fafc; color: #475569; border: 1px solid #cbd5e1; }
    .badge-inprogress { background-color: #fffbeb; color: #b45309; border: 1px solid #fcd34d; font-weight: 600; }"""

content = content.replace(old_styles, new_styles)

# 3. Update Title & Favicon/Header branding
content = content.replace("<title>ShiftSync - Core System Mockup</title>", "<title>ShiftSync | Kenya Airways Operations Handover System</title>")

# 4. Update Login Screen with Kenya Airways / Kenyan Flag styling
old_login_header = """      <div class="text-center space-y-2">
        <div class="w-12 h-12 rounded-xl bg-slate-900 text-white flex items-center justify-center mx-auto text-xl font-bold shadow-md">
          ☵
        </div>
        <h2 class="text-2xl font-bold tracking-tight text-slate-900">Shift Handover System</h2>
        <p class="text-xs text-slate-500 font-medium">ShiftSync Operational Portal</p>
      </div>"""

new_login_header = """      <!-- Kenyan Flag Accent Ribbon on Login Card -->
      <div class="h-1.5 w-full kenya-flag-ribbon rounded-t-xl -mt-8 -mx-8 mb-6" style="width: calc(100% + 4rem);"></div>
      <div class="text-center space-y-2">
        <div class="w-14 h-14 rounded-2xl bg-[#C8102E] text-white flex items-center justify-center mx-auto text-2xl font-bold shadow-lg border-2 border-red-700">
          ✈
        </div>
        <div>
          <div class="flex items-center justify-center space-x-1.5">
            <span class="text-xs font-bold uppercase tracking-widest text-[#C8102E]">KENYA AIRWAYS</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded bg-emerald-100 text-[#007A3D] font-bold">KQ</span>
          </div>
          <h2 class="text-2xl font-black tracking-tight text-slate-900">ShiftSync Operations</h2>
          <p class="text-xs text-slate-500 font-medium">Flight, Ramp & Engineering Handover Portal • JKIA</p>
        </div>
      </div>"""

content = content.replace(old_login_header, new_login_header)

# Replace login button
content = content.replace(
    """<button type="submit" class="w-full py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold shadow transition">
          Login to ShiftSync
        </button>""",
    """<button type="submit" class="w-full py-2.5 rounded-lg bg-[#C8102E] hover:bg-[#A60C25] text-white text-sm font-bold shadow-md hover:shadow-lg transition">
          Sign In to Kenya Airways ShiftSync
        </button>"""
)

# 5. Add Kenyan Flag ribbon to Main Application Shell
old_header_tag = """  <div id="screen-app" class="min-h-screen flex flex-col hidden">
    
    <!-- Top Bar -->
    <header class="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-6 sticky top-0 z-40">"""

new_header_tag = """  <div id="screen-app" class="min-h-screen flex flex-col hidden">
    <!-- Kenyan National Flag Accent Strip (Black - White - Red - White - Green) -->
    <div class="h-1.5 w-full kenya-flag-ribbon sticky top-0 z-50"></div>

    <!-- Top Bar -->
    <header class="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-6 sticky top-1.5 z-40 shadow-xs">"""

content = content.replace(old_header_tag, new_header_tag)

# 6. Update Top Bar Brand & Facility Tag
old_brand_logo = """        <div class="flex items-center space-x-2.5">
          <div class="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center font-bold text-sm">
            ☵
          </div>
          <span class="font-bold text-lg tracking-tight text-slate-900">SHIFT SYSTEM</span>
        </div>
        <span class="hidden sm:inline-block text-slate-300">|</span>
        <span class="hidden sm:inline-block text-xs font-medium text-slate-500">Facility: Nairobi Sector 2 Operations</span>"""

new_brand_logo = """        <div class="flex items-center space-x-2.5">
          <div class="w-9 h-9 rounded-xl bg-[#C8102E] text-white flex items-center justify-center font-black text-lg shadow-sm border border-red-700">
            ✈
          </div>
          <div>
            <div class="flex items-center space-x-1.5">
              <span class="font-black text-base tracking-tight text-slate-900">ShiftSync</span>
              <span class="px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-red-100 text-[#C8102E]">KQ OPS</span>
            </div>
            <p class="text-[10px] text-slate-500 font-semibold tracking-wide">KENYA AIRWAYS • THE PRIDE OF AFRICA</p>
          </div>
        </div>
        <span class="hidden lg:inline-block text-slate-300">|</span>
        <div class="hidden lg:flex items-center space-x-2 text-xs text-slate-600">
          <span class="w-2 h-2 rounded-full bg-[#007A3D]"></span>
          <span class="font-medium">Jomo Kenyatta International Airport (JKIA) • Terminal 1 & Ramp Operations</span>
        </div>"""

content = content.replace(old_brand_logo, new_brand_logo)

# 7. Update Primary Action Buttons from bg-slate-900 to Kenya Airways Red bg-[#C8102E]
# Replace specific prominent buttons
buttons_to_replace = [
    # Dashboard + Create Handover button
    ('px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow transition">\n                + Create Handover Report',
     'px-3.5 py-2 rounded-lg bg-[#C8102E] hover:bg-[#A60C25] text-white text-xs font-bold shadow-sm transition">\n                + Create Handover Report'),
    # Shift Management + Create New Shift
    ('px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow transition">\n              + Create New Shift',
     'px-3.5 py-2 rounded-lg bg-[#C8102E] hover:bg-[#A60C25] text-white text-xs font-bold shadow-sm transition">\n              + Create New Shift'),
    # Handover Reports + New Handover Report
    ('px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow transition">\n              + New Handover Report',
     'px-3.5 py-2 rounded-lg bg-[#C8102E] hover:bg-[#A60C25] text-white text-xs font-bold shadow-sm transition">\n              + New Handover Report'),
    # Task Tracking + Add New Task
    ('px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow transition">\n              + Add New Task',
     'px-3.5 py-2 rounded-lg bg-[#C8102E] hover:bg-[#A60C25] text-white text-xs font-bold shadow-sm transition">\n              + Add New Task'),
    # User Management + Add New User
    ('px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow transition">\n              + Add New User',
     'px-3.5 py-2 rounded-lg bg-[#C8102E] hover:bg-[#A60C25] text-white text-xs font-bold shadow-sm transition">\n              + Add New User'),
    # Submit Handover Report button
    ('px-5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-white shadow transition">\n                Submit Handover Report',
     'px-5 py-2 rounded-lg bg-[#007A3D] hover:bg-[#00582B] text-xs font-bold text-white shadow-md transition">\n                ✔ Submit Handover Report (Formal Sign-off)'),
    # Review & Acknowledge button
    ('px-2.5 py-1 rounded bg-slate-900 text-white font-semibold hover:bg-slate-800">Review & Acknowledge</button>',
     'px-2.5 py-1 rounded bg-[#C8102E] text-white font-bold hover:bg-[#A60C25] shadow-xs">Review & Acknowledge</button>'),
    # NLP Run button
    ('px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow transition">\n                  <span id="nlp-spinner" class="hidden animate-spin">⟳</span>\n                  <span>✨ Run ShiftSync NLP Extraction</span>',
     'px-4 py-2 rounded-lg bg-[#C8102E] hover:bg-[#A60C25] text-white text-xs font-bold shadow-md transition">\n                  <span id="nlp-spinner" class="hidden animate-spin">⟳</span>\n                  <span>✨ Run ShiftSync NLP Extraction</span>'),
    # Modal Save Buttons
    ('px-4 py-2 rounded-lg bg-slate-900 text-white font-semibold hover:bg-slate-800 shadow">Save User</button>',
     'px-4 py-2 rounded-lg bg-[#C8102E] text-white font-bold hover:bg-[#A60C25] shadow">Save User</button>'),
    ('px-4 py-2 rounded-lg bg-slate-900 text-white font-semibold hover:bg-slate-800 shadow">Save Shift</button>',
     'px-4 py-2 rounded-lg bg-[#C8102E] text-white font-bold hover:bg-[#A60C25] shadow">Save Shift</button>'),
    ('px-4 py-2 rounded-lg bg-slate-900 text-white font-semibold hover:bg-slate-800 shadow">Save Task</button>',
     'px-4 py-2 rounded-lg bg-[#C8102E] text-white font-bold hover:bg-[#A60C25] shadow">Save Task</button>')
]

for old_btn, new_btn in buttons_to_replace:
    content = content.replace(old_btn, new_btn)

# 8. Update Sidebar Active Shift Widget to KQ styling
old_sidebar_widget = """        <!-- Current Shift Info Widget in Sidebar -->
        <div class="p-3 rounded-xl bg-slate-100 border border-slate-200 text-xs">
          <div class="flex items-center justify-between mb-1">
            <span class="text-[11px] font-semibold text-slate-500 uppercase">Active Shift</span>
            <span class="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">ACTIVE</span>
          </div>
          <p class="font-bold text-slate-900">Day Shift (Crew A)</p>
          <p class="text-[11px] text-slate-600 font-mono mt-0.5">06:00 - 18:00</p>
          <p class="text-[11px] text-slate-500 mt-1">Supervisor: Sarah Jenkins</p>
        </div>"""

new_sidebar_widget = """        <!-- Current Shift Info Widget in Sidebar (Kenya Airways Theme) -->
        <div class="p-3.5 rounded-xl bg-slate-900 text-white border-t-2 border-[#C8102E] shadow-sm text-xs space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-300">KQ ACTIVE SHIFT</span>
            <span class="px-1.5 py-0.5 rounded bg-[#007A3D] text-white text-[9px] font-extrabold tracking-wide">LIVE</span>
          </div>
          <p class="font-bold text-sm text-white">JKIA Ramp & Line Ops A</p>
          <div class="flex items-center justify-between text-[11px] text-slate-300 font-mono">
            <span>06:00 - 18:00 EAT</span>
            <span class="text-[#f87171] font-bold">Crew A</span>
          </div>
          <p class="text-[10px] text-slate-400 pt-1 border-t border-slate-800">Lead: Capt. / Supv. Sarah Jenkins</p>
        </div>"""

content = content.replace(old_sidebar_widget, new_sidebar_widget)

# 9. Update Dashboard Active Shift Banner
old_dash_banner = """            <div>
              <div class="flex items-center space-x-2 mb-1">
                <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">CURRENT ACTIVE SHIFT</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-100 text-emerald-800">ACTIVE</span>
              </div>
              <h2 class="text-lg font-bold text-slate-900">Day Shift (Crew A)</h2>
              <p class="text-xs text-slate-500 font-mono mt-0.5">25 October 2026 • 06:00 - 18:00</p>
            </div>"""

new_dash_banner = """            <div>
              <div class="flex items-center space-x-2 mb-1">
                <span class="text-[11px] font-bold text-[#C8102E] uppercase tracking-wider">KENYA AIRWAYS FLIGHT & GROUND SHIFT</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-extrabold bg-[#007A3D] text-white">ACTIVE ROTATION</span>
              </div>
              <h2 class="text-lg font-black text-slate-900">JKIA Terminal 1 & Ramp Operations (Crew A)</h2>
              <p class="text-xs text-slate-500 font-mono mt-0.5">Nairobi Hub (HKJK) • 06:00 - 18:00 EAT</p>
            </div>"""

content = content.replace(old_dash_banner, new_dash_banner)

# Write updated content
with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Updated successfully! New length: {len(content)}")
