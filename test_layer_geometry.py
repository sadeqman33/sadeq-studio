import subprocess,unittest
from pathlib import Path
class LayerGeometryTests(unittest.TestCase):
 def test_uniform_group_move_scale_preserves_editability_and_bounds(self):
  script=r"""
const assert=require('node:assert/strict'),g=require('./layer_geometry.js');
const rows=[{id:'text',type:'text',x:30,y:40,width:40,fontSize:80,start:1,end:3,text:'صادق'},{id:'icon',type:'icon',x:70,y:60,width:10,start:2,end:4,asset:'source'}];
assert.deepEqual(g.centre(rows),{x:50,y:50});
const moved=g.move(rows,10,5);assert.deepEqual(moved.map(l=>[l.x,l.y]),[[40,45],[80,65]]);
assert.equal(moved[0].start,1);assert.equal(moved[1].asset,'source');assert.equal(rows[0].x,30);
const clamp=g.move(rows,100,-100);assert.equal(clamp[1].x,100);assert.equal(clamp[0].x,60);assert.equal(clamp[0].y,0);assert.equal(clamp[1].y,20);
const scale=g.scale(rows,1.5);assert.deepEqual(scale.map(l=>[l.x,l.y,l.width]),[[20,35,60],[80,65,15]]);assert.equal(scale[0].fontSize,120);assert.equal(scale[0].text,'صادق');assert.equal(scale[1].end,4);
assert.throws(()=>g.scale(rows,4));assert.throws(()=>g.move(rows,NaN,0));assert.equal(g.limits(rows).max,2.5);
"""
  subprocess.run(['node','-e',script],cwd=Path(__file__).parent,check=True)
