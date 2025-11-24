// src/constants.js

export const CHARSET = [" ", "!", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/", ":", ";", "<", "=", ">", "?", "@", "[", "]", "^", "_", "{", "|", "}", "~"];

export const BASE = 30;
export const MAX_DELAY = 300;

const SCHEDULER = `S={t:{},g:{},c:0,o:0,i:0,d:{get false(){let t=S.t[S.c];do{let e=3*S.i;[t[e],S=>S][+(t[e+2]<S.g[t[e+1]])]()}while(++S.i<t.length/3);delete S.t[S.c],S.i=0}},run(t,e,l){let c=S.c-~e-1,g=S.t[c]=[S.t[c],[]][+!S.t[c]],i=g.length;g[i]=t,g[i+1]=[l,"0"][+!l],g[i+2]=S.o++},stop(t){S.g[t]=S.o++}};`;

const TICK_LOOP = `tick=()=>{S.d[!S.t[S.c]];S.c++};`;

const MUSIC_ENGINE = `
this.Music={
P:(()=>{let p=[],i=0;do{p[i]=Math.pow(2,(i-39)/12)}while(++i<120);return p})(),
D:(()=>{let d={},c=" !#$%&'()*+,-./:;<=>?@[]^_{|}~",i=0;do{d[c[i]]=i}while(++i<30);return d})(),
O:[0,-5,7,7,-13],
SND:["harp_pling","game_start_countdown_01","game_start_countdown_02","game_start_countdown_03","game_start_countdown_final"],
VOL:[1,.8,.6,.4,.2,.1],
play:function(s){
S.stop("mus");S.stop("dec");
let M=this,D=M.D,P=M.P,O=M.O,SND=M.SND,VOL=M.VOL;
let i=0,T=0,l=s.length;
const f=()=>{
let c=50;
do{
if(i>=l)return;
let v=0,k=0;
do{v=v*30+D[s[i++]]}while(++k<4);
let d=v%300;v=(v-d)/300;
let n=v%88;v=(v-n)/88;
let vol=v%6;
let snd=(v-vol)/6;
T+=d;
S.run(()=>{
let idx=n+O[snd];
idx=idx&-(idx>=0);
api.broadcastSound(SND[snd],VOL[vol],P[idx]);
},T,"mus");
}while(--c>0);
if(i<l)S.run(f,0,"dec");
};
S.run(f,0,"dec");
},
stop:function(){S.stop("mus");S.stop("dec");}
};
`;

export const SETUP_CODE = (SCHEDULER + TICK_LOOP + MUSIC_ENGINE).replace(/\n\s*/g, '');