import os, json, base64
from flask import Flask, request, jsonify, Response
import requests

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

app = Flask(__name__)

PROMPT = (
    "Ata ozer le-chanut sifrey limud. Build inventory from a shelf photo. "
    "Read all instructions below carefully and answer in Hebrew values.\n"
    "Identify EVERY distinct book title visible, INCLUDING a single lone copy and books "
    "at the edges of the photo. Do NOT skip a unique single book or merge it into a "
    "nearby group of different books - list each distinct title as its own row even if "
    "it has only one copy. Spine text may appear rotated (vertical, sideways, upside "
    "down) - read it in any orientation.\n"
    "IRON RULE - accuracy over completeness:\n"
    "1) Only write text you actually read clearly. If a spine is unreadable or you "
    "are unsure of the title, put in 'name' only what you are certain of, or the "
    "Hebrew words 'lo barur', and leave subject, grade and publisher empty. NEVER "
    "invent a name, subject or publisher that is not written in the image.\n"
    "2) count: count HOW MANY TIMES this exact title text appears on separate visible "
    "book spines/copies in the image (count the occurrences of the title text). Count "
    "each distinct physical copy once - do NOT double-count the same book if its title "
    "shows on both its spine and its cover. Count only what is visible; do not add hidden "
    "copies. If unsure, give the lower, safe number.\n"
    "Return ONLY a valid JSON array, no extra text, no code fences, no explanation.\n"
    "Each item keys: \"name\", \"subject\", \"grade\", \"publisher\", \"count\" (number), "
    "\"notes\" (short or \"\"). All values in Hebrew. \"\" if unknown. If no books, return []."
)

def parse_books(text):
    text = (text or "").replace("```json", "").replace("```", "").strip()
    s, e = text.find("["), text.rfind("]")
    if s >= 0 and e > s:
        try:
            arr = json.loads(text[s:e+1])
            if isinstance(arr, list):
                return arr
        except Exception:
            pass
    os_, oe = text.find("{"), text.rfind("}")
    if os_ >= 0 and oe > os_:
        try:
            o = json.loads(text[os_:oe+1])
            if isinstance(o.get("books"), list):
                return o["books"]
            if o.get("name"):
                return [o]
        except Exception:
            pass
    return []

@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")

@app.route("/scan", methods=["POST"])
def scan():
    if not OPENAI_API_KEY:
        return jsonify({"error": "missing_key", "msg": "Missing OPENAI_API_KEY in Railway."}), 500
    data = request.get_json(silent=True) or {}
    b64 = data.get("image", "")
    if not b64:
        return jsonify({"error": "no_image"}), 400
    payload = {
        "model": MODEL,
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64, "detail": "high"}}
        ]}]
    }
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer " + OPENAI_API_KEY, "Content-Type": "application/json"},
            json=payload, timeout=90)
        if r.status_code != 200:
            print("OPENAI ERROR:", r.status_code, r.text[:500], flush=True)
            return jsonify({"error": "api", "msg": r.text[:300]}), 502
        txt = r.json()["choices"][0]["message"]["content"]
        return jsonify({"books": parse_books(txt)})
    except Exception as ex:
        print("SERVER ERROR:", str(ex), flush=True)
        return jsonify({"error": "server", "msg": str(ex)[:300]}), 500

HTML = r"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>סורק מלאי - ספרי לימוד</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@500;700;900&family=Heebo:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
  :root{--paper:#f4ecdb;--paper-2:#ece1c9;--ink:#23362b;--ink-soft:#3f5446;--ochre:#c8772e;--ochre-deep:#a95a18;--line:#cdbf9e;--card:#fbf6ea;--red:#9c3b2e;--green:#3c6b4a}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Heebo',sans-serif;color:var(--ink);background:var(--paper);min-height:100vh;padding:22px 16px 60px;line-height:1.55}
  .wrap{max-width:880px;margin:0 auto}
  header{text-align:center;margin-bottom:24px}
  .kick{font-size:.8rem;letter-spacing:.2em;color:var(--ochre-deep);font-weight:700}
  h1{font-family:'Frank Ruhl Libre',serif;font-weight:900;font-size:clamp(2rem,7vw,3rem);margin:.1em 0;color:var(--ink)}
  h1 .u{color:var(--ochre);border-bottom:5px solid var(--ochre)}
  .sub{color:var(--ink-soft);max-width:540px;margin:0 auto}
  .card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;margin-bottom:20px;box-shadow:0 10px 30px -18px rgba(35,54,43,.5)}
  .field{margin-bottom:16px}
  label{display:block;font-weight:500;font-size:.9rem;margin-bottom:6px;color:var(--ink-soft)}
  input[type=text]{width:100%;padding:11px 13px;border:1px solid var(--line);border-radius:9px;background:#fffdf7;font-family:inherit;font-size:1rem;color:var(--ink)}
  input[type=text]:focus{outline:none;border-color:var(--ochre);box-shadow:0 0 0 3px rgba(200,119,46,.18)}
  .drop{border:2.5px dashed var(--line);border-radius:12px;background:#fffdf7;padding:30px 18px;text-align:center;cursor:pointer;transition:.18s}
  .drop:hover{border-color:var(--ochre);background:#fdf8ec}
  .drop .big{font-family:'Frank Ruhl Libre',serif;font-weight:700;font-size:1.3rem}
  .drop .small{color:var(--ink-soft);font-size:.9rem;margin-top:4px}
  .drop .ic{font-size:2.3rem;margin-bottom:6px}
  input[type=file]{display:none}
  .note{background:rgba(200,119,46,.1);border:1px solid rgba(200,119,46,.3);border-radius:10px;padding:12px 14px;font-size:.88rem;color:var(--ochre-deep);margin-top:14px}
  .queue{margin-top:14px;display:flex;flex-direction:column;gap:8px}
  .q-item{display:flex;align-items:center;gap:10px;font-size:.9rem;background:#fffdf7;border:1px solid var(--line);border-radius:8px;padding:8px 11px}
  .q-item .name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .spin{width:15px;height:15px;border:2.5px solid var(--line);border-top-color:var(--ochre);border-radius:50%;animation:sp .7s linear infinite;flex-shrink:0}
  .ok{color:var(--green);font-weight:700}.err{color:var(--red);font-weight:700;font-size:.82rem}
  .stats{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:16px}
  .stat{flex:1;min-width:120px;background:var(--ink);color:var(--paper);border-radius:11px;padding:14px 16px}
  .stat .n{font-family:'Frank Ruhl Libre',serif;font-weight:900;font-size:2rem;line-height:1;color:#f2d6a8}
  .stat .l{font-size:.82rem;opacity:.8;margin-top:3px}
  .tbl-head{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px}
  .tbl-head h2{font-family:'Frank Ruhl Libre',serif;font-weight:700;font-size:1.4rem}
  .actions{display:flex;gap:8px;flex-wrap:wrap}
  button.btn{font-family:inherit;font-weight:500;font-size:.92rem;cursor:pointer;border:1px solid var(--ink);background:var(--ink);color:var(--paper);padding:9px 16px;border-radius:9px}
  button.btn.ghost{background:transparent;color:var(--ink)}
  .table-scroll{overflow-x:auto;border:1px solid var(--line);border-radius:11px}
  table{width:100%;border-collapse:collapse;background:#fffdf7;min-width:620px}
  th{background:var(--paper-2);font-weight:700;font-size:.85rem;text-align:right;padding:11px 12px;border-bottom:2px solid var(--line);white-space:nowrap}
  td{padding:4px 6px;border-bottom:1px solid var(--line);font-size:.95rem}
  td input{width:100%;border:1px solid transparent;background:transparent;padding:7px 8px;border-radius:6px;font-family:inherit;font-size:.95rem;color:var(--ink)}
  td input:hover{border-color:var(--line)}
  td input:focus{outline:none;border-color:var(--ochre);background:#fff}
  td.qty input{text-align:center;font-weight:700;max-width:74px}
  td.del{width:38px;text-align:center}
  .x{cursor:pointer;color:var(--line);font-weight:700;font-size:1.1rem;border:none;background:none;padding:4px 8px;border-radius:6px}
  .x:hover{color:var(--red);background:rgba(156,59,46,.1)}
  .empty{text-align:center;padding:40px 20px;color:var(--ink-soft)}
  .empty .ic{font-size:2.6rem;opacity:.5}
  .hide{display:none}
  .toast{position:fixed;bottom:20px;right:50%;transform:translateX(50%);background:var(--green);color:#fff;padding:11px 20px;border-radius:10px;font-weight:500;z-index:9;max-width:90vw;text-align:center}
  @keyframes sp{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="kick">חזרה ללימודים · ספירת מלאי</div>
    <h1>סורק <span class="u">מלאי</span></h1>
    <p class="sub">צלמו מדף, וה־AI יקרא את הכותרים ויבנה טבלה. אפשר לתקן ידנית ולייצא לאקסל.</p>
  </header>

  <div class="card">
    <div class="field">
      <label for="loc">מיקום / מדף (לא חובה — יתווסף לספרים מהצילום הבא)</label>
      <input type="text" id="loc" placeholder="לדוגמה: מדף 3, כיתה ז׳">
    </div>
    <div class="drop" id="drop" tabindex="0" role="button">
      <div class="ic">📚</div>
      <div class="big">צלמו או בחרו תמונת מדף</div>
      <div class="small">אפשר כמה תמונות יחד · התמונה תוקטן אוטומטית</div>
    </div>
    <input type="file" id="file" accept="image/*" multiple capture="environment">
    <div class="queue" id="queue"></div>
    <div class="note">💡 ה־AI קורא שמות ספרים <b>בכל זווית</b> ולא ממציא — מה שלא קריא יסומן "לא ברור". ה<b>כמות</b> היא שדרות נראות בלבד — לאמת בעין.</div>
  </div>

  <div class="card">
    <div class="stats">
      <div class="stat"><div class="n" id="st-titles">0</div><div class="l">כותרים</div></div>
      <div class="stat"><div class="n" id="st-copies">0</div><div class="l">סך עותקים</div></div>
      <div class="stat"><div class="n" id="st-photos">0</div><div class="l">תמונות שעובדו</div></div>
    </div>
    <div class="tbl-head">
      <h2>המלאי</h2>
      <div class="actions">
        <button class="btn ghost" id="addRow">+ שורה</button>
        <button class="btn ghost" id="copyBtn">העתקה</button>
        <button class="btn" id="csvBtn">ייצוא לאקסל</button>
      </div>
    </div>
    <div class="table-scroll">
      <table><thead><tr>
        <th>שם הספר</th><th>מקצוע</th><th>כיתה</th><th>הוצאה</th><th>כמות</th><th>מיקום</th><th>הערות</th><th></th>
      </tr></thead><tbody id="tbody"></tbody></table>
    </div>
    <div class="empty" id="empty"><div class="ic">🗂️</div><p>עוד אין ספרים. צלמו מדף ראשון.</p></div>
  </div>
</div>
<script>
const $=s=>document.querySelector(s);
let rows=[],photoCount=0,uid=0;
const fileInput=$('#file'),drop=$('#drop'),queue=$('#queue'),tbody=$('#tbody'),empty=$('#empty');
drop.addEventListener('click',()=>fileInput.click());
drop.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' ')fileInput.click();});
drop.addEventListener('dragover',e=>{e.preventDefault();drop.style.borderColor='var(--ochre)';});
drop.addEventListener('dragleave',()=>drop.style.borderColor='');
drop.addEventListener('drop',e=>{e.preventDefault();drop.style.borderColor='';handleFiles(e.dataTransfer.files);});
fileInput.addEventListener('change',e=>handleFiles(e.target.files));
function handleFiles(files){[...files].forEach(f=>{if(f.type.startsWith('image/'))processImage(f);});fileInput.value='';}
async function prepareImage(file){
  let bmp,w,h;
  try{bmp=await createImageBitmap(file,{imageOrientation:'from-image'});w=bmp.width;h=bmp.height;}
  catch(e){bmp=await new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=()=>rej(new Error('x'));i.src=URL.createObjectURL(file);});w=bmp.naturalWidth;h=bmp.naturalHeight;}
  const max=1400,scale=Math.min(1,max/Math.max(w,h)),cw=Math.max(1,Math.round(w*scale)),ch=Math.max(1,Math.round(h*scale));
  const c=document.createElement('canvas');c.width=cw;c.height=ch;c.getContext('2d').drawImage(bmp,0,0,cw,ch);
  return c.toDataURL('image/jpeg',0.85).split(',')[1];
}
async function processImage(file){
  const loc=$('#loc').value.trim();
  const item=document.createElement('div');item.className='q-item';
  item.innerHTML='<div class="spin"></div><div class="name">'+esc(file.name)+'</div>';
  queue.prepend(item);
  for(let a=0;a<2;a++){
    try{
      const b64=await prepareImage(file);
      const resp=await fetch('/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:b64})});
      const data=await resp.json();
      if(data.error)throw new Error(data.msg||data.error);
      let added=0;
      (data.books||[]).forEach(b=>{if(!b||(!b.name&&!b.subject))return;rows.push({id:++uid,name:b.name||'',subject:b.subject||'',grade:b.grade||'',publisher:b.publisher||'',count:parseInt(b.count)||1,loc:loc||'',notes:b.notes||''});added++;});
      photoCount++;
      item.innerHTML=(added>0?'<span class="ok">✓</span>':'<span style="color:var(--ink-soft);font-weight:700">—</span>')+'<div class="name">'+esc(file.name)+'</div><span style="font-size:.82rem;color:var(--ink-soft)">'+(added>0?added+' ספרים':'לא זוהו ספרים')+'</span>';
      render();return;
    }catch(err){if(a===1)item.innerHTML='<span class="err">⚠</span><div class="name">'+esc(file.name)+'</div><span style="font-size:.8rem;color:var(--ink-soft)">שגיאה — נסו שוב</span>';}
  }
}
function render(){
  empty.classList.toggle('hide',rows.length>0);tbody.innerHTML='';
  rows.forEach(r=>{const tr=document.createElement('tr');
    tr.innerHTML='<td><input data-id="'+r.id+'" data-k="name" value="'+esc(r.name)+'"></td><td><input data-id="'+r.id+'" data-k="subject" value="'+esc(r.subject)+'"></td><td><input data-id="'+r.id+'" data-k="grade" value="'+esc(r.grade)+'"></td><td><input data-id="'+r.id+'" data-k="publisher" value="'+esc(r.publisher)+'"></td><td class="qty"><input data-id="'+r.id+'" data-k="count" value="'+esc(r.count)+'" inputmode="numeric"></td><td><input data-id="'+r.id+'" data-k="loc" value="'+esc(r.loc)+'"></td><td><input data-id="'+r.id+'" data-k="notes" value="'+esc(r.notes)+'"></td><td class="del"><button class="x" data-del="'+r.id+'">×</button></td>';
    tbody.appendChild(tr);});
  tbody.querySelectorAll('input').forEach(inp=>inp.addEventListener('input',e=>{const r=rows.find(x=>x.id==e.target.dataset.id);if(r)r[e.target.dataset.k]=e.target.value;stats();}));
  tbody.querySelectorAll('[data-del]').forEach(b=>b.addEventListener('click',e=>{rows=rows.filter(x=>x.id!=e.target.dataset.del);render();}));
  stats();
}
function stats(){$('#st-titles').textContent=rows.length;$('#st-copies').textContent=rows.reduce((s,r)=>s+(parseInt(r.count)||0),0);$('#st-photos').textContent=photoCount;}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');}
$('#addRow').addEventListener('click',()=>{rows.push({id:++uid,name:'',subject:'',grade:'',publisher:'',count:1,loc:$('#loc').value.trim(),notes:''});render();});
$('#csvBtn').addEventListener('click',()=>{if(!rows.length)return toast('אין נתונים');const h=['שם הספר','מקצוע','כיתה','הוצאה','כמות','מיקום','הערות'];const L=[h.join(',')];rows.forEach(r=>L.push([r.name,r.subject,r.grade,r.publisher,r.count,r.loc,r.notes].map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')));const b=new Blob(['\uFEFF'+L.join('\n')],{type:'text/csv;charset=utf-8;'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='מלאי-ספרי-לימוד.csv';a.click();toast('הקובץ ירד');});
$('#copyBtn').addEventListener('click',()=>{if(!rows.length)return toast('אין נתונים');const h=['שם הספר','מקצוע','כיתה','הוצאה','כמות','מיקום','הערות'];const L=[h.join('\t')];rows.forEach(r=>L.push([r.name,r.subject,r.grade,r.publisher,r.count,r.loc,r.notes].join('\t')));navigator.clipboard.writeText(L.join('\n')).then(()=>toast('הועתק'));});
function toast(m){const t=document.createElement('div');t.className='toast';t.textContent=m;document.body.appendChild(t);setTimeout(()=>t.remove(),2200);}
render();
</script>
</body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
