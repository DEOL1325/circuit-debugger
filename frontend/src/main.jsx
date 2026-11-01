import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const seed = () => ({positive:'E1', negative:'E20', components:[
  {id:'R1',kind:'resistor',pins:['B5','B10']},
  {id:'D1',kind:'led',pins:['D10','D15']},
  {id:'W1',kind:'wire',pins:['A1','A5']},
  {id:'W2',kind:'wire',pins:['A15','A20']},
]});
const ink = {resistor:'#efb65b',led:'#b5f283',wire:'#76b8ff'};
const holePoint = hole => {
  const m=/^([A-J])(\d{1,2})$/.exec(hole);
  if (!m || +m[2] < 1 || +m[2] > 30) return null;
  const i=m[1].charCodeAt(0)-65;
  return [54+i*25+(i>4?36:0),43+(+m[2]-1)*16];
};

function Board({circuit,result}) {
  const faults = new Set(result?.findings.flatMap(f=>f.holes) || []);
  return <svg className="board" viewBox="0 0 400 570" role="img" aria-label="Connection map of a 30-row breadboard. A to E connect horizontally; F to J form separate strips.">
    <rect x="23" y="11" width="347" height="534" rx="16" fill="#e4e8e1"/>
    <rect x="166" y="31" width="29" height="491" rx="6" fill="#bac2b8"/>
    {'ABCDEFGHIJ'.split('').map(c=><text key={c} x={holePoint(c+'1')[0]} y="30" textAnchor="middle" fill="#53614e" fontSize="12">{c}</text>)}
    {Array.from({length:30},(_,i)=>i+1).map(row=><g key={row}>
      <text x="34" y={47+(row-1)*16} textAnchor="middle" fill="#64715f" fontSize="10">{row}</text>
      {'ABCDEFGHIJ'.split('').map(col=>{const [x,y]=holePoint(col+row); return <circle key={col} cx={x} cy={y} r="3" fill="#87937f"/>;})}
    </g>)}
    {circuit.components.map(c=>{
      const a=holePoint(c.pins[0]),b=holePoint(c.pins[1]); if(!a||!b)return null;
      const color=c.pins.some(p=>faults.has(p))?'#db543e':ink[c.kind];
      return <g key={c.id}><path d={`M${a} L${b}`} stroke="#15211c" strokeWidth="8" strokeLinecap="round"/><path d={`M${a} L${b}`} stroke={color} strokeWidth="4" strokeLinecap="round"/>
        {[a,b].map((p,i)=><circle key={i} cx={p[0]} cy={p[1]} r="5" fill={color} stroke="#15211c" strokeWidth="1.5"/>)}
        <rect x={(a[0]+b[0])/2+8} y={(a[1]+b[1])/2-9} width="30" height="18" rx="4" fill="#15211c"/>
        <text x={(a[0]+b[0])/2+23} y={(a[1]+b[1])/2+4} fontSize="11" fill={color} textAnchor="middle">{c.id}</text>
      </g>;
    })}
    {[[circuit.positive,'+','#d04c40'],[circuit.negative,'−','#293d31']].map(([h,label,color])=>{const p=holePoint(h);return p&&<g key={label}><circle cx={p[0]} cy={p[1]} r="9" fill={color}/><text x={p[0]} y={p[1]+4} fill="white" textAnchor="middle" fontSize="14">{label}</text></g>;})}
    <text x="195" y="563" textAnchor="middle" fill="#8b9b90" fontSize="12">Connection map · not an image detection result</text>
  </svg>;
}

function App(){
  const [circuit,setCircuit]=useState(seed);
  const [result,setResult]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [health,setHealth]=useState(null),[photo,setPhoto]=useState(null),[view,setView]=useState('map');
  const [marks,setMarks]=useState({}),[selected,setSelected]=useState('R1:0'),[proposals,setProposals]=useState([]);
  const [confirmed,setConfirmed]=useState(false),[source,setSource]=useState('Example connections');
  const input=useRef(); const version=useRef(0);
  const workbench=useRef(null);
  useEffect(()=>{fetch('/api/health').then(r=>r.json()).then(setHealth).catch(()=>setHealth({ok:false}));},[]);
  function change(next){version.current++;setCircuit(next);setResult(null);setConfirmed(false);setError('');}
  function preset(type){let next=seed();if(type==='open')next.components[0].pins[1]='B11';if(type==='reversed')next.components[1].pins.reverse();change(next);setPhoto(null);setMarks({});setProposals([]);setView('map');setSource(type==='good'?'Correct example':type==='open'?'Example: disconnected resistor':'Example: reversed LED');}
  function updatePin(i,p,value){const next=structuredClone(circuit);next.components[i].pins[p]=value.toUpperCase();change(next);}
  async function request(path,body){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Check the hole labels (A1–J30), component IDs, and input values.');return data;}
  async function analyze(){setBusy(true);setError('');const current=version.current;try{const data=await request('/api/check',circuit);if(current===version.current)setResult(data);}catch(e){setError(e.message);}finally{setBusy(false);}}
  async function detect(){setBusy(true);setError('');const current=version.current;try{const data=await request('/api/detect',{image:photo});if(current===version.current)setProposals(data.proposals);}catch(e){setError(e.message);}finally{setBusy(false);}}
  function upload(file){if(!file)return;if(!['image/jpeg','image/png','image/webp'].includes(file.type)){setError('Choose a JPEG, PNG, or WebP photo.');return;}if(file.size>8*1024*1024){setError('Choose a photo smaller than 8 MB.');return;}
    const reader=new FileReader();reader.onerror=()=>setError('Could not read the image. Please try another file.');reader.onload=()=>{change(seed());setPhoto(reader.result);setView('photo');setMarks({});setProposals([]);setSource(file.name);};reader.readAsDataURL(file);
  }
  function exportReport(){const blob=new Blob([JSON.stringify({project:'Circuit Debugger',version:'0.1.0',source,circuit,photo_marks:marks,result},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='circuit-check.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  const terminals=circuit.components.flatMap(c=>c.pins.map((hole,i)=>({key:`${c.id}:${i}`,label:`${c.id} ${c.kind==='led'?(i?'cathode':'anode'):`pin ${i+1}`} · ${hole}`,hole})));
  const faultHoles=new Set(result?.findings.flatMap(f=>f.holes)||[]);
  return <div className="app">
    <header><a className="brand" href="/" aria-label="Circuit Debugger home"><span className="brand-icon">⌁</span> circuit<span>debugger</span></a><span className="header-note">AI APPLICATIONS LAB <span className="version">PROTOTYPE 01</span></span></header>
    <section className="intro-hero" aria-labelledby="intro-title">
      <div className="hero-copy"><p className="hero-kicker"><span className="live-dot"/> A BETTER WAY TO DEBUG THE BASICS</p>
        <h1 id="intro-title">One misplaced wire.<br/><span>One clear next step.</span></h1>
        <p className="hero-lede">Enter your breadboard connections, run a check, and see where the circuit breaks.</p>
        <div className="hero-actions"><button className="hero-cta" onClick={()=>workbench.current?.scrollIntoView({behavior:'smooth',block:'start'})}>Open the workbench <span>↓</span></button><span className="hero-meta">LED + resistor · 30-row board</span></div>
        <p className="hero-note">A guided circuit checker for learning. Photo recognition is still experimental.</p>
      </div>
      <div className="hero-graphic" aria-hidden="true">
        <div className="orbit orbit-one"/><div className="orbit orbit-two"/>
        <svg className="hero-circuit" viewBox="0 0 460 330" fill="none">
          <path className="circuit-base" d="M63 165h72m0 0v-77h78m0 0 28 0 16-24 30 48 16-24h47v77h56"/>
          <path className="circuit-current" d="M63 165h72m0 0v-77h78m0 0 28 0 16-24 30 48 16-24h47v77h56"/>
          <rect x="188" y="75" width="54" height="30" rx="5" className="resistor-box"/><text x="215" y="95" textAnchor="middle" className="circuit-label">R1</text>
          <path d="M289 64v48l38-24-38-24Zm42 0v48" className="diode"/>
          <circle cx="63" cy="165" r="8" className="terminal terminal-plus"/><circle cx="404" cy="165" r="8" className="terminal terminal-minus"/>
          <text x="63" y="198" textAnchor="middle" className="power-label">V+</text><text x="404" y="198" textAnchor="middle" className="power-label">GND</text>
          <circle cx="135" cy="165" r="5" className="node"/><circle cx="215" cy="88" r="5" className="node node-delay"/><circle cx="331" cy="88" r="5" className="node node-delay-two"/>
        </svg>
        <div className="hero-caption"><span className="caption-line"/> SERIES CIRCUIT <span className="caption-index">01 / 03</span></div>
      </div>
      <div className="hero-bottom"><span>START WITH A SIMPLE LED CIRCUIT</span><span className="scroll-cue">SCROLL TO CHECK YOUR WIRING <b>↓</b></span></div>
    </section>
    <main>
      <div className="heading" ref={workbench} id="workbench"><div><p className="eyebrow">THE WORKBENCH</p><h2 className="workbench-title">Check the connections.</h2><p className="intro">Confirm the hole numbers, then trace a missing path.</p></div><div className="model-state"><span className="status-dot"/>{health?.vision_ready?'Vision model connected':'Manual confirmation mode'}<small>{health?.ok===false?'Backend unavailable · start the Python server':'LED + series resistor · 30-row board'}</small></div></div>
      <div className="workspace">
        <section className="panel canvas-panel" aria-label="Circuit image and connection map">
          <div className="panel-top"><div><span className="step">01</span><h2>Your circuit</h2></div><div className="segmented"><button className={view==='map'?'active':''} onClick={()=>setView('map')}>Connection map</button><button className={view==='photo'?'active':''} onClick={()=>setView('photo')}>Photo</button></div></div>
          <div className="source-line"><span className="tiny-square"/>{source}</div>
          <div className="canvas">
            {view==='map'?<Board circuit={circuit} result={result}/>:photo?<div className="photo-workspace"><div className="photo-wrap">
              <img src={photo} alt="Uploaded breadboard circuit" onClick={e=>{const r=e.currentTarget.getBoundingClientRect();setMarks({...marks,[selected]:{x:(e.clientX-r.left)/r.width,y:(e.clientY-r.top)/r.height}});}}/>
              <svg className="photo-overlay" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">{proposals.map((p,i)=><rect key={i} x={p.box[0]*100} y={p.box[1]*100} width={(p.box[2]-p.box[0])*100} height={(p.box[3]-p.box[1])*100} fill="none" stroke="#c5f68c" strokeWidth="0.5"/>)}</svg>
              {terminals.filter(t=>marks[t.key]).map(t=><span key={t.key} className={`photo-mark ${faultHoles.has(t.hole)?'fault':''}`} style={{left:`${marks[t.key].x*100}%`,top:`${marks[t.key].y*100}%`}} title={t.label}>{t.hole}</span>)}
            </div><label className="mark-control">Mark a terminal on the photo<select value={selected} onChange={e=>setSelected(e.target.value)}>{terminals.map(t=><option key={t.key} value={t.key}>{t.label}</option>)}</select></label><p className="muted">Choose a terminal, then click its position in the photo. Markers are yours, not AI predictions.</p>
            {health?.vision_ready&&<button className="secondary" disabled={busy} onClick={detect}>Suggest components with AI</button>}
            {proposals.length>0&&<div className="proposal-list"><strong>Unconfirmed model suggestions</strong>{proposals.map((p,i)=><p key={i}>{p.kind} · {Math.round(p.confidence*100)}% model score · {p.keypoints.length} terminal proposals</p>)}<p>Assign hole numbers in the connection table after inspecting these suggestions.</p></div>}
            </div>:<div className="empty-photo"><span className="upload-symbol">＋</span><h3>Bring your circuit into view</h3><p>Use a clear, top-down photo with<br/>the breadboard labels visible.</p><button className="secondary" onClick={()=>input.current.click()}>Choose a photo</button></div>}
          </div>
          <div className="canvas-footer"><span><i style={{background:ink.resistor}}/>Resistor</span><span><i style={{background:ink.led}}/>LED</span><span><i style={{background:ink.wire}}/>Wire</span><button className="text-button" onClick={()=>input.current.click()}>Upload photo ↗</button><input type="file" ref={input} accept="image/jpeg,image/png,image/webp" hidden onChange={e=>{upload(e.target.files[0]);e.target.value='';}}/></div>
        </section>
        <div className="right-column">
          <section className="panel reference"><div className="panel-top"><div><span className="step">REF</span><h2>LED in series</h2></div><span className="pill">REFERENCE</span></div><div className="schematic" aria-label="Positive supply connects through a resistor and then an LED to negative supply"><b>+</b><span className="trace"/><span className="resistor-symbol">R</span><span className="trace"/><span className="led-symbol">▷│</span><span className="trace"/><b>−</b></div><p>One resistor and one LED in series. The resistor may sit on either side of the LED.</p></section>
          <section className="panel connection-panel"><div className="panel-top"><div><span className="step">02</span><h2>Confirm connections</h2></div></div><p className="section-help">A–E share a row. F–J share a separate row. Power rails are outside this prototype.</p>
            {photo&&<p className="notice">The table starts with example values. Replace them with the connections in your photo.</p>}
            <div className="supply"><label>Supply +<input aria-label="Positive supply hole" value={circuit.positive} onChange={e=>change({...circuit,positive:e.target.value.toUpperCase()})} maxLength={3}/></label><label>Supply −<input aria-label="Negative supply hole" value={circuit.negative} onChange={e=>change({...circuit,negative:e.target.value.toUpperCase()})} maxLength={3}/></label></div>
            <div className="table-wrap"><table><thead><tr><th>Part</th><th>Pin 1</th><th>Pin 2</th><th><span className="sr-only">Remove</span></th></tr></thead><tbody>{circuit.components.map((c,i)=><tr key={c.id}><td><span className="part-id" style={{color:ink[c.kind]}}>{c.id}</span><small>{c.kind==='led'?'LED · anode → cathode':c.kind}</small></td>{c.pins.map((p,j)=><td key={j}><input aria-label={`${c.id} ${j===0?'pin 1':'pin 2'}`} maxLength={3} value={p} onChange={e=>updatePin(i,j,e.target.value)}/></td>)}<td>{c.kind==='wire'&&<button className="remove" aria-label={`Remove ${c.id}`} onClick={()=>{change({...circuit,components:circuit.components.filter(x=>x.id!==c.id)});setSelected('R1:0');}}>×</button>}</td></tr>)}</tbody></table></div>
            <button className="text-button add-wire" disabled={circuit.components.length>=30} onClick={()=>{let n=1;while(circuit.components.some(c=>c.id===`W${n}`))n++;change({...circuit,components:[...circuit.components,{id:`W${n}`,kind:'wire',pins:['A1','F1']}]});}}>＋ Add jumper wire</button>
            <label className="confirmation"><input type="checkbox" checked={confirmed} onChange={e=>{version.current++;setConfirmed(e.target.checked);if(!e.target.checked)setResult(null);}}/> {photo?'I checked all table entries against my photo.':'Check these example connections.'}</label>
            <button className="primary" onClick={analyze} disabled={busy||!confirmed}>{busy?'Checking…':'Check connections'}<span>↗</span></button>
          </section>
        </div>
      </div>
      <section className="panel results" aria-live="polite"><div className="panel-top"><div><span className="step">03</span><h2>{result?(result.status==='topology_pass'?'Topology check passed':`${result.findings.length} wiring ${result.findings.length===1?'issue':'issues'} found`):'Inspection results'}</h2></div>{result&&<button className="text-button" onClick={exportReport}>Download report ↓</button>}</div>
        {error&&<p className="error" role="alert">{error}</p>}
        {!result?<p className="result-empty">Confirm the connections above to run a check. Photo detection requires a trained model.</p>:<><div className="findings">{result.findings.map((f,i)=><article className="finding" key={i}><span className="fault-number">{String(i+1).padStart(2,'0')}</span><div><h3>{f.title}</h3><p>{f.detail}</p><div className="hole-tags">{f.holes.map((h,j)=><span key={j}>{h}</span>)}</div></div></article>)}{result.status==='topology_pass'&&<article className="pass"><h3>The marked wiring forms the expected series circuit.</h3><p>This confirms the topology you entered. Component values and physical operation still need checking.</p></article>}</div><p className="scope">{result.basis} {result.scope}</p></>}
      </section>
      <div className="examples"><span>EXPLORE AN EXAMPLE</span><button onClick={()=>preset('good')}>Correct circuit</button><button onClick={()=>preset('open')}>Disconnected resistor</button><button onClick={()=>preset('reversed')}>Reversed LED</button></div>
      <footer><span>CIRCUIT DEBUGGER / LAB BUILD 0.1</span><span>Disconnect power before changing physical wiring.</span></footer>
    </main>
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
