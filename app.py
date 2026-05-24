from flask import Flask, request, jsonify, render_template_string
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# ============================================
# YOUR DATABASE API
# ============================================
DB_API = "https://bronx-db.up.railway.app"

# ============================================
# ADMIN PANEL HTML
# ============================================
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>BRONX ADMIN - KEY MANAGER</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:#0a0a0a;color:#bf00ff;font-family:monospace;padding:15px}
        .header{text-align:center;padding:20px;border:2px solid #bf00ff;border-radius:15px;margin-bottom:20px;background:#111}
        h1{font-size:24px;text-shadow:0 0 20px #bf00ff}
        .card{background:#111;border:1px solid #bf00ff;border-radius:10px;padding:20px;margin:15px 0}
        h3{color:#bf00ff;margin-bottom:15px}
        input,select{width:100%;padding:12px;background:#000;border:1px solid #bf00ff;border-radius:8px;color:#bf00ff;margin:8px 0;font-family:monospace}
        label{color:#888;font-size:11px;display:block;margin-top:8px}
        .btn{width:100%;padding:12px;background:#bf00ff;color:#000;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:8px 0;font-size:14px}
        .btn:hover{box-shadow:0 0 20px #bf00ff}
        .btn-red{background:#ff3333;color:#fff}
        .btn-green{background:#00cc44;color:#000}
        .row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
        .key-card{background:#0a0a0a;border:1px solid #333;padding:10px;margin:6px 0;border-radius:6px}
        .badge{padding:3px 10px;border-radius:20px;font-size:10px}
        .active{background:#0f02;color:#0f0}
        .expired{background:#f002;color:#f00}
        .stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:15px;margin-bottom:20px}
        .stat{background:#111;border:1px solid #bf00ff;padding:15px;text-align:center;border-radius:10px}
        .stat-val{font-size:28px;color:#bf00ff;font-weight:bold}
        .stat-label{color:#888;font-size:11px}
        .toast{position:fixed;bottom:20px;right:20px;background:#bf00ff;color:#000;padding:12px 20px;border-radius:8px;font-weight:bold;z-index:999;display:none}
    </style>
</head>
<body>
    <div class="header">
        <h1>👑 BRONX ADMIN PANEL</h1>
        <p style="color:#888;font-size:10px">Database: bronx-db.up.railway.app</p>
    </div>
    
    <div class="stats">
        <div class="stat"><div class="stat-val" id="totalKeys">0</div><div class="stat-label">TOTAL KEYS</div></div>
        <div class="stat"><div class="stat-val" id="activeKeys">0</div><div class="stat-label">ACTIVE</div></div>
        <div class="stat"><div class="stat-val" id="totalUsed">0</div><div class="stat-label">TOTAL USED</div></div>
    </div>
    
    <div class="card">
        <h3>🔑 GENERATE API KEY</h3>
        <div class="row">
            <div><label>KEY NAME</label><input type="text" id="keyName" placeholder="BRONX_ABC"></div>
            <div><label>OWNER</label><input type="text" id="owner" value="Premium User"></div>
        </div>
        <div class="row">
            <div><label>LIMIT</label><input type="number" id="limit" value="100"></div>
            <div><label>EXPIRY (Days)</label><input type="number" id="expiry" value="365"></div>
        </div>
        <button class="btn" onclick="generateKey()">🚀 GENERATE KEY</button>
    </div>
    
    <div class="card">
        <h3>📋 ALL KEYS</h3>
        <button class="btn btn-green" onclick="loadKeys()">🔄 REFRESH</button>
        <div id="keysList" style="max-height:400px;overflow:auto;margin-top:10px"></div>
    </div>
    
    <div id="toast" class="toast"></div>
    
    <script>
        function toast(msg){let t=document.getElementById('toast');t.textContent=msg;t.style.display='block';setTimeout(()=>t.style.display='none',2000)}
        
        async function generateKey(){
            let name=document.getElementById('keyName').value;
            if(!name){toast('❌ Enter key name!');return}
            let owner=document.getElementById('owner').value||'User';
            let limit=parseInt(document.getElementById('limit').value)||100;
            let expiry=parseInt(document.getElementById('expiry').value)||365;
            
            // ✅ SAVE TO DATABASE via Admin API
            let resp=await fetch('/admin/generate',{
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({key:name, owner, limit, expiry})
            });
            let data=await resp.json();
            if(data.success){toast('✅ Key Generated!');loadKeys();}
            else toast('❌ '+data.error);
        }
        
        async function loadKeys(){
            let resp=await fetch('/admin/keys');
            let keys=await resp.json();
            
            if(keys.error){document.getElementById('keysList').innerHTML='<p style="color:#888">No keys</p>';return}
            
            let arr=Object.entries(keys);
            document.getElementById('totalKeys').textContent=arr.length;
            
            document.getElementById('keysList').innerHTML=arr.map(([k,v])=>{
                return `<div class="key-card">
                    <b style="color:#ff0">🔑 ${k}</b>
                    <span class="badge active">${v.status||'active'}</span><br>
                    👤 ${v.owner} | 📊 ${v.limit||'∞'} | ✅ ${v.used||0} | ⏰ ${v.expiry||'Never'}
                    <button onclick="deleteKey('${k}')" style="background:red;color:#fff;border:none;padding:3px 10px;border-radius:3px;cursor:pointer;margin-left:10px">🗑️</button>
                </div>`;
            }).join('');
        }
        
        async function deleteKey(key){
            if(!confirm('Delete '+key+'?'))return;
            await fetch('/admin/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key})});
            toast('✅ Deleted!');
            loadKeys();
        }
        
        loadKeys();
    </script>
</body>
</html>
"""

# ============================================
# ✅ ADMIN API ENDPOINTS (Save/Load from Railway)
# ============================================

@app.route('/admin/generate', methods=['POST'])
def admin_generate():
    """Generate key - Save to Railway DB"""
    try:
        body = request.get_json()
        key = body.get('key', '')
        owner = body.get('owner', 'User')
        limit = int(body.get('limit', 100))
        expiry_days = int(body.get('expiry', 365))
        
        if not key:
            return jsonify({"success": False, "error": "Key name required"}), 400
        
        expiry = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d") if expiry_days > 0 else "Never"
        
        # Get existing keys from Railway
        resp = requests.get(f"{DB_API}/api_keys")
        keys = resp.json() if resp.status_code == 200 else {}
        if isinstance(keys, dict) and 'error' in keys:
            keys = {}
        
        # Add new key
        keys[key] = {
            "owner": owner,
            "limit": limit,
            "used": 0,
            "expiry": expiry,
            "status": "active",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to Railway
        save_resp = requests.post(f"{DB_API}/api_keys", json=keys)
        
        return jsonify({"success": True, "key": key})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/keys')
def admin_keys():
    """Get all keys from Railway"""
    try:
        resp = requests.get(f"{DB_API}/api_keys")
        return jsonify(resp.json())
    except:
        return jsonify({})

@app.route('/admin/delete', methods=['POST'])
def admin_delete():
    """Delete key from Railway"""
    try:
        body = request.get_json()
        key = body.get('key', '')
        
        resp = requests.get(f"{DB_API}/api_keys")
        keys = resp.json() if resp.status_code == 200 else {}
        if isinstance(keys, dict) and key in keys:
            del keys[key]
            requests.post(f"{DB_API}/api_keys", json=keys)
        
        return jsonify({"success": True})
    except:
        return jsonify({"success": False}), 500

@app.route('/')
def home():
    return ADMIN_HTML

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
