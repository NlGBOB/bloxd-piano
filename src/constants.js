import RAW_SYMBOLS from './unicode_1_byte_symbols.json';

export const PADDING_CHAR = RAW_SYMBOLS[0];

export const DATA_CHARSET = RAW_SYMBOLS.slice(1).filter(c =>
    c !== '`' && c !== '"' && c !== "'" && c !== '\\'
);

export const BASE = DATA_CHARSET.length;

export const MAX_DELAY = 1200;

const DATA_CHARSET_STR = DATA_CHARSET.join("");


export const SCHEDULER_CODE = `// --- The Scheduler ---
S={t:{},g:{},c:0,o:0,i:0,d:{get false(){let t=S.t[S.c];do{let e=3*S.i;[t[e],S=>S][+(t[e+2]<S.g[t[e+1]])]()}while(++S.i<t.length/3);delete S.t[S.c],S.i=0}},run(t,e,l){let c=S.c-~e-1,g=S.t[c]=[S.t[c],[]][+!S.t[c]],i=g.length;g[i]=t,g[i+1]=[l,"0"][+!l],g[i+2]=S.o++},stop(t){S.g[t]=S.o++}};`;

export const TICK_CORE = `S.d[!S.t[S.c]];S.c++`;

export const TICK_WRAPPER = `
tick=()=>{
    ${TICK_CORE}
    // Add other code here. It'll run after scheduled tasks
};`;

export const MUSIC_ENGINE_CODE = `
// --- Music Engine ---
this.Music={T:[1,1.0595,1.1225,1.1892,1.26,1.3348,1.4142,1.4983,1.5874,1.6818,1.7818,1.8877],D:(()=>{let c="${DATA_CHARSET_STR}",d={},i=0;for(;i<c.length;i++)d[c[i]]=i;return {m:d,b:c.length};})(),O:[9,4,16,16,-4],SND:["harp_pling","game_start_countdown_01","game_start_countdown_02","game_start_countdown_03","game_start_countdown_final"],VOL:[1,0.95,0.9,0.85,0.8,0.75,0.7,0.65,0.6,0.55,0.5,0.45,0.4,0.35,0.3,0.25,0.2,0.15,0.1,0.05],play:function(s){S.stop("mus");S.stop("dec");let M=this,D=M.D.m,B=M.D.b,T=M.T,O=M.O,SND=M.SND,VOL=M.VOL;let len=((D[s[0]]*B+D[s[1]])*B+D[s[2]])*B+D[s[3]];let i=4,limit=len+4;const f=()=>{let c=50,time=0,v,d;do{v=((D[s[i]]*B+D[s[i+1]])*B+D[s[i+2]])*B+D[s[i+3]];d=v%1200;if((c<1)&(d>0)){S.run(f,time,"dec");return}i+=4;v=(v-d)/1200;let n=v%88;v=(v-n)/88;let vol=v%20;let snd=(v-vol)/20;time+=d;S.run(()=>{let x=n+O[snd];x=x&-(x>=0);api.broadcastSound(SND[snd],VOL[vol],T[x%12]*(1<<(x/12|0))*0.0625);},time,"mus");c--;}while(i<limit)};if(limit>4)S.run(f,0,"dec");},stop:function(){S.stop("mus");S.stop("dec");}};""
`;

export const COORDINATE_HELPER = `
// --- Coordinate Helper (Remove this after setup!) ---
onPlayerChangeBlock = (playerId, x, y, z, fromBlock, toBlock) => {
   if(toBlock == "Code Block") {
       api.log("The coordinates of the code block are: ", x, y, z);
   }
};
`;