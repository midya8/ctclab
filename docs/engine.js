// Independent scalar implementation of established CTC. No model, corpus or network call.
const N=-Infinity;
const sum=a=>a.reduce((s,x)=>s+x,0);
const lse=a=>{let m=Math.max(...a);return m===N?N:m+Math.log(sum(a.map(x=>Math.exp(x-m))))};
export function collapse(path,blank){return path.filter((x,i)=>x!==blank&&(i===0||path[i-1]!==x))}
export function audit(spec){
 const exact=(o,keys)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).sort().join('|')===[...keys].sort().join('|');
 if(!exact(spec,['symbols','blank','logits','target']))throw Error('Exact fields: symbols, blank, logits, target');
 const {symbols,blank:b,logits:z,target:y}=spec,c=symbols?.length,t=z?.length;
 if(!Array.isArray(symbols)||c<2||c>4||new Set(symbols).size!==c||symbols.some(s=>typeof s!=='string'||s.length<1||s.length>12||!/^[\x21-\x7e]+$/.test(s)))throw Error('Two to four unique printable ASCII symbol labels, length 1..12');
 if(!Number.isInteger(b)||b<0||b>=c)throw Error('Blank index');
 if(!Array.isArray(y)||y.length>6||y.some(k=>!Number.isInteger(k)||k<0||k>=c||k===b))throw Error('At most six target labels, excluding blank');
 if(!Array.isArray(z)||t>6||c**t>1024||z.some(row=>!Array.isArray(row)||row.length!==c||row.some(v=>typeof v!=='number'||!Number.isFinite(v)||Math.abs(v)>1e6)))throw Error('Bounded rectangular finite logits; at most six frames and 1024 paths');
 const logs=z.map(row=>{let m=Math.max(...row),den=Math.log(sum(row.map(x=>Math.exp(x-m))));return row.map(x=>(x-m)-den)}),p=logs.map(row=>row.map(Math.exp));
 const ext=[b];for(const k of y)ext.push(k,b);const n=ext.length,edges=[];
 for(let s=0;s<n;s++)for(let d=s;d<=s+2&&d<n;d++)if(d!==s+2||(ext[d]!==b&&ext[d]!==ext[s]))edges.push([s,d]);
 const incoming=ext.map((_,s)=>edges.filter(e=>e[1]===s).map(e=>e[0])),outgoing=ext.map((_,s)=>edges.filter(e=>e[0]===s).map(e=>e[1])),ends=n===1?[0]:[n-2,n-1];
 const a=Array.from({length:t},()=>Array(n).fill(N)),back=Array.from({length:t},()=>Array(n).fill(N));let logz;
 if(t){a[0][0]=logs[0][b];if(n>1)a[0][1]=logs[0][ext[1]];for(let i=1;i<t;i++)for(let s=0;s<n;s++)a[i][s]=logs[i][ext[s]]+lse(incoming[s].map(q=>a[i-1][q]));for(const s of ends)back[t-1][s]=0;for(let i=t-2;i>=0;i--)for(let s=0;s<n;s++)back[i][s]=lse(outgoing[s].map(d=>logs[i+1][ext[d]]+back[i+1][d]));logz=lse(ends.map(s=>a[t-1][s]));}else logz=y.length?N:0;
 const possible=logz!==N,state=possible?a.map((row,i)=>row.map((v,s)=>Math.exp(v+back[i][s]-logz))):null,label=possible?a.map((_,i)=>symbols.map((_,k)=>sum(state[i].filter((v,s)=>ext[s]===k)))):null,grad=possible?p.map((row,i)=>row.map((v,k)=>v-label[i][k])):null,clean=mat=>mat.map(row=>row.map(v=>v===N?null:v));
 const dynamic={log_probabilities:logs,probabilities:p,extended_target:ext,transitions:edges,alpha:clean(a),beta:clean(back),possible,minimum_frames:y.length+y.slice(1).filter((k,i)=>k===y[i]).length,log_probability:possible?logz:null,probability:possible?Math.exp(logz):0,loss:possible?-logz:null,state_posteriors:state,label_posteriors:label,logit_gradients:grad};
 const paths=[],groups=new Map();
 function walk(path,score){if(path.length===t){const collapsed=collapse(path,b),key=JSON.stringify(collapsed);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(score);paths.push({path:[...path],collapsed,log_probability:score,probability:Math.exp(score),matches:key===JSON.stringify(y)});return}for(let k=0;k<c;k++)walk([...path,k],score+logs[path.length][k]);}walk([],0);
 const lex=(a,b)=>{for(let i=0;i<Math.min(a.length,b.length);i++)if(a[i]!==b[i])return a[i]-b[i];return a.length-b.length};
 const outputs=[...groups].map(([key,v])=>({labels:JSON.parse(key),log_probability:lse(v),probability:Math.exp(lse(v)),path_count:v.length,rank_bucket:Math.floor(lse(v)*1e8+0.5)})).sort((a,b)=>b.rank_bucket-a.rank_bucket||lex(a.labels,b.labels));
 const gp=z.map(row=>row.indexOf(Math.max(...row))),gc=collapse(gp,b),matched=paths.filter(p=>p.matches),ol=lse(matched.map(p=>p.log_probability)),gl=outputs.find(o=>JSON.stringify(o.labels)===JSON.stringify(gc)).log_probability;
 return {schema_version:1,ranking_resolution_nats:1e-8,spec:JSON.parse(JSON.stringify(spec)),dynamic,paths,outputs,oracle:{path_count:paths.length,matched_count:matched.length,log_probability:ol===N?null:ol,probability:ol===N?0:Math.exp(ol)},greedy:{path:gp,collapsed:gc},best_output:outputs[0],greedy_is_canonical_best:JSON.stringify(gc)===JSON.stringify(outputs[0].labels),greedy_output_log_probability:gl,greedy_log_gap:Math.max(...outputs.map(o=>o.log_probability))-gl};
}
