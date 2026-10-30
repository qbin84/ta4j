// usage: node render_svg.mjs GRAPHVIZ_PKG_DIR IN.dot OUT.svg
// GRAPHVIZ_PKG_DIR: directory containing node_modules/@hpcc-js/wasm-graphviz (Graphviz compiled to WASM),
// used when the native `dot` binary is not installed.
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [pkgDir, input, output] = process.argv.slice(2);
const { Graphviz } = await import(pathToFileURL(join(pkgDir, "node_modules/@hpcc-js/wasm-graphviz/dist/index.js")));
const graphviz = await Graphviz.load();
writeFileSync(output, graphviz.dot(readFileSync(input, "utf8")));
console.log(`graphviz ${graphviz.version()} -> ${output}`);
