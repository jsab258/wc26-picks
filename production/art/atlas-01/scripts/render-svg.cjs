// Optional PNG preview renderer. npm install sharp in your normal tools environment.
// CODEX_NODE_MODULES can point at an existing dependency bundle; no installation performed here.
const path=require('path'),fs=require('fs');
const sharp=require(process.env.CODEX_NODE_MODULES?path.join(process.env.CODEX_NODE_MODULES,'sharp'):'sharp');
const root=path.resolve(__dirname,'../previews');
(async()=>{for(const f of fs.readdirSync(root).filter(f=>f.endsWith('.svg'))){await sharp(path.join(root,f),{density:110}).png().toFile(path.join(root,f.replace('.svg','.png')));console.log(f);}})().catch(e=>{console.error(e);process.exit(1)});
