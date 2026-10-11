/* Reversible manual edits, scoped to one project/work. Media and memory stay outside. */
(function(root){
 class History{
  constructor(limit=100){this.limit=limit;this.reset('',null)}
  reset(scope,value){this.scope=scope;this.current=structuredClone(value);this.past=[];this.future=[];this.group=null;this.at=0}
  sync(scope,value){if(this.scope!==scope||JSON.stringify(value)!==JSON.stringify(this.current))this.reset(scope,value)}
  record(value,group=null,at=Date.now()){
   if(JSON.stringify(value)===JSON.stringify(this.current))return;
   if(!group||group!==this.group||at-this.at>600){this.past.push(structuredClone(this.current));if(this.past.length>this.limit)this.past.shift()}
   this.current=structuredClone(value);this.future=[];this.group=group;this.at=at;
  }
  accept(value){this.current=structuredClone(value);this.group=null}
  undo(){if(!this.past.length)return null;this.future.push(this.current);this.current=this.past.pop();this.group=null;return structuredClone(this.current)}
  redo(){if(!this.future.length)return null;this.past.push(this.current);this.current=this.future.pop();this.group=null;return structuredClone(this.current)}
 }
 function shortcut(e,editable=false){
  if(e.isComposing||e.altKey)return null;const key=e.key.toLowerCase(),mod=e.metaKey||e.ctrlKey;
  if(mod&&key==='s'&&!e.shiftKey)return 'save';
  if(editable)return null;
  if(mod&&key==='z')return e.shiftKey?'redo':'undo';
  if(e.ctrlKey&&!e.metaKey&&key==='y')return 'redo';
  if(mod)return null;
  if(key==='backspace'||key==='delete')return 'delete';
  if(e.shiftKey)return null;
  if(key==='s')return 'split';if(e.code==='Space')return 'play';return null;
 }
 const api={History,shortcut};if(typeof module!=='undefined')module.exports=api;root.EditorHistory=api;
})(typeof window!=='undefined'?window:globalThis);
