// Read the existing recorded totals; this view never estimates missing usage or billing.
export function mountSessionUsage({session,tr}) {
 const text=(local,en)=>tr?local:en;
 const el=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value!=null)n.textContent=value;return n;};
 const fmt=n=>new Intl.NumberFormat(tr?'tr-TR':'en-US').format(n);
 const block=el('section','wb-session-usage');block.setAttribute('aria-label',text('Kayıtlı kullanım','Recorded usage'));
 const heading=el('h3','',text('Kayıtlı kullanım','Recorded usage'));
 const metrics=el('div','wb-session-metrics');
 const tokens=el('div');tokens.append(el('small','',text('Toplam token','Total tokens')),el('strong','',fmt(session.total_tokens)));
 const priced=Number(session.api_priced_share)>0;
 const price=el('div');price.append(el('small','',t('stat_api')),el('strong','',priced?usageUsd(session.api_usd):'—'));
 if(!priced)price.append(el('small','session-price-state',text('Fiyat eksik','Price unavailable')));
 metrics.append(tokens,price);block.append(heading,metrics);
 const parts=[
  [text('Girdi','Input'),session.tokens.input,'input'],
  [text('Önbellek','Cache'),session.tokens.cache_read+session.tokens.cache_write,'cache'],
  [text('Çıktı','Output'),session.tokens.output,'output']
 ];
 const total=parts.reduce((sum,[,value])=>sum+value,0);
 const bar=el('div','session-token-bar');bar.setAttribute('aria-hidden','true');
 const legend=el('dl','session-token-legend');
 for(const [label,value,key] of parts){
  if(total>0&&value>0){const segment=el('span','token-part token-part-'+key);segment.style.flexGrow=String(value/total);bar.append(segment);}
  const item=el('div','token-key-'+key);item.append(el('dt','',label),el('dd','',fmt(value)));legend.append(item);
 }
 if(total>0)block.append(bar);
 block.append(legend);
 const notes=el('div','session-usage-notes');
 if(session.quality?.tokens_complete===false)notes.append(el('p','session-usage-partial',text('Token kaydı eksik; gösterilen toplam kısmi.','Token records are incomplete; the displayed total is partial.')));
 notes.append(el('p','',text('API fiyat karşılığı gerçek faturan veya abonelik harcaman değildir.','API price equivalent is not your actual bill or subscription spend.')));
 if(priced&&session.api_priced_share<0.9995)notes.append(el('p','',text('Kullanımın yalnız '+usagePct(session.api_priced_share)+' bölümü fiyatlandırılabildi.','Only '+usagePct(session.api_priced_share)+' of usage could be priced.')));
 block.append(notes);
 return block;
}
