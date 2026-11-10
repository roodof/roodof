import {mountSegments} from './primitives.jsx';

// Move existing controls once. Category changes never recreate forms or perform writes.
export function mountSettings({tr,page,show}){
 const text=(local,en)=>tr?local:en;
 const el=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value)n.textContent=value;return n;};
 const $=id=>document.getElementById(id);
 const entries=[['general',text('Genel','General')],['sources',text('Kayıt kaynakları','Record sources')],['alerts',t('usage_alerts')],['support',text('Yedek ve destek','Backup & support')]];
 const tabs=el('div','settings-tabs wb-segmented');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label',text('Ayar grupları','Settings groups'));page.prepend(tabs);
 const panels={};
 for(const [key] of entries){const panel=el('section','settings-group');panel.id='settings-panel-'+key;panel.dataset.settingsGroup=key;panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby','settings-tab-'+key);panel.tabIndex=0;panels[key]=panel;page.append(panel);}
 let active='general';
 function select(key){if(!panels[key])return;active=key;for(const [name,panel] of Object.entries(panels))panel.hidden=name!==key;control.setValue(key);}
 const control=mountSegments(tabs,entries,active,select,{tabPrefix:'settings'});
 const application=el('section','settings-application');
 application.append(el('h2','',text('Uygulama','Application')));
 for(const [id,label] of [['lang-toggle',text('Arayüz dili','Interface language')],['usage-update-open',text('Sürüm ve güncelleme','Version & updates')],['usage-help',text('Kullanım kılavuzu','User guide')]]){
  const action=$(id);if(!action)continue;
  const row=el('div','settings-application-row');row.append(el('span','',label),action);application.append(row);
 }
 panels.general.append(application);
 const starting=page.querySelector('.first-use-settings');
 panels.sources.append($('source-folders'));if(starting)panels.sources.append(starting);
 panels.alerts.append($('budget-watch'));
 function tool(key,title,note,...nodes){
  const details=el('details','settings-tool');details.dataset.settingsTool=key;
  const summary=el('summary'),words=el('span','settings-tool-words');words.append(el('strong','',title),el('span','',note));summary.append(words);
  const body=el('div','settings-tool-body');body.append(...nodes.filter(Boolean));details.append(summary,body);panels.support.append(details);return details;
 }
 const backup=page.querySelector('.backup-controls');
 tool('backup',text('Yedek al ve kurtar','Back up & recover'),text('Özel geçmişini bir dosyada sakla veya yedekten aç.','Save a private history copy or recover a backup.'),backup);
 const history=$('usage-archive-controls');history.classList.add('settings-tool');history.dataset.settingsTool='history';history.open=false;panels.support.append(history);
 tool('reconnect',text('Taşınan oturumu yeniden bağla','Reconnect a moved session'),text('Eski kaydındaki iş ve uyarı ayarlarını seçtiğin oturuma taşı.','Transfer saved work and alert settings to a chosen session.'),$('session-identity-status'),$('session-reconnections'));
 tool('diagnostics',text('Okuma sorunlarını incele','Inspect read issues'),text('Eksik kayıtların nedenini gör ve destek bilgisi hazırla.','See why records are missing and prepare support information.'),$('diagnostics'));
 tool('report',text('Kullanım raporu indir','Download a usage report'),text('Seçili ajan, dönem ve proje için JSON raporu.','JSON for the selected agent, period and project.'),page.querySelector('.ws-report'));
 select(active);
 return {reveal(target){
  const panel=target?.closest('[data-settings-group]');if(!panel)return;
  show('settings',true);select(panel.dataset.settingsGroup);
  for(let node=target.parentElement;node&&node!==panel;node=node.parentElement)if(node.tagName==='DETAILS')node.open=true;
 },select};
}
