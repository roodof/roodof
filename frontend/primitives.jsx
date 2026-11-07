import React, {useState, useId} from 'react';
import {createRoot} from 'react-dom/client';
import {flushSync} from 'react-dom';
import {LayoutGroup, MotionConfig, motion, useReducedMotion} from 'motion/react';
import {createElement as createIcon} from 'lucide';

export const selectionSpring = {type:'spring', stiffness:400, damping:30};
function Icon({node}) {
 return <span className="ws-route-icon" aria-hidden="true" ref={element=>{
  if(element&&!element.firstChild)element.append(createIcon(node,{width:16,height:16,'stroke-width':1.6}));
 }}/>;
}
function TactileButton({children,...props}) {
 const reduced=useReducedMotion();
 return <motion.button type="button" whileTap={reduced?undefined:{scale:.98}} transition={reduced?{duration:0}:selectionSpring} {...props}>{children}</motion.button>;
}
export function mountNavigation(host,routes,words,onSelect) {
 let updateActive,updateWarning;
 function Navigation(){
  const [active,setActive]=useState('sessions'),[warning,setWarning]=useState({count:0,text:''});
  updateActive=setActive;updateWarning=setWarning;
  const id=useId(),reduced=useReducedMotion();
  return <MotionConfig reducedMotion="user"><LayoutGroup id={id}>
   {routes.map(([name,icon])=><TactileButton key={name} data-route={name} className={'ws-nav-item'+(active===name?' active':'')}
    aria-current={active===name?'page':undefined} aria-label={words[name]+(name==='quota'&&warning.count?' · '+words.warning:'')}
    title={name==='quota'&&warning.count?warning.text:words[name]} onClick={()=>onSelect(name)}>
    {active===name&&<motion.span className="ws-nav-indicator" layoutId="active-route" transition={reduced?{duration:0}:selectionSpring}/>}
    <Icon node={icon}/><span className="ws-route-label">{words[name]}</span>
    {name==='quota'&&warning.count>0&&<span className="ws-warning-count">{warning.count}</span>}
   </TactileButton>)}
  </LayoutGroup></MotionConfig>;
 }
 const root=createRoot(host);flushSync(()=>root.render(<Navigation/>));
 return {setActive:name=>updateActive(name),setWarning:(count,text)=>updateWarning({count,text})};
}
export function mountSegments(host,items,initialValue,onSelect){
 let update;
 function Segments(){
  const [value,setValue]=useState(initialValue),id=useId(),reduced=useReducedMotion();update=setValue;
  return <MotionConfig reducedMotion="user"><LayoutGroup id={id}>
   {items.map(([key,label])=><TactileButton key={key} data-value={key} aria-pressed={value===key} onClick={()=>onSelect(key)}>
    {value===key&&<motion.span className="wb-active-indicator" layoutId="active-segment" transition={reduced?{duration:0}:selectionSpring}/>}
    <span className="wb-segment-label">{label}</span>
   </TactileButton>)}
  </LayoutGroup></MotionConfig>;
 }
 const root=createRoot(host);flushSync(()=>root.render(<Segments/>));return {setValue:v=>update(v)};
}
