// Same-origin API client with structured errors and incremental NDJSON solver events.
/** Send a JSON request and turn API validation responses into readable messages. */
export async function api(path, body, signal) {
  const response = await fetch(`/api/${path}`, {method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail||'Request failed'));
  return data;
}
/** Stream actual solver events without waiting for the whole search to finish. */
export async function streamSolve(body,onEvent,onResult,signal) {
  const response = await fetch('/api/solve/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});
  if (!response.ok) throw new Error((await response.text()) || 'Solver unavailable');
  const reader=response.body.getReader(),decoder=new TextDecoder();
  let buffer='';
  while (true) {
    const {done,value}=await reader.read();
    buffer+=decoder.decode(value||new Uint8Array(),{stream:!done});
    const lines=buffer.split('\n'); buffer=lines.pop();
    for (const line of lines) if (line.trim()) {
      const item=JSON.parse(line);
      if (item.kind==='event') onEvent(item.event);
      else if (item.kind==='result') onResult(item.result);
      else if (item.kind==='error') throw new Error(item.message);
    }
    if(done) break;
  }
}
