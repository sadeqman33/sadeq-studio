import subprocess,unittest
from pathlib import Path

class KeyboardTests(unittest.TestCase):
 def test_reversible_edits_scope_grouping_and_text_shortcuts(self):
  script=r"""
const assert=require('node:assert/strict'),{History,shortcut}=require('./editor_history.js');
const h=new History(3),original={layers:[{id:'caption',text:'تعلم'}],timeline:[{id:'clip'}],fps:60};
h.sync('project/work',original);h.record({...original,layers:[]});
assert.deepEqual(h.undo(),original);assert.equal(h.redo().layers.length,0);
h.undo();h.record({...original,fps:30});assert.equal(h.redo(),null);
h.undo();assert.equal(h.current.fps,60);assert.equal(original.layers.length,1);
h.sync('project/other',original);assert.equal(h.undo(),null);assert.equal(h.redo(),null);
h.record({...original,fps:31},'text',1000);h.record({...original,fps:32},'text',1100);assert.equal(h.past.length,1);assert.equal(h.undo().fps,60);
h.record({...original,fps:31},'text',1000);h.record({...original,fps:32},'text',1700);assert.equal(h.past.length,2);
for(let n=0;n<10;n++)h.record({...original,fps:n});assert.equal(h.past.length,3);
const key=(key,extra={})=>({key,code:key===' '?'Space':key,...extra});
assert.equal(shortcut(key('Backspace')),'delete');assert.equal(shortcut(key('Delete')),'delete');
assert.equal(shortcut(key('z',{metaKey:true})),'undo');assert.equal(shortcut(key('Z',{metaKey:true,shiftKey:true})),'redo');
assert.equal(shortcut(key('z',{ctrlKey:true})),'undo');assert.equal(shortcut(key('y',{ctrlKey:true})),'redo');
assert.equal(shortcut(key('s',{metaKey:true}),true),'save');assert.equal(shortcut(key('Backspace'),true),null);assert.equal(shortcut(key('z',{metaKey:true}),true),null);
assert.equal(shortcut(key('Backspace',{metaKey:true})),null);assert.equal(shortcut(key('s',{altKey:true})),null);assert.equal(shortcut(key('z',{metaKey:true,isComposing:true})),null);
assert.equal(shortcut(key('s')),'split');assert.equal(shortcut(key(' ')),'play');
"""
  subprocess.run(['node','-e',script],cwd=Path(__file__).parent,check=True)
