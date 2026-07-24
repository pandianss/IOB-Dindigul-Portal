import csv
import json
import os

form_dir = r"C:\Users\sspan\Videos\Form"

# Read iob_logo.json
with open(os.path.join(form_dir, "iob_logo.json"), "r", encoding="utf-8") as f:
    lottie_data = json.load(f)

# Read MCC List.txt
mcc_list = []
with open(os.path.join(form_dir, "MCC List.txt"), "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if 'value="' in line and '</option>' in line:
            val_start = line.find('value="') + 7
            val_end = line.find('"', val_start)
            val = line[val_start:val_end]
            
            text_start = line.find('>') + 1
            text_end = line.find('</option>')
            text = line[text_start:text_end]
            
            if val != "0":
                parts = text.split('-', 1)
                desc = parts[1].strip() if len(parts) > 1 else text.strip()
                mcc_list.append({"code": val, "desc": desc})

# Read branches.csv
branches = {}
with open(os.path.join(form_dir, "branches.csv"), "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        code = row.get("code", "").strip()
        name = row.get("name_en", "").strip()
        if code and name:
            padded = code.zfill(4)
            branches[padded] = {
                "name": name,
                "district": row.get("district", "").strip() or "Dindigul",
                "pincode": row.get("pincode", "").strip()
            }

# Read staff_list.csv
staff_list = {}
with open(os.path.join(form_dir, "staff_list.csv"), "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        roll = row.get("Roll", "").strip()
        name = row.get("Name", "").strip()
        sol = row.get("Branch", "").strip().zfill(4)
        if roll:
            staff_list[roll] = {
                "name": name,
                "sol": sol,
                "designation": row.get("Designation", "").strip()
            }

admin_url = "https://script.google.com/macros/s/AKfycby_RxcPyViFLY_ILWqzxB6jb9RopXU_vZhHbusPdbrj70FcQx6vGcyrAQTTy_gW4goL/exec"

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Indian Overseas Bank - Merchant Services Portal</title>
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js"></script>
<style>
  :root {{
    --iob-blue: #1a3a7a;
    --iob-blue-light: #2550a8;
    --iob-blue-dark: #0d2354;
    --iob-gold: #e8a020;
    --bg: #f0f4ff;
    --card: #ffffff;
    --border: #d0daf0;
    --text: #1a2440;
    --muted: #6b7a99;
    --success: #16a34a;
    --warning: #d97706;
    --error: #dc2626;
    --input-bg: #f8faff;
    --shadow: 0 4px 24px rgba(26,58,122,0.10);
    --shadow-lg: 0 8px 40px rgba(26,58,122,0.16);
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Inter', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }}

  /* ── SPLASH SCREEN ── */
  #splash {{
    position: fixed; inset: 0; z-index: 999;
    background: linear-gradient(135deg, var(--iob-blue-dark) 0%, var(--iob-blue) 60%, var(--iob-blue-light) 100%);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 20px; transition: opacity 0.5s ease, transform 0.5s ease;
  }}
  #splash.hide {{ opacity: 0; pointer-events: none; transform: translateY(-20px); }}
  #lottie-splash {{ width: 140px; height: 140px; }}
  #splash-title {{ color: #fff; font-size: 1.5rem; font-weight: 700; letter-spacing: 0.02em; text-align: center; }}
  #splash-sub {{ color: rgba(255,255,255,0.75); font-size: 0.88rem; }}
  #splash-progress {{ width: 180px; height: 3px; background: rgba(255,255,255,0.2); border-radius: 99px; overflow: hidden; }}
  #splash-bar {{ height: 100%; width: 0%; background: var(--iob-gold); border-radius: 99px; transition: width 0.1s linear; }}

  /* ── HEADER ── */
  header {{
    background: linear-gradient(90deg, var(--iob-blue-dark) 0%, var(--iob-blue) 100%);
    color: #fff; padding: 0 28px;
    display: flex; align-items: center; justify-content: space-between;
    height: 70px; box-shadow: 0 2px 16px rgba(13,35,84,0.25);
    position: sticky; top: 0; z-index: 100;
  }}
  .header-left {{ display: flex; align-items: center; gap: 14px; }}
  .header-logo {{ height: 42px; width: auto; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2)); }}
  .header-title {{ font-size: 1.05rem; font-weight: 600; opacity: 0.95; letter-spacing: 0.01em; }}
  .header-right {{ display: flex; align-items: center; gap: 12px; }}
  .header-lottie {{ width: 44px; height: 44px; }}
  .admin-link {{
    background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25);
    color: #fff; border-radius: 8px; padding: 6px 14px; font-size: 0.8rem;
    font-weight: 600; text-decoration: none; transition: all 0.2s;
  }}
  .admin-link:hover {{ background: rgba(255,255,255,0.3); }}

  /* ── MAIN ── */
  main {{ max-width: 980px; margin: 0 auto; padding: 24px 16px 64px; }}

  /* ── MAIN NAV TABS ── */
  .nav-tabs {{
    display: flex; gap: 10px; margin-bottom: 24px;
    background: #e2e8f0; padding: 5px; border-radius: 14px;
  }}
  .nav-tab-btn {{
    flex: 1; border: none; background: transparent; padding: 12px 16px;
    border-radius: 10px; font-size: 0.9rem; font-weight: 700; cursor: pointer;
    color: var(--muted); transition: all 0.2s; text-align: center;
  }}
  .nav-tab-btn.active {{ background: #fff; color: var(--iob-blue); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}

  /* ── CARDS ── */
  .type-card {{
    background: var(--card); border-radius: 18px; padding: 28px;
    box-shadow: var(--shadow); margin-bottom: 24px; border: 1px solid var(--border);
  }}
  .type-card h2 {{ font-size: 1.2rem; font-weight: 700; color: var(--iob-blue); margin-bottom: 6px; }}
  .type-card p {{ color: var(--muted); font-size: 0.88rem; margin-bottom: 20px; }}
  .type-options {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
  .type-btn {{
    border: 2px solid var(--border); background: var(--input-bg);
    border-radius: 14px; padding: 20px 14px; text-align: center; cursor: pointer;
    transition: all 0.2s ease; display: flex; flex-direction: column; align-items: center; gap: 8px;
    font-family: inherit;
  }}
  .type-btn:hover {{ border-color: var(--iob-blue-light); background: #eef2ff; transform: translateY(-2px); }}
  .type-btn.active {{ border-color: var(--iob-blue); background: linear-gradient(135deg, #eef2ff, #e0e8ff); box-shadow: 0 4px 14px rgba(26,58,122,0.15); }}
  .type-btn .icon {{ font-size: 2rem; }}
  .type-btn .label {{ font-size: 0.88rem; font-weight: 700; color: var(--iob-blue); line-height: 1.25; }}
  .type-btn .sublabel {{ font-size: 0.73rem; color: var(--muted); margin-top: 2px; }}

  /* ── SECTION CARDS ── */
  .section-card {{
    background: var(--card); border-radius: 18px; box-shadow: var(--shadow);
    border: 1px solid var(--border); margin-bottom: 24px; overflow: hidden;
  }}
  .section-header {{
    background: linear-gradient(90deg, var(--iob-blue) 0%, var(--iob-blue-light) 100%);
    color: #fff; padding: 16px 24px; display: flex; align-items: center; gap: 12px;
  }}
  .section-header .badge {{
    background: rgba(255,255,255,0.22); border-radius: 6px; padding: 3px 10px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em;
  }}
  .section-header h3 {{ font-size: 1rem; font-weight: 700; }}
  .section-body {{ padding: 24px; }}

  /* ── FORM LAYOUT ── */
  .form-grid {{ display: grid; gap: 18px; }}
  .col-2 {{ grid-template-columns: 1fr 1fr; }}
  .span-2 {{ grid-column: 1 / -1; }}

  /* ── FIELDS ── */
  .field {{ display: flex; flex-direction: column; gap: 5px; }}
  .field label {{
    font-size: 0.75rem; font-weight: 700; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.05em;
  }}
  .field label .req {{ color: var(--error); margin-left: 2px; }}
  .field input, .field select {{
    border: 1.5px solid var(--border); border-radius: 9px; padding: 10px 12px;
    font-size: 0.88rem; font-family: inherit; background: var(--input-bg);
    color: var(--text); transition: all 0.2s ease; outline: none;
  }}
  .field input:focus, .field select:focus {{
    border-color: var(--iob-blue-light); background: #fff;
    box-shadow: 0 0 0 3px rgba(37,80,168,0.12);
  }}
  .field input.error, .field select.error {{ border-color: var(--error) !important; background: #fff5f5; }}
  .field input.autofilled {{ border-color: var(--success) !important; background: #f0fff4 !important; }}
  .field .hint {{ font-size: 0.72rem; color: var(--muted); margin-top: 2px; }}
  .sol-error {{ font-size: 0.75rem; color: var(--error); font-weight: 600; margin-top: 3px; display: none; }}

  /* ── MCC DROPDOWN ── */
  .mcc-wrapper {{ position: relative; }}
  .mcc-dropdown {{
    position: absolute; top: calc(100% + 4px); left: 0; right: 0;
    background: #fff; border: 1.5px solid var(--iob-blue-light);
    border-radius: 10px; max-height: 200px; overflow-y: auto;
    z-index: 200; box-shadow: var(--shadow-lg); display: none;
  }}
  .mcc-dropdown.open {{ display: block; }}
  .mcc-item {{ padding: 9px 12px; font-size: 0.82rem; cursor: pointer; border-bottom: 1px solid #f0f0f0; }}
  .mcc-item:hover {{ background: #eef2ff; }}
  .mcc-item .code {{ font-weight: 700; color: var(--iob-blue); margin-right: 8px; }}
  .mcc-selected {{
    margin-top: 6px; padding: 7px 10px; background: #eef2ff;
    border-radius: 7px; font-size: 0.8rem; color: var(--iob-blue);
    font-weight: 600; display: none;
  }}
  .mcc-selected.show {{ display: block; }}

  /* ── GPS INPUT ── */
  .gps-row {{ display: flex; gap: 8px; }}
  .gps-row input {{ flex: 1; }}
  .btn-gps {{
    padding: 10px 14px; background: var(--iob-blue); color: #fff;
    border: none; border-radius: 99px; cursor: pointer; font-size: 0.8rem;
    font-weight: 600; font-family: inherit; white-space: nowrap; transition: all 0.2s;
  }}
  .btn-gps:hover {{ background: var(--iob-blue-light); }}
  .btn-gps:disabled {{ opacity: 0.6; cursor: not-allowed; }}
  .gps-status {{ font-size: 0.72rem; color: var(--muted); }}

  /* ── RADIO PILLS & HIGHLIGHT BANNERS ── */
  .radio-group {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 4px; }}
  .radio-pill {{
    display: flex; align-items: center; gap: 6px;
    border: 1.5px solid var(--border); border-radius: 99px;
    padding: 8px 16px; cursor: pointer; font-size: 0.84rem;
    font-weight: 600; transition: all 0.2s;
  }}
  .radio-pill input[type=radio], .radio-pill input[type=checkbox] {{ accent-color: var(--iob-blue); }}
  .radio-pill:has(input:checked) {{ border-color: var(--iob-blue); background: #eef2ff; color: var(--iob-blue); }}

  .product-highlight {{
    background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
    border: 1.5px solid #f59e0b; border-radius: 12px;
    padding: 14px 18px; margin-top: 10px; font-size: 0.84rem; color: #92400e;
    display: flex; align-items: flex-start; gap: 10px; line-height: 1.45;
  }}
  .product-highlight .icon {{ font-size: 1.4rem; flex-shrink: 0; }}

  .soundbox-box {{
    background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 12px;
    padding: 16px 20px; margin-top: 8px; display: flex; flex-direction: column; gap: 14px;
  }}

  /* ── SUBMIT BUTTON ── */
  .submit-zone {{ text-align: center; padding: 12px 0 4px; }}
  .btn-submit {{
    background: linear-gradient(135deg, var(--iob-blue) 0%, var(--iob-blue-light) 100%);
    color: #fff; border: none; border-radius: 12px; padding: 14px 44px;
    font-size: 0.98rem; font-weight: 700; font-family: inherit; cursor: pointer;
    transition: all 0.25s ease; box-shadow: 0 4px 16px rgba(26,58,122,0.3);
  }}
  .btn-submit:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(26,58,122,0.4); }}
  .btn-submit:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
  .btn-reset {{
    background: none; border: 1.5px solid var(--border); border-radius: 12px;
    padding: 12px 28px; font-size: 0.88rem; font-weight: 600; font-family: inherit;
    cursor: pointer; color: var(--muted); margin-left: 10px;
  }}
  .btn-reset:hover {{ border-color: var(--muted); color: var(--text); }}

  /* ── INFO BANNER ── */
  .info-box {{
    background: #fffbeb; border: 1px solid #f5c842; border-radius: 9px;
    padding: 10px 14px; font-size: 0.8rem; color: #7a5800;
    display: flex; gap: 8px; align-items: center; margin-bottom: 18px;
  }}

  /* ── MODALS & FLOATING AUTH PANEL ── */
  .modal-overlay {{
    position: fixed; inset: 0; background: rgba(13,35,84,0.55);
    backdrop-filter: blur(6px); z-index: 500;
    display: flex; align-items: center; justify-content: center;
    padding: 16px; opacity: 0; pointer-events: none; transition: opacity 0.3s;
  }}
  .modal-overlay.open {{ opacity: 1; pointer-events: auto; }}
  .modal-card {{
    background: var(--card); border-radius: 20px; max-width: 460px; width: 100%;
    box-shadow: var(--shadow-lg); border: 1px solid var(--border); overflow: hidden;
    transform: translateY(20px); transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1);
  }}
  .modal-overlay.open .modal-card {{ transform: translateY(0); }}
  .modal-header {{
    background: linear-gradient(90deg, var(--iob-blue-dark) 0%, var(--iob-blue) 100%);
    color: #fff; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between;
  }}
  .modal-header h3 {{ font-size: 1rem; font-weight: 700; }}
  .modal-close {{ background: none; border: none; color: #fff; font-size: 1.4rem; cursor: pointer; opacity: 0.8; }}
  .modal-body {{ padding: 20px; display: flex; flex-direction: column; gap: 14px; }}
  .modal-footer {{ padding: 0 20px 20px; display: flex; justify-content: flex-end; gap: 8px; }}

  .first-time-box {{
    background: #fef3c7; border: 1px solid #f59e0b; border-radius: 10px;
    padding: 12px 14px; font-size: 0.8rem; color: #92400e; line-height: 1.4;
  }}

  .staff-badge-float {{
    background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px;
    padding: 10px 14px; font-size: 0.82rem; color: #166534; font-weight: 600;
    display: none;
  }}

  /* ── STATUS / TRACKING TABLE ── */
  .search-bar-wrap {{ margin-bottom: 16px; display: flex; gap: 12px; }}
  .search-bar-wrap input {{
    flex: 1; border: 1.5px solid var(--border); border-radius: 99px;
    padding: 10px 18px; font-size: 0.88rem; font-family: inherit; outline: none;
    background: var(--input-bg);
  }}
  .search-bar-wrap input:focus {{ border-color: var(--iob-blue-light); background: #fff; }}

  .table-card {{
    background: var(--card); border-radius: 16px; border: 1px solid var(--border);
    box-shadow: var(--shadow); overflow: hidden;
  }}
  .table-responsive {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.85rem; }}
  th {{
    background: #f8faff; color: var(--muted); font-weight: 700;
    text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.05em;
    padding: 14px 16px; border-bottom: 1px solid var(--border);
  }}
  td {{ padding: 14px 16px; border-bottom: 1px solid #f0f4ff; color: var(--text); vertical-align: middle; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #f8fbff; }}

  .badge-type {{
    display: inline-block; padding: 3px 8px; border-radius: 6px;
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
  }}
  .badge-type.qr {{ background: #e0e7ff; color: #3730a3; }}
  .badge-type.sb {{ background: #fae8ff; color: #86198f; }}
  .badge-type.lead {{ background: #fef3c7; color: #92400e; }}

  .badge-status {{
    display: inline-flex; align-items: center; gap: 4px;
    padding: 4px 10px; border-radius: 99px; font-size: 0.75rem; font-weight: 700;
  }}
  .badge-status.pending {{ background: #fef3c7; color: #92400e; }}
  .badge-status.vendor {{ background: #e0f2fe; color: #0369a1; }}
  .badge-status.completed {{ background: #dcfce7; color: #166534; }}
  .badge-status.rejected {{ background: #fee2e2; color: #991b1b; }}

  .btn-pdf {{
    background: #f0fdf4; color: var(--success); border: 1px solid #bbf7d0;
    border-radius: 8px; padding: 6px 12px; font-size: 0.78rem;
    font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;
    transition: all 0.2s;
  }}
  .btn-pdf:hover {{ background: #dcfce7; }}

  /* ── TOAST ── */
  #toast {{
    position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%) translateY(80px);
    background: var(--iob-blue-dark); color: #fff; padding: 12px 24px; border-radius: 10px;
    font-size: 0.88rem; font-weight: 600; box-shadow: var(--shadow-lg);
    transition: transform 0.35s cubic-bezier(0.34,1.56,0.64,1); z-index: 999; text-align: center;
  }}
  #toast.show {{ transform: translateX(-50%) translateY(0); }}
  #toast.success {{ background: var(--success); }}
  #toast.error {{ background: var(--error); }}

  .hidden {{ display: none !important; }}
  .section-divider {{ border: none; border-top: 1.5px dashed var(--border); margin: 6px 0 16px; }}
  .empty-state {{ padding: 40px 16px; text-align: center; color: var(--muted); font-size: 0.9rem; }}

  @media (max-width: 768px) {{
    .type-options {{ grid-template-columns: 1fr; }}
    .col-2 {{ grid-template-columns: 1fr; }}
    .header-title {{ display: none; }}
  }}
</style>
</head>
<body>

<!-- SPLASH -->
<div id="splash">
  <div id="lottie-splash"></div>
  <div id="splash-title">Indian Overseas Bank</div>
  <div id="splash-sub">Merchant Services Portal</div>
  <div id="splash-progress"><div id="splash-bar"></div></div>
</div>

<!-- HEADER -->
<header>
  <div class="header-left">
    <img src="2026logo_min.svg" alt="IOB Logo" class="header-logo">
    <span class="header-title">Merchant Services Portal</span>
  </div>
  <div class="header-right">
    <a href="admin.html" class="admin-link">⚙️ Admin Dashboard</a>
    <div id="header-lottie" class="header-lottie"></div>
  </div>
</header>

<!-- MAIN -->
<main>

  <!-- NAVIGATION TABS -->
  <div class="nav-tabs">
    <button type="button" class="nav-tab-btn active" id="tab-apply" onclick="switchNavTab('apply')">📝 Submit Application / Lead</button>
    <button type="button" class="nav-tab-btn" id="tab-status" onclick="switchNavTab('status')">🔍 Track Applications & Status</button>
  </div>

  <!-- ════════════════ PAGE 1: APPLICATION FORM ════════════════ -->
  <div id="page-apply">

    <!-- DATALISTS -->
    <datalist id="sol-datalist">
"""

for code, bdata in branches.items():
    html_content += f'      <option value="{code}">{code} — {bdata["name"]}</option>\n'

html_content += f"""    </datalist>

    <datalist id="staff-datalist">
"""

for roll, sdata in staff_list.items():
    html_content += f'      <option value="{roll}">{roll} — {sdata["name"]} ({sdata["designation"]})</option>\n'

html_content += f"""    </datalist>

    <!-- SERVICE SELECTOR -->
    <div class="type-card">
      <h2>Select Merchant Service or Product Lead</h2>
      <p>Choose whether to onboard a new QR Code, request Soundbox, or submit a Merchant Product Lead:</p>
      <div class="type-options">
        <button type="button" class="type-btn" id="btn-qr" onclick="setType('qr')">
          <span class="icon">📲</span>
          <span class="label">New Payment QR Code</span>
          <span class="sublabel">Generates UPI QR (Option for Soundbox)</span>
        </button>
        <button type="button" class="type-btn" id="btn-soundbox" onclick="setType('soundbox')">
          <span class="icon">🔊</span>
          <span class="label">Soundbox Only</span>
          <span class="sublabel">For merchants already having QR Code & VPA</span>
        </button>
        <button type="button" class="type-btn" id="btn-lead" onclick="setType('lead')">
          <span class="icon">💳</span>
          <span class="label">Submit Merchant Lead</span>
          <span class="sublabel">3-in-1 POS, IOB Pay, or QR Standee</span>
        </button>
      </div>
    </div>

    <form id="mainForm" novalidate>

      <!-- ══════════ QR CODE SECTION ══════════ -->
      <div id="qr-section" class="hidden">
        <div class="section-card">
          <div class="section-header">
            <span class="badge">QR CODE</span>
            <h3>QR Code Generation Template Details</h3>
          </div>
          <div class="section-body">

            <div class="info-box">
              <span>💡 Pre-set Defaults: <strong>ACTIVE = 1</strong>, <strong>ONBORDINGTYPE = M</strong>, <strong>STATE = TamilNadu</strong>. VPA will be generated by Admin upon completion.</span>
            </div>

            <div class="form-grid col-2">
              <div class="field">
                <label>MERCHANTNAME <span class="req">*</span></label>
                <input type="text" id="qr-merchantname" placeholder="Full Merchant / Shop Name" autocomplete="off">
              </div>
              <div class="field">
                <label>MERCHANTVPA <span class="hint">(Suggested VPA)</span></label>
                <input type="text" id="qr-merchantvpa" placeholder="e.g. merchantname@iob (Optional)">
              </div>
              <div class="field">
                <label>ACCOUNTNO <span class="req">*</span></label>
                <input type="text" id="qr-accountno" placeholder="Bank Account Number" inputmode="numeric">
              </div>
              <div class="field">
                <label>IFSC <span class="req">*</span></label>
                <input type="text" id="qr-ifsc" placeholder="e.g. IOBA0000174" style="text-transform:uppercase">
              </div>
              <div class="field">
                <label>MOBILENO <span class="req">*</span></label>
                <input type="tel" id="qr-mobile" placeholder="10-digit Mobile Number" maxlength="10" inputmode="numeric">
              </div>
              <div class="field">
                <label>EMAILID <span class="req">*</span></label>
                <input type="email" id="qr-email" placeholder="merchant@email.com">
              </div>
              <div class="field">
                <label>GSTNO <span class="hint">(Not Mandatory)</span></label>
                <input type="text" id="qr-gstno" placeholder="15-digit GSTIN (Optional)" style="text-transform:uppercase">
              </div>
              <div class="field">
                <label>MERCHANTTYPE <span class="req">*</span></label>
                <select id="qr-merchanttype">
                  <option value="">-- Select Merchant Type --</option>
                  <option value="SMALL">Small merchant - turnover up to ₹ 20 lakh</option>
                  <option value="LARGE">Large merchant - turnover above ₹ 20 lakh</option>
                </select>
              </div>
            </div>

            <hr class="section-divider">

            <div class="form-grid col-2">
              <div class="field span-2">
                <label>MCCCODE <span class="req">*</span></label>
                <div class="mcc-wrapper">
                  <input type="text" id="qr-mcc-search" class="mcc-search" placeholder="Type to search MCC codes or categories..." autocomplete="off">
                  <div id="qr-mcc-dropdown" class="mcc-dropdown"></div>
                  <input type="hidden" id="qr-mcc-value">
                  <div id="qr-mcc-selected" class="mcc-selected"></div>
                </div>
              </div>
            </div>

            <hr class="section-divider">

            <div class="form-grid col-2">
              <div class="field">
                <label>LATITUDE (6 decimal) <span class="req">*</span></label>
                <div class="gps-row">
                  <input type="text" id="qr-lat" placeholder="e.g. 10.362400" inputmode="decimal">
                  <button type="button" class="btn-gps" onclick="getGPS('qr')" id="qr-gps-btn">📍 Capture GPS</button>
                </div>
                <div class="gps-status" id="qr-gps-status"></div>
              </div>
              <div class="field">
                <label>LONGITUDE (6 decimal) <span class="req">*</span></label>
                <input type="text" id="qr-lng" placeholder="e.g. 77.969500" inputmode="decimal">
              </div>
            </div>

            <hr class="section-divider">

            <div class="form-grid col-2">
              <div class="field">
                <label>ADDRESS1 <span class="req">*</span></label>
                <input type="text" id="qr-addr1" placeholder="Door No, Street Name">
              </div>
              <div class="field">
                <label>ADDRESS2</label>
                <input type="text" id="qr-addr2" placeholder="Area / Landmark">
              </div>
              <div class="field">
                <label>POSTOFFICENAME <span class="req">*</span></label>
                <input type="text" id="qr-postoffice" placeholder="Post Office Name">
              </div>
              <div class="field">
                <label>PINCODE <span class="req">*</span></label>
                <input type="text" id="qr-pincode" placeholder="6-digit Pincode" maxlength="6" inputmode="numeric">
              </div>
              <div class="field">
                <label>STATE</label>
                <input type="text" id="qr-state" value="TamilNadu" readonly style="color:var(--muted)">
              </div>
              <div class="field">
                <label>DISTRICT <span class="req">*</span></label>
                <input type="text" id="qr-district" placeholder="District">
              </div>
              <div class="field span-2">
                <label>SUBDISTRICT <span class="req">*</span></label>
                <input type="text" id="qr-subdistrict" placeholder="Taluk / Sub-District">
              </div>
            </div>

            <hr class="section-divider">

            <!-- SOUNDBOX REQUIREMENT TOGGLE -->
            <div class="soundbox-box">
              <div style="display:flex;align-items:center;justify-content:space-between">
                <div>
                  <strong style="color:var(--iob-blue);font-size:0.9rem">🔊 Apply for NPST Soundbox after QR Generation?</strong>
                  <p style="font-size:0.75rem;color:var(--muted);margin-top:2px">When checked, an application for Soundbox will automatically be created once Admin generates the QR Code & VPA.</p>
                </div>
                <label class="radio-pill">
                  <input type="checkbox" id="qr-require-sb" onchange="toggleQrSbFields(this.checked)"> Yes, Soundbox Required
                </label>
              </div>

              <div id="qr-sb-fields" class="hidden" style="margin-top:8px">
                <div class="form-grid col-2">
                  <div class="field">
                    <label>Sol ID / Branch Code <span class="req">*</span></label>
                    <input type="text" id="qr-solid" list="sol-datalist" placeholder="Search / Type Sol ID (e.g. 0174)" maxlength="4" inputmode="numeric" oninput="onSolInput(this, 'qr')">
                    <div class="sol-error" id="qr-sol-error"></div>
                  </div>
                  <div class="field">
                    <label>Branch Name (Autofill)</label>
                    <input type="text" id="qr-branchname" placeholder="Branch Name" readonly>
                  </div>
                  <div class="field span-2">
                    <label>Soundbox Language <span class="req">*</span></label>
                    <div class="radio-group">
                      <label class="radio-pill"><input type="radio" name="qr-sb-lang" value="ta" checked> Tamil (ta)</label>
                      <label class="radio-pill"><input type="radio" name="qr-sb-lang" value="en"> English (en)</label>
                      <label class="radio-pill"><input type="radio" name="qr-sb-lang" value="hi"> Hindi (hi)</label>
                      <label class="radio-pill"><input type="radio" name="qr-sb-lang" value="ml"> Malayalam (ml)</label>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- ══════════ SOUNDBOX SECTION ══════════ -->
      <div id="sb-section" class="hidden">
        <div class="section-card">
          <div class="section-header">
            <span class="badge">SOUNDBOX</span>
            <h3>Soundbox Application Template Details (Existing QR Holders)</h3>
          </div>
          <div class="section-body">

            <div class="form-grid col-2">
              <div class="field">
                <label>Sol ID <span class="req">*</span></label>
                <input type="text" id="sb-solid" list="sol-datalist" placeholder="Search / Type Sol ID (e.g. 0174)" maxlength="4" inputmode="numeric" oninput="onSolInput(this, 'sb')">
                <div class="sol-error" id="sb-sol-error"></div>
                <div class="hint">Must be a valid 4-digit SOL ID from branches.csv</div>
              </div>
              <div class="field">
                <label>Branch Name (Autofill)</label>
                <input type="text" id="sb-branchname" placeholder="Branch Name" readonly>
              </div>
              <div class="field">
                <label>Region (Autofill)</label>
                <input type="text" id="sb-region" value="Dindigul" placeholder="Region" readonly>
              </div>
              <div class="field">
                <label>VPA <span class="req">*</span></label>
                <input type="text" id="sb-vpa" placeholder="e.g. merchant@iob">
              </div>
              <div class="field">
                <label>Account Name <span class="req">*</span></label>
                <input type="text" id="sb-accountname" placeholder="Account Name">
              </div>
              <div class="field">
                <label>Mobile Number <span class="req">*</span></label>
                <input type="tel" id="sb-mobile" placeholder="10-digit Mobile Number" maxlength="10" inputmode="numeric">
              </div>
            </div>

            <hr class="section-divider">

            <div class="form-grid col-2">
              <div class="field span-2">
                <label>Address <span class="req">*</span></label>
                <input type="text" id="sb-address" placeholder="Full Merchant Address">
              </div>
              <div class="field">
                <label>Pin Code <span class="req">*</span></label>
                <input type="text" id="sb-pincode" placeholder="6-digit Pincode" maxlength="6" inputmode="numeric">
              </div>
              <div class="field">
                <label>City <span class="req">*</span></label>
                <input type="text" id="sb-city" placeholder="City / Town">
              </div>
              <div class="field">
                <label>State <span class="req">*</span></label>
                <input type="text" id="sb-state" value="Tamil Nadu" placeholder="State">
              </div>
            </div>

            <hr class="section-divider">

            <div class="form-grid col-2">
              <div class="field span-2">
                <label>MCC <span class="req">*</span></label>
                <div class="mcc-wrapper">
                  <input type="text" id="sb-mcc-search" class="mcc-search" placeholder="Type to search MCC codes or categories..." autocomplete="off">
                  <div id="sb-mcc-dropdown" class="mcc-dropdown"></div>
                  <input type="hidden" id="sb-mcc-value">
                  <div id="sb-mcc-selected" class="mcc-selected"></div>
                </div>
              </div>
            </div>

            <hr class="section-divider">

            <div class="field">
              <label>Language <span class="req">*</span></label>
              <div class="radio-group">
                <label class="radio-pill"><input type="radio" name="sb-lang" value="ta" checked> Tamil (ta)</label>
                <label class="radio-pill"><input type="radio" name="sb-lang" value="en"> English (en)</label>
                <label class="radio-pill"><input type="radio" name="sb-lang" value="hi"> Hindi (hi)</label>
                <label class="radio-pill"><input type="radio" name="sb-lang" value="ml"> Malayalam (ml)</label>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- ══════════ MERCHANT LEADS SECTION ══════════ -->
      <div id="lead-section" class="hidden">
        <div class="section-card">
          <div class="section-header">
            <span class="badge">LEAD SUBMISSION</span>
            <h3>Submit Lead for Merchant Solutions</h3>
          </div>
          <div class="section-body">

            <!-- PRODUCT SELECTOR -->
            <div class="field">
              <label>Select Product / Solution <span class="req">*</span></label>
              <div class="radio-group" style="margin-top:6px">
                <label class="radio-pill">
                  <input type="radio" name="lead-product" value="3 in 1 POS (QR Code + POS + Soundbox)" checked onchange="onLeadProductChange(this.value)">
                  💳 3 in 1 POS (QR + POS + Soundbox)
                </label>
                <label class="radio-pill">
                  <input type="radio" name="lead-product" value="IOB Pay (Online Payment Solution)" onchange="onLeadProductChange(this.value)">
                  🌐 IOB Pay (Online Solution)
                </label>
                <label class="radio-pill">
                  <input type="radio" name="lead-product" value="QR Standee (Religious / Charity)" onchange="onLeadProductChange(this.value)">
                  🏛️ QR Standee (Religious / Charity)
                </label>
              </div>
            </div>

            <!-- PRODUCT HIGHLIGHT BANNERS -->
            <div class="product-highlight" id="lead-banner-pos">
              <span class="icon">🎁</span>
              <div>
                <strong>Special Scheme for POS:</strong> POS is available <strong>RENT-FREE</strong> for <strong>CD Diamond</strong> and <strong>CD Platinum</strong> account holders — provided Average Quarterly Balance (AQB) is maintained!
              </div>
            </div>

            <div class="product-highlight hidden" id="lead-banner-iobpay">
              <span class="icon">🎓</span>
              <div>
                <strong>IOB Pay Solution:</strong> Customized online payment gateway solution for <strong>Schools, Colleges, Lodges, Hospitals, & Educational Institutions</strong>.
              </div>
            </div>

            <div class="product-highlight hidden" id="lead-banner-qrstandee">
              <span class="icon">🏛️</span>
              <div>
                <strong>QR Standee Solution:</strong> Specially designed durable payment QR standees for <strong>Religious Institutions, Temples, & Charity Trusts</strong>.
              </div>
            </div>

            <hr class="section-divider">

            <div class="form-grid col-2">
              <div class="field">
                <label>Sol ID / Branch Code <span class="req">*</span></label>
                <input type="text" id="lead-solid" list="sol-datalist" placeholder="Search / Type Sol ID (e.g. 0174)" maxlength="4" inputmode="numeric" oninput="onSolInput(this, 'lead')">
                <div class="sol-error" id="lead-sol-error"></div>
              </div>
              <div class="field">
                <label>Branch Name (Autofill)</label>
                <input type="text" id="lead-branchname" placeholder="Branch Name" readonly>
              </div>
              <div class="field">
                <label>15-digit Current Account Number <span class="req">*</span></label>
                <input type="text" id="lead-accountno" placeholder="15-digit Current Account No" maxlength="15" inputmode="numeric">
                <div class="hint">15-digit IOB Current Account number</div>
              </div>
              <div class="field">
                <label>Merchant / Entity Name <span class="req">*</span></label>
                <input type="text" id="lead-merchantname" placeholder="Full Merchant / Institution Name">
              </div>
              <div class="field">
                <label>Merchant Mobile Number <span class="req">*</span></label>
                <input type="tel" id="lead-mobile" placeholder="10-digit Mobile Number" maxlength="10" inputmode="numeric">
              </div>
              <div class="field">
                <label>Number of Devices / Solutions Required <span class="req">*</span></label>
                <input type="number" id="lead-devices" placeholder="e.g. 1" min="1" value="1" inputmode="numeric">
              </div>
            </div>

            <hr class="section-divider">

            <div class="form-grid col-2">
              <div class="field">
                <label>Branch Contact Person Name <span class="req">*</span></label>
                <input type="text" id="lead-contactname" placeholder="Name of Branch Staff / Officer">
              </div>
              <div class="field">
                <label>Branch Contact Mobile Number <span class="req">*</span></label>
                <input type="tel" id="lead-contactmobile" placeholder="10-digit Staff Mobile Number" maxlength="10" inputmode="numeric">
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- SUBMIT -->
      <div id="submit-zone" class="section-card hidden">
        <div class="section-body submit-zone">
          <button type="button" class="btn-submit" id="btn-submit" onclick="onInitiateSubmit()">
            Submit Application / Lead
          </button>
          <button type="button" class="btn-reset" onclick="resetForm()">Reset</button>
        </div>
      </div>

    </form>

  </div>

  <!-- ════════════════ PAGE 2: STATUS & TRACKING ════════════════ -->
  <div id="page-status" class="hidden">
    <div class="section-card">
      <div class="section-header">
        <span class="badge">TRACKING</span>
        <h3>Track Application & Lead Status</h3>
      </div>
      <div class="section-body">
        
        <div class="search-bar-wrap">
          <input type="text" id="statusSearch" placeholder="Search by Merchant Name, VPA, Account No, Mobile No, SOL ID..." oninput="renderStatusTable()">
          <button type="button" class="btn-gps" onclick="loadStatusData()">🔄 Refresh</button>
        </div>

        <div class="table-card">
          <div class="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Type / Product</th>
                  <th>Merchant Name</th>
                  <th>VPA / Account</th>
                  <th>Mobile</th>
                  <th>Location / SOL</th>
                  <th>Status & Progress</th>
                  <th>Document / Details</th>
                </tr>
              </thead>
              <tbody id="statusTableBody">
                <tr><td colspan="7" class="empty-state">Loading status data...</td></tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  </div>

</main>

<!-- FLOATING AUTHENTICATION PANEL MODAL (WITH FIRST-TIME PWD CHANGE ENFORCEMENT) -->
<div class="modal-overlay" id="staffAuthModal">
  <div class="modal-card">
    <div class="modal-header">
      <h3 id="authModalTitle">👤 Staff Authentication Required</h3>
      <button class="modal-close" onclick="closeStaffAuthModal()">&times;</button>
    </div>
    <div class="modal-body">
      <div style="font-size:0.83rem;color:var(--muted);line-height:1.4" id="authModalDesc">
        Please enter your <strong>Staff Roll Number</strong> and <strong>Password</strong> to authorize this submission.
      </div>

      <!-- FIRST TIME LOGIN NOTICE -->
      <div class="first-time-box hidden" id="firstTimeNotice">
        🔒 <strong>First-Time Login Detected!</strong> Default password (Roll No) detected. Please set your new custom password below to complete authorization.
      </div>

      <div class="field">
        <label>Staff Roll Number <span class="req">*</span></label>
        <input type="text" id="modal-staff-roll" list="staff-datalist" placeholder="Enter Roll No (e.g. 48243)" oninput="onStaffRollInputModal(this.value)">
      </div>

      <div class="field" id="currentPassContainer">
        <label id="passLabel">Current Password <span class="req">*</span></label>
        <input type="password" id="modal-staff-pass" placeholder="Password (Default: Roll No)">
      </div>

      <!-- NEW PASSWORD FIELDS (APPEARS ON 1ST LOGIN) -->
      <div class="field hidden" id="newPassContainer">
        <label>Create New Password <span class="req">*</span></label>
        <input type="password" id="modal-staff-newpass" placeholder="Enter New Password">
      </div>
      <div class="field hidden" id="confirmPassContainer">
        <label>Confirm New Password <span class="req">*</span></label>
        <input type="password" id="modal-staff-confirmpass" placeholder="Re-enter New Password">
      </div>

      <div class="staff-badge-float" id="modal-staff-badge">
        <!-- Verified Info Filled Here -->
      </div>

      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px" id="modalFooterLinks">
        <span style="font-size:0.75rem;color:var(--muted)">1st Login Default = Roll No</span>
        <span style="font-size:0.75rem;color:var(--iob-blue-light);text-decoration:underline;cursor:pointer;font-weight:600" onclick="openPassChangeModal()">🔒 Change Password</span>
      </div>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn-cancel" onclick="closeStaffAuthModal()">Cancel</button>
      <button type="button" class="btn-submit" style="padding:10px 24px;font-size:0.9rem" id="btnConfirmAuthSubmit" onclick="confirmAuthAndSubmit()">
        ✓ Confirm & Submit
      </button>
    </div>
  </div>
</div>

<!-- CHANGE PASSWORD MODAL (REGULAR FORGOT/CHANGE) -->
<div class="modal-overlay" id="passChangeModal">
  <div class="modal-card">
    <div class="modal-header">
      <h3>🔒 Change My Password</h3>
      <button class="modal-close" onclick="closePassChangeModal()">&times;</button>
    </div>
    <div class="modal-body">
      <div class="field">
        <label>Staff Roll Number <span class="req">*</span></label>
        <input type="text" id="change-roll" placeholder="Enter Staff Roll No (e.g. 48243)">
      </div>
      <div class="field">
        <label>Current Password <span class="req">*</span></label>
        <input type="password" id="change-oldpass" placeholder="Current Password (Default: Roll No)">
      </div>
      <div class="field">
        <label>New Password <span class="req">*</span></label>
        <input type="password" id="change-newpass" placeholder="Enter New Password">
      </div>
      <div style="font-size:0.75rem;color:var(--muted);background:#f8fafc;padding:8px 12px;border-radius:8px">
        ⚠️ <strong>Forgot Password?</strong> Password resets are strictly managed by your Administrator. Please contact your Admin to reset your password back to default.
      </div>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn-cancel" onclick="closePassChangeModal()">Cancel</button>
      <button type="button" class="btn-submit" style="padding:10px 20px;font-size:0.85rem" onclick="saveNewPassword()">Save New Password</button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
// CONFIGURATION
let APPS_SCRIPT_URL = "{admin_url}";

// Embedded MCC List
const MCC_LIST = {json.dumps(mcc_list)};

// Embedded Lottie Animation
const LOTTIE_DATA = {json.dumps(lottie_data)};

// Embedded Branches Data (58 valid branches from branches.csv)
const BRANCHES = {json.dumps(branches)};

// Embedded Staff List (293 staff from staff_list.csv)
const STAFF_LIST = {json.dumps(staff_list)};

let TRACKING_DATA = {{ qr: [], sb: [], lead: [] }};
let currentActiveStaff = null;
let isFirstTimeLogin = false;

// Initialize Splash & Lottie
window.addEventListener('DOMContentLoaded', () => {{
  lottie.loadAnimation({{
    container: document.getElementById('lottie-splash'),
    renderer: 'svg', loop: true, autoplay: true,
    animationData: LOTTIE_DATA
  }});
  lottie.loadAnimation({{
    container: document.getElementById('header-lottie'),
    renderer: 'svg', loop: true, autoplay: true,
    animationData: LOTTIE_DATA
  }});

  let p = 0;
  const bar = document.getElementById('splash-bar');
  const timer = setInterval(() => {{
    p = Math.min(p + 20, 95);
    bar.style.width = p + '%';
  }}, 100);

  setTimeout(() => {{
    clearInterval(timer);
    bar.style.width = '100%';
    setTimeout(() => {{
      document.getElementById('splash').classList.add('hide');
    }}, 300);
  }}, 800);

  setupMCC('qr');
  setupMCC('sb');

  // Background fetch status data immediately so tracking tab is pre-warmed
  loadStatusData();

  document.addEventListener('click', e => {{
    if (!e.target.closest('.mcc-wrapper')) {{
      document.querySelectorAll('.mcc-dropdown').forEach(d => d.classList.remove('open'));
    }}
  }});
}});

function onStaffRollInputModal(roll) {{
  const rollClean = roll.trim();
  const badge = document.getElementById('modal-staff-badge');
  const passEl = document.getElementById('modal-staff-pass');

  const firstNotice = document.getElementById('firstTimeNotice');
  const newPassBox = document.getElementById('newPassContainer');
  const confirmPassBox = document.getElementById('confirmPassContainer');

  if (!rollClean) {{
    badge.style.display = 'none';
    firstNotice.classList.add('hidden');
    newPassBox.classList.add('hidden');
    confirmPassBox.classList.add('hidden');
    currentActiveStaff = null;
    isFirstTimeLogin = false;
    return;
  }}

  const staff = STAFF_LIST[rollClean];
  if (staff) {{
    currentActiveStaff = {{ roll: rollClean, ...staff }};

    const hasCustomPass = localStorage.getItem('staff_pass_' + rollClean) ? true : false;
    isFirstTimeLogin = !hasCustomPass;

    if (isFirstTimeLogin) {{
      firstNotice.classList.remove('hidden');
      newPassBox.classList.remove('hidden');
      confirmPassBox.classList.remove('hidden');
      document.getElementById('passLabel').textContent = "Current Password (Default: Roll No)";
      if (!passEl.value) passEl.value = rollClean;
    }} else {{
      firstNotice.classList.add('hidden');
      newPassBox.classList.add('hidden');
      confirmPassBox.classList.add('hidden');
      document.getElementById('passLabel').textContent = "Password";
      const savedPass = localStorage.getItem('staff_pass_' + rollClean);
      if (!passEl.value) passEl.value = savedPass || rollClean;
    }}

    // Lookup branch details
    const branch = BRANCHES[staff.sol] || {{ name: 'Branch ' + staff.sol }};
    badge.innerHTML = `✓ <strong>${{staff.name}}</strong> (${{staff.designation}}) — <strong>Branch:</strong> ${{staff.sol}} (${{branch.name}})`;
    badge.style.display = 'block';

    // Auto-fill SOL ID and Branch Name in background form if empty or incomplete
    ['qr', 'sb', 'lead'].forEach(prefix => {{
      const solEl = document.getElementById(prefix + '-solid');
      if (solEl && !solEl.value) {{
        solEl.value = staff.sol;
        onSolInput(solEl, prefix);
      }}
    }});

    const contactNameEl = document.getElementById('lead-contactname');
    if (contactNameEl && !contactNameEl.value) contactNameEl.value = staff.name;

  }} else {{
    currentActiveStaff = null;
    isFirstTimeLogin = false;
    badge.style.display = 'none';
    firstNotice.classList.add('hidden');
    newPassBox.classList.add('hidden');
    confirmPassBox.classList.add('hidden');
  }}
}}

function onInitiateSubmit() {{
  if (!currentType) {{ showToast('Please select service / lead type first', 'error'); return; }}
  if (!validateFormFields()) return;

  // Open Floating Authentication Modal
  document.getElementById('staffAuthModal').classList.add('open');
  const rollInput = document.getElementById('modal-staff-roll');
  if (currentActiveStaff) {{
    rollInput.value = currentActiveStaff.roll;
    onStaffRollInputModal(currentActiveStaff.roll);
  }} else {{
    rollInput.focus();
  }}
}}

function closeStaffAuthModal() {{
  document.getElementById('staffAuthModal').classList.remove('open');
}}

function confirmAuthAndSubmit() {{
  const roll = document.getElementById('modal-staff-roll').value.trim();
  const pass = document.getElementById('modal-staff-pass').value.trim();

  if (!roll || !STAFF_LIST[roll]) {{
    showToast('Please enter a valid Staff Roll Number', 'error');
    document.getElementById('modal-staff-roll').focus();
    return;
  }}

  const expectedPass = localStorage.getItem('staff_pass_' + roll) || roll;
  if (pass !== expectedPass) {{
    showToast('Incorrect Current Password for Roll Number ' + roll, 'error');
    document.getElementById('modal-staff-pass').focus();
    return;
  }}

  // Handle First-Time Login Password Change Mandatory Prompt
  if (isFirstTimeLogin) {{
    const newPass = document.getElementById('modal-staff-newpass').value.trim();
    const confirmPass = document.getElementById('modal-staff-confirmpass').value.trim();

    if (!newPass) {{
      showToast('First login requires creating a new custom password', 'error');
      document.getElementById('modal-staff-newpass').focus();
      return;
    }}

    if (newPass === roll) {{
      showToast('New password cannot be the default Roll Number', 'error');
      document.getElementById('modal-staff-newpass').focus();
      return;
    }}

    if (newPass !== confirmPass) {{
      showToast('New passwords do not match. Please re-check', 'error');
      document.getElementById('modal-staff-confirmpass').focus();
      return;
    }}

    // Save newly created password
    localStorage.setItem('staff_pass_' + roll, newPass);
    showToast('✅ New password created successfully!', 'success');
  }}

  currentActiveStaff = {{ roll: roll, ...STAFF_LIST[roll] }};
  closeStaffAuthModal();
  executeSubmission();
}}

function openPassChangeModal() {{
  document.getElementById('passChangeModal').classList.add('open');
  if (currentActiveStaff) document.getElementById('change-roll').value = currentActiveStaff.roll;
}}

function closePassChangeModal() {{
  document.getElementById('passChangeModal').classList.remove('open');
}}

function saveNewPassword() {{
  const roll = document.getElementById('change-roll').value.trim();
  const oldPass = document.getElementById('change-oldpass').value.trim();
  const newPass = document.getElementById('change-newpass').value.trim();

  if (!roll || !STAFF_LIST[roll]) {{ showToast('Please enter a valid Staff Roll Number', 'error'); return; }}
  const expectedOld = localStorage.getItem('staff_pass_' + roll) || roll;
  if (oldPass !== expectedOld) {{ showToast('Current password does not match', 'error'); return; }}
  if (!newPass) {{ showToast('Please enter a valid new password', 'error'); return; }}

  localStorage.setItem('staff_pass_' + roll, newPass);
  showToast('✅ Password changed successfully!', 'success');
  closePassChangeModal();
  if (currentActiveStaff && currentActiveStaff.roll === roll) {{
    document.getElementById('modal-staff-pass').value = newPass;
  }}
}}

function switchNavTab(tab) {{
  document.querySelectorAll('.nav-tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');

  if (tab === 'apply') {{
    document.getElementById('page-apply').classList.remove('hidden');
    document.getElementById('page-status').classList.add('hidden');
  }} else {{
    document.getElementById('page-apply').classList.add('hidden');
    document.getElementById('page-status').classList.remove('hidden');
    renderStatusTable();
    loadStatusData();
  }}
}}

let currentType = null;
function setType(t) {{
  currentType = t;
  document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('btn-' + t).classList.add('active');

  const qr = document.getElementById('qr-section');
  const sb = document.getElementById('sb-section');
  const lead = document.getElementById('lead-section');
  const sz = document.getElementById('submit-zone');

  qr.classList.add('hidden');
  sb.classList.add('hidden');
  lead.classList.add('hidden');

  let firstSection = null;
  if (t === 'qr') {{
    qr.classList.remove('hidden');
    firstSection = qr;
  }} else if (t === 'soundbox') {{
    sb.classList.remove('hidden');
    firstSection = sb;
  }} else if (t === 'lead') {{
    lead.classList.remove('hidden');
    firstSection = lead;
  }}

  sz.classList.remove('hidden');

  if (firstSection) {{
    firstSection.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }}
}}

function onLeadProductChange(val) {{
  document.getElementById('lead-banner-pos').classList.add('hidden');
  document.getElementById('lead-banner-iobpay').classList.add('hidden');
  document.getElementById('lead-banner-qrstandee').classList.add('hidden');

  if (val.includes('3 in 1 POS')) document.getElementById('lead-banner-pos').classList.remove('hidden');
  else if (val.includes('IOB Pay')) document.getElementById('lead-banner-iobpay').classList.remove('hidden');
  else if (val.includes('QR Standee')) document.getElementById('lead-banner-qrstandee').classList.remove('hidden');
}}

function toggleQrSbFields(checked) {{
  const fields = document.getElementById('qr-sb-fields');
  if (checked) fields.classList.remove('hidden');
  else fields.classList.add('hidden');
}}

function onSolInput(el, prefix) {{
  const raw = el.value.replace(/\\D/g, '');
  const errEl = document.getElementById(prefix + '-sol-error');

  if (!raw) {{
    document.getElementById(prefix + '-branchname').value = '';
    if (prefix === 'sb') document.getElementById('sb-region').value = 'Dindigul';
    if (errEl) errEl.style.display = 'none';
    el.classList.remove('error');
    return;
  }}

  const padded = raw.padStart(4, '0');
  const b = BRANCHES[padded];

  if (b) {{
    const bName = document.getElementById(prefix + '-branchname');
    bName.value = b.name;
    bName.classList.add('autofilled');

    if (prefix === 'sb') {{
      const bReg = document.getElementById('sb-region');
      bReg.value = 'Dindigul';
      bReg.classList.add('autofilled');

      const pc = document.getElementById('sb-pincode');
      if (!pc.value && b.pincode) pc.value = b.pincode;
    }}

    if (errEl) errEl.style.display = 'none';
    el.classList.remove('error');
  }} else {{
    document.getElementById(prefix + '-branchname').value = '';
    if (prefix === 'sb') document.getElementById('sb-region').value = 'Dindigul';

    if (errEl) {{
      errEl.textContent = '❌ Invalid SOL ID: Branch not found in branches.csv';
      errEl.style.display = 'block';
    }}
    el.classList.add('error');
  }}
}}

function setupMCC(prefix) {{
  const search = document.getElementById(prefix + '-mcc-search');
  const drop = document.getElementById(prefix + '-mcc-dropdown');
  const hidden = document.getElementById(prefix + '-mcc-value');
  const sel = document.getElementById(prefix + '-mcc-selected');

  search.addEventListener('input', () => {{
    const q = search.value.toLowerCase().trim();
    drop.innerHTML = '';
    if (!q) {{ drop.classList.remove('open'); return; }}

    const matches = MCC_LIST.filter(m => m.code.includes(q) || m.desc.toLowerCase().includes(q)).slice(0, 35);
    if (matches.length === 0) {{
      drop.innerHTML = '<div class="mcc-item" style="color:var(--muted)">No MCC code found</div>';
    }} else {{
      matches.forEach(m => {{
        const item = document.createElement('div');
        item.className = 'mcc-item';
        item.innerHTML = `<span class="code">${{m.code}}</span>${{m.desc}}`;
        item.onclick = () => {{
          hidden.value = m.code;
          search.value = m.code + ' - ' + m.desc;
          sel.textContent = 'Selected: ' + m.code + ' (' + m.desc + ')';
          sel.classList.add('show');
          drop.classList.remove('open');
        }};
        drop.appendChild(item);
      }});
    }}
    drop.classList.add('open');
  }});

  search.addEventListener('focus', () => {{
    if (search.value) drop.classList.add('open');
  }});
}}

function getGPS(prefix) {{
  const btn = document.getElementById(prefix + '-gps-btn');
  const status = document.getElementById(prefix + '-gps-status');
  if (!navigator.geolocation) {{ showToast('GPS not supported by your browser', 'error'); return; }}
  btn.disabled = true;
  btn.textContent = '⏳ Locating...';
  status.textContent = 'Fetching current position...';

  navigator.geolocation.getCurrentPosition(
    pos => {{
      const lat = pos.coords.latitude.toFixed(6);
      const lng = pos.coords.longitude.toFixed(6);
      document.getElementById(prefix + '-lat').value = lat;
      document.getElementById(prefix + '-lng').value = lng;
      status.textContent = '✓ Location captured (Accuracy: ±' + Math.round(pos.coords.accuracy) + 'm)';
      btn.disabled = false;
      btn.textContent = '📍 Capture GPS';
    }},
    err => {{
      status.textContent = 'Location error: ' + err.message;
      btn.disabled = false;
      btn.textContent = '📍 Capture GPS';
    }},
    {{ enableHighAccuracy: true, timeout: 10000 }}
  );
}}

function validateFormFields() {{
  let valid = true;
  document.querySelectorAll('.field input, .field select').forEach(e => e.classList.remove('error'));

  function check(id) {{
    const el = document.getElementById(id);
    if (!el || !el.value.trim()) {{
      if (el) el.classList.add('error');
      valid = false;
    }}
  }}

  if (currentType === 'qr') {{
    check('qr-merchantname'); check('qr-accountno');
    check('qr-ifsc'); check('qr-mobile'); check('qr-email'); check('qr-merchanttype');
    check('qr-lat'); check('qr-lng'); check('qr-addr1'); check('qr-postoffice');
    check('qr-pincode'); check('qr-district'); check('qr-subdistrict');
    if (!document.getElementById('qr-mcc-value').value) {{
      document.getElementById('qr-mcc-search').classList.add('error');
      valid = false;
    }}
    if (document.getElementById('qr-require-sb').checked) {{
      const solRaw = document.getElementById('qr-solid').value.replace(/\\D/g, '');
      const padded = solRaw.padStart(4, '0');
      if (!solRaw || !BRANCHES[padded]) {{
        document.getElementById('qr-solid').classList.add('error');
        showToast('Invalid SOL ID. Must be a valid branch code from branches.csv', 'error');
        valid = false;
      }}
    }}
  }}

  if (currentType === 'soundbox') {{
    const solRaw = document.getElementById('sb-solid').value.replace(/\\D/g, '');
    const padded = solRaw.padStart(4, '0');
    if (!solRaw || !BRANCHES[padded]) {{
      document.getElementById('sb-solid').classList.add('error');
      showToast('Invalid SOL ID. Must be a valid branch code from branches.csv', 'error');
      valid = false;
    }}
    check('sb-vpa'); check('sb-accountname');
    check('sb-mobile'); check('sb-address'); check('sb-pincode');
    check('sb-city'); check('sb-state');
    if (!document.getElementById('sb-mcc-value').value) {{
      document.getElementById('sb-mcc-search').classList.add('error');
      valid = false;
    }}
  }}

  if (currentType === 'lead') {{
    const solRaw = document.getElementById('lead-solid').value.replace(/\\D/g, '');
    const padded = solRaw.padStart(4, '0');
    if (!solRaw || !BRANCHES[padded]) {{
      document.getElementById('lead-solid').classList.add('error');
      showToast('Invalid SOL ID. Must be a valid branch code from branches.csv', 'error');
      valid = false;
    }}
    check('lead-accountno'); check('lead-merchantname');
    check('lead-mobile'); check('lead-devices');
    check('lead-contactname'); check('lead-contactmobile');

    const acc = document.getElementById('lead-accountno').value.trim();
    if (acc.length !== 15) {{
      document.getElementById('lead-accountno').classList.add('error');
      showToast('Current Account number must be exactly 15 digits', 'error');
      valid = false;
    }}
  }}

  if (!valid) showToast('Please fill in all mandatory fields before submitting', 'error');
  return valid;
}}

function collectQR() {{
  const lat = parseFloat(document.getElementById('qr-lat').value || 0).toFixed(6);
  const lng = parseFloat(document.getElementById('qr-lng').value || 0).toFixed(6);
  const isSbRequired = document.getElementById('qr-require-sb').checked;
  const staff = currentActiveStaff || {{}};

  return {{
    MERCHANTNAME: document.getElementById('qr-merchantname').value.trim(),
    MERCHANTVPA: document.getElementById('qr-merchantvpa').value.trim() || "Pending Generation",
    ACCOUNTNO: document.getElementById('qr-accountno').value.trim(),
    IFSC: document.getElementById('qr-ifsc').value.trim().toUpperCase(),
    MOBILENO: document.getElementById('qr-mobile').value.trim(),
    MCCCODE: document.getElementById('qr-mcc-value').value,
    ACTIVE: "1",
    ONBORDINGTYPE: "M",
    GSTNO: document.getElementById('qr-gstno').value.trim(),
    EMAILID: document.getElementById('qr-email').value.trim(),
    MERCHANTTYPE: document.getElementById('qr-merchanttype').value,
    LATITUDE: lat,
    LONGITUDE: lng,
    ADDRESS1: document.getElementById('qr-addr1').value.trim(),
    ADDRESS2: document.getElementById('qr-addr2').value.trim(),
    POSTOFFICENAME: document.getElementById('qr-postoffice').value.trim(),
    PINCODE: document.getElementById('qr-pincode').value.trim(),
    STATE: "TamilNadu",
    DISTRICT: document.getElementById('qr-district').value.trim(),
    SUBDISTRICT: document.getElementById('qr-subdistrict').value.trim(),
    SOUNDBOX_REQUIRED: isSbRequired ? "Yes" : "No",
    SOL_ID: isSbRequired ? document.getElementById('qr-solid').value.padStart(4, '0') : "",
    SOUNDBOX_LANG: isSbRequired ? (document.querySelector('input[name="qr-sb-lang"]:checked')?.value || 'ta') : "",
    STAFF_ROLL: staff.roll || "",
    STAFF_NAME: staff.name || ""
  }};
}}

function collectSB() {{
  const solRaw = document.getElementById('sb-solid').value.replace(/\\D/g,'');
  const lang = document.querySelector('input[name="sb-lang"]:checked')?.value || 'ta';
  const staff = currentActiveStaff || {{}};

  return {{
    SOL_ID: solRaw.padStart(4, '0'),
    BRANCH_NAME: document.getElementById('sb-branchname').value.trim(),
    REGION: "Dindigul",
    VPA: document.getElementById('sb-vpa').value.trim(),
    ACCOUNT_NAME: document.getElementById('sb-accountname').value.trim(),
    ADDRESS: document.getElementById('sb-address').value.trim(),
    PIN_CODE: document.getElementById('sb-pincode').value.trim(),
    CITY: document.getElementById('sb-city').value.trim(),
    STATE: document.getElementById('sb-state').value.trim(),
    MCC: document.getElementById('sb-mcc-value').value,
    MOBILE_NUMBER: document.getElementById('sb-mobile').value.trim(),
    LANGUAGE: lang,
    STAFF_ROLL: staff.roll || "",
    STAFF_NAME: staff.name || ""
  }};
}}

function collectLead() {{
  const solRaw = document.getElementById('lead-solid').value.replace(/\\D/g,'');
  const product = document.querySelector('input[name="lead-product"]:checked')?.value || '3 in 1 POS (QR Code + POS + Soundbox)';
  const staff = currentActiveStaff || {{}};

  return {{
    PRODUCT: product,
    SOL_ID: solRaw.padStart(4, '0'),
    BRANCH_NAME: document.getElementById('lead-branchname').value.trim(),
    ACCOUNT_NO: document.getElementById('lead-accountno').value.trim(),
    MERCHANT_NAME: document.getElementById('lead-merchantname').value.trim(),
    MOBILE_NO: document.getElementById('lead-mobile').value.trim(),
    NO_OF_DEVICES: document.getElementById('lead-devices').value.trim(),
    CONTACT_NAME: document.getElementById('lead-contactname').value.trim(),
    CONTACT_MOBILE: document.getElementById('lead-contactmobile').value.trim(),
    STAFF_ROLL: staff.roll || "",
    STAFF_NAME: staff.name || ""
  }};
}}

async function executeSubmission() {{
  const payload = {{ type: currentType }};
  let newItem = null;

  if (currentType === 'qr') {{
    newItem = collectQR();
    payload.qr = newItem;
    if (!TRACKING_DATA.qr) TRACKING_DATA.qr = [];
    TRACKING_DATA.qr.unshift({{ ...newItem, STATUS: 'Pending Review', COMPLETED_DATE: 'Just now' }});
  }}
  if (currentType === 'soundbox') {{
    newItem = collectSB();
    payload.sb = newItem;
    if (!TRACKING_DATA.sb) TRACKING_DATA.sb = [];
    TRACKING_DATA.sb.unshift({{ ...newItem, STATUS: 'Pending Review', COMPLETED_DATE: 'Just now' }});
  }}
  if (currentType === 'lead') {{
    newItem = collectLead();
    payload.lead = newItem;
    if (!TRACKING_DATA.lead) TRACKING_DATA.lead = [];
    TRACKING_DATA.lead.unshift({{ ...newItem, STATUS: 'Pending Review', UPDATED_DATE: 'Just now' }});
  }}

  // OPTIMISTIC IMMEDIATE UPDATE TO TRACKING TABLE
  renderStatusTable();

  const btn = document.getElementById('btn-submit');
  btn.disabled = true;
  btn.textContent = 'Submitting...';

  try {{
    await fetch(APPS_SCRIPT_URL, {{
      method: 'POST',
      mode: 'no-cors',
      headers: {{ 'Content-Type': 'text/plain;charset=utf-8' }},
      body: JSON.stringify(payload)
    }});

    showToast('✅ Lead / Application submitted successfully!', 'success');
    setTimeout(() => {{
      resetForm();
      loadStatusData();
    }}, 1200);

  }} catch(e) {{
    showToast('Submission error: ' + e.message, 'error');
  }} finally {{
    btn.disabled = false;
    btn.textContent = 'Submit Application / Lead';
  }}
}}

function resetForm() {{
  document.getElementById('mainForm').reset();
  document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
  ['qr-section', 'sb-section', 'lead-section', 'submit-zone'].forEach(id => document.getElementById(id).classList.add('hidden'));
  document.querySelectorAll('.mcc-selected').forEach(e => e.classList.remove('show'));
  document.querySelectorAll('[id$="-mcc-value"]').forEach(e => e.value = '');
  document.querySelectorAll('.autofilled').forEach(e => e.classList.remove('autofilled'));
  document.querySelectorAll('.sol-error').forEach(e => e.style.display = 'none');
  document.getElementById('qr-sb-fields').classList.add('hidden');
  document.getElementById('sb-region').value = 'Dindigul';
  onLeadProductChange('3 in 1 POS (QR Code + POS + Soundbox)');
  currentType = null;

  window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}

// ─────────────────────────────────────────────
// TRACKING & STATUS TAB
// ─────────────────────────────────────────────
async function loadStatusData() {{
  try {{
    const res = await fetch(APPS_SCRIPT_URL);
    const data = await res.json();
    if (data && (data.qr || data.sb || data.lead)) {{
      TRACKING_DATA = data;
      renderStatusTable();
    }}
  }} catch(e) {{
    console.error("Status load error:", e);
  }}
}}

function renderStatusTable() {{
  const query = document.getElementById('statusSearch').value.toLowerCase().trim();
  const tbody = document.getElementById('statusTableBody');

  let items = [];
  (TRACKING_DATA.qr || []).forEach(item => {{
    items.push({{ ...item, _type: 'QR', _name: item.MERCHANTNAME, _vpa: item.MERCHANTVPA, _acc: item.ACCOUNTNO, _mobile: item.MOBILENO, _loc: item.DISTRICT || item.CITY || '-' }});
  }});
  (TRACKING_DATA.sb || []).forEach(item => {{
    items.push({{ ...item, _type: 'Soundbox', _name: item.ACCOUNT_NAME, _vpa: item.VPA, _acc: '-', _mobile: item.MOBILE_NUMBER, _loc: (item.BRANCH_NAME || '') + ' (' + (item.SOL_ID || '') + ')' }});
  }});
  (TRACKING_DATA.lead || []).forEach(item => {{
    items.push({{ ...item, _type: 'Lead', _name: item.MERCHANT_NAME, _vpa: item.PRODUCT, _acc: item.ACCOUNT_NO, _mobile: item.MOBILE_NO, _loc: (item.BRANCH_NAME || '') + ' (' + (item.SOL_ID || '') + ')' }});
  }});

  if (query) {{
    items = items.filter(item => {{
      return (item._name || '').toLowerCase().includes(query) ||
             (item._vpa || '').toLowerCase().includes(query) ||
             String(item._mobile || '').includes(query) ||
             String(item._acc || '').includes(query) ||
             (item._loc || '').toLowerCase().includes(query);
    }});
  }}

  if (items.length === 0) {{
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No matching items found.</td></tr>`;
    return;
  }}

  tbody.innerHTML = items.map(item => {{
    let typeBadge = '';
    if (item._type === 'QR') typeBadge = '<span class="badge-type qr">📲 QR Code</span>';
    else if (item._type === 'Soundbox') typeBadge = '<span class="badge-type sb">🔊 Soundbox</span>';
    else typeBadge = '<span class="badge-type lead">💳 Product Lead</span>';

    const st = item.STATUS || 'Pending Review';
    let statusBadge = '';
    if (st === 'Completed' || st === 'Merchant Onboarded') {{
      statusBadge = `<span class="badge-status completed">✓ Onboarded</span>`;
    }} else if (st === 'Forwarded to Vendor') {{
      statusBadge = `<span class="badge-status vendor">🚚 With Vendor</span>`;
    }} else if (st === 'Rejected / Closed') {{
      statusBadge = `<span class="badge-status rejected">❌ Closed</span>`;
    }} else {{
      statusBadge = `<span class="badge-status pending">⏳ Pending Review</span>`;
    }}

    const createdStr = item.CREATED_DATE ? `<div style="font-size:0.72rem;color:var(--text);font-weight:600;margin-top:3px">📅 Created: ${item.CREATED_DATE}</div>` : '';
    const dateStr = item.COMPLETED_DATE || item.UPDATED_DATE ? `⏱ Updated: ${item.COMPLETED_DATE || item.UPDATED_DATE}` : '';
    const remarksStr = item.VENDOR_REMARKS ? `<div style="font-size:0.72rem;color:var(--muted);font-style:italic">Remarks: ${{item.VENDOR_REMARKS}}</div>` : '';

    let detailCol = '';
    if (item._type === 'Lead') {{
      detailCol = `<div style="font-size:0.75rem"><strong>Devices:</strong> ${{item.NO_OF_DEVICES || 1}}</div><div style="font-size:0.72rem;color:var(--muted)">Contact: ${{item.CONTACT_NAME || ''}} (${{item.CONTACT_MOBILE || ''}})</div>`;
    }} else {{
      detailCol = item.QR_PDF_URL 
        ? `<a href="${{item.QR_PDF_URL}}" target="_blank" class="btn-pdf">📄 Download QR PDF</a>` 
        : `<span style="font-size:0.75rem;color:var(--muted)">Pending QR</span>`;
    }}

    return `
      <tr>
        <td>${{typeBadge}}</td>
        <td><strong>${{item._name || '-'}}</strong></td>
        <td><div>${{item._vpa || '-'}}</div><div style="font-size:0.74rem;color:var(--muted)">Acc: ${{item._acc || '-'}}</div></td>
        <td>${{item._mobile || '-'}}</td>
        <td>${{item._loc || '-'}}</td>
        <td>${{statusBadge}}<div style="font-size:0.72rem;color:var(--muted);margin-top:2px">${{dateStr}}</div>${{remarksStr}}</td>
        <td>${{detailCol}}</td>
      </tr>
    `;
  }}).join('');
}}

let toastTimer;
function showToast(msg, type='') {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show ' + type;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.className = '', 4000);
}}
</script>
</body>
</html>
"""

with open(os.path.join(form_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print("Updated index.html with optimistic UI updates and fast reads!")
