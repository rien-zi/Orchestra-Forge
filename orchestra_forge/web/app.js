'use strict';
const $ = id => document.getElementById(id);
const names = ['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'];
const state = {program:0,pitch:60,velocity:40,duration:.8,pattern:'note',base:48};
let instruments=[], currentUrl=null, activeRequest=false, pending=null, generation=0;
const favorites = [
  {program:0,label:'Soft piano',sub:'Clear & gentle',symbol:'♬'},
  {program:4,label:'Electric piano',sub:'Warm & rounded',symbol:'♫'},
  {program:8,label:'Celesta',sub:'A little enchanted',symbol:'✧'},
  {program:46,label:'Harp',sub:'Soft & flowing',symbol:'♩'}
];
const tips={0:'A rounded acoustic piano for gentle melodies.',1:'A bright piano with a clear, lively attack.',4:'A warm keyboard sound with a soft attack.',8:'Delicate bell-like accents. Try a soft touch in the middle register.',46:'A plucked orchestral harp with a flowing release.'};
function noteName(pitch){return names[pitch%12]+(Math.floor(pitch/12)-1);}
function selectedName(){return instruments[state.program]?.name || 'Acoustic Grand Piano';}
function share(){return `Audiolizer: ${selectedName()} (GM program ${state.program}, zero-based); ${noteName(state.pitch)} / MIDI ${state.pitch}; velocity ${state.velocity}; note length ${state.duration.toFixed(1)} s; ${state.pattern==='note'?'single note':state.pattern==='chord'?'major chord':'major-key phrase'}; listening volume ${$('volume').value}%; SoundFont: ${$('soundfont').textContent}.`;}
function update(){
  $('noteName').textContent=noteName(state.pitch);
  $('pitchValue').textContent=noteName(state.pitch);
  $('frequency').textContent=(440*Math.pow(2,(state.pitch-69)/12)).toFixed(1)+' Hz';
  $('midiLabel').textContent=`MIDI ${state.pitch}${state.pitch===60?' · Middle C':''}`;
  $('velocityValue').textContent=`${state.velocity} · ${state.velocity<50?'Soft':state.velocity<75?'Medium':'Strong'}`;
  $('durationValue').textContent=state.duration.toFixed(1)+' s';
  $('pitch').value=state.pitch; $('instrument').value=state.program;
  $('selectedInstrument').textContent=selectedName();
  $('instrumentTip').textContent=tips[state.program] || 'Try one note, then a short phrase to hear its character.';
  $('shareText').textContent=share();
  document.querySelectorAll('.favorite').forEach(button=>{
    const selected=Number(button.dataset.program)===state.program;
    button.classList.toggle('selected',selected);button.setAttribute('aria-pressed',String(selected));
  });
  document.querySelectorAll('.key').forEach(button=>{
    const selected=Number(button.dataset.pitch)===state.pitch;
    button.classList.toggle('selected',selected);button.setAttribute('aria-pressed',String(selected));
  });
}
function keyboard(){
  const container=$('keyboard');container.replaceChildren();
  const white=[];
  for(let pitch=state.base;pitch<=state.base+24;pitch++)if(![1,3,6,8,10].includes(pitch%12))white.push(pitch);
  let whiteCount=0;
  for(let pitch=state.base;pitch<=state.base+24;pitch++){
    const black=[1,3,6,8,10].includes(pitch%12);
    const button=document.createElement('button');button.type='button';button.className=`key ${black?'black':'white'}-key`;
    button.dataset.pitch=pitch;button.textContent=noteName(pitch);
    button.setAttribute('aria-label',`Play ${noteName(pitch)}, MIDI ${pitch}`);
    if(black){const width=100/white.length*.6;button.style.width=width+'%';button.style.left=(whiteCount*100/white.length-width/2)+'%';}
    else whiteCount++;
    button.addEventListener('click',()=>{state.pitch=pitch;update();requestPreview();});
    button.addEventListener('keydown',event=>{
      if(event.key==='ArrowLeft'||event.key==='ArrowRight'){
        event.preventDefault();state.pitch=Math.max(24,Math.min(96,state.pitch+(event.key==='ArrowRight'?1:-1)));
        revealPitch();update();requestPreview();
        document.querySelector(`.key[data-pitch="${state.pitch}"]`)?.focus();
      }
    });
    container.append(button);
  }
  $('keyboardRange').textContent=`${noteName(state.base)} – ${noteName(state.base+24)}`;
  $('octaveDown').disabled=state.base<=24;$('octaveUp').disabled=state.base>=72;
  update();
}
function revealPitch(){if(state.pitch<state.base||state.pitch>state.base+24){state.base=Math.max(24,Math.min(72,Math.floor((state.pitch-12)/12)*12));keyboard();}}
function halt(){const audio=$('audio');audio.pause();audio.currentTime=0;document.body.classList.remove('playing');}
function requestPreview(){
  generation++;pending={data:{program:state.program,pitch:state.pitch,velocity:state.velocity,duration:state.duration,pattern:state.pattern},id:generation};
  halt();$('status').textContent='Preparing your sound…';pump();
}
async function pump(){
  if(activeRequest||!pending)return;
  activeRequest=true;const request=pending;pending=null;
  $('play').disabled=true;
  try{
    const response=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request.data)});
    if(!response.ok){const problem=await response.json();throw new Error(problem.error||'Could not create preview.');}
    const blob=await response.blob();
    if(request.id!==generation)return;
    if(currentUrl)URL.revokeObjectURL(currentUrl);
    currentUrl=URL.createObjectURL(blob);$('audio').src=currentUrl;$('audio').volume=Number($('volume').value)/100;
    await $('audio').play();document.body.classList.add('playing');$('status').textContent=`Listening to ${selectedName()} · ${noteName(request.data.pitch)}`;
  }catch(error){if(request.id===generation)$('status').textContent=error.message;}
  finally{activeRequest=false;$('play').disabled=false;if(pending)pump();}
}
$('play').addEventListener('click',requestPreview);
$('stop').addEventListener('click',()=>{generation++;pending=null;halt();$('status').textContent='Stopped. Try another sound.';});
$('audio').addEventListener('ended',()=>{document.body.classList.remove('playing');$('status').textContent='How did that feel? Adjust a note, or copy your settings.';});
$('audio').addEventListener('error',()=>{$('status').textContent='The preview could not play. Try listening again.';document.body.classList.remove('playing');});
$('instrument').addEventListener('change',()=>{state.program=Number($('instrument').value);update();});
for(const id of ['pitch','velocity','duration'])$(id).addEventListener('input',()=>{state[id]=Number($(id).value);if(id==='pitch')revealPitch();update();});
$('volume').addEventListener('input',()=>{$('audio').volume=Number($('volume').value)/100;update();});
$('octaveDown').addEventListener('click',()=>{state.base=Math.max(24,state.base-12);keyboard();});
$('octaveUp').addEventListener('click',()=>{state.base=Math.min(72,state.base+12);keyboard();});
document.querySelectorAll('.pattern').forEach(button=>button.addEventListener('click',()=>{
  state.pattern=button.dataset.pattern;
  document.querySelectorAll('.pattern').forEach(item=>{const active=item===button;item.classList.toggle('active',active);item.setAttribute('aria-pressed',String(active));});update();
}));
$('copy').addEventListener('click',async()=>{
  try{await navigator.clipboard.writeText(share());$('copy').textContent='Copied ✓';setTimeout(()=>{$('copy').textContent='Copy settings ↗';},1800);}
  catch{const range=document.createRange();range.selectNodeContents($('shareText'));const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);$('status').textContent='Settings selected. Press ⌘C to copy.';}
});
async function init(){
  try{
    const response=await fetch('/api/instruments');if(!response.ok)throw new Error('Could not load instruments.');
    const data=await response.json();instruments=data.instruments;$('soundfont').textContent=data.soundfont;
    for(const instrument of instruments){const option=document.createElement('option');option.value=instrument.program;option.textContent=instrument.name;$('instrument').append(option);}
    for(const item of favorites){
      const button=document.createElement('button');button.className='favorite';button.dataset.program=item.program;
      const symbol=document.createElement('span');symbol.className='symbol';symbol.textContent=item.symbol;symbol.setAttribute('aria-hidden','true');
      const text=document.createElement('span');text.textContent=item.label;const small=document.createElement('small');small.textContent=item.sub;text.append(small);button.append(symbol,text);
      button.addEventListener('click',()=>{state.program=item.program;update();});$('favorites').append(button);
    }
    keyboard();
  }catch(error){$('status').textContent=error.message;$('play').disabled=true;}
}
init();
