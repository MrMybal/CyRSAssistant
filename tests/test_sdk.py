"""Native SDK frontends and opt-in integration with an actual ReShade runtime."""
import base64
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import queue
import tempfile
from pathlib import Path
import subprocess
import threading
import time
import unittest
import urllib.request
import urllib.error
from companion.transport import Client, version

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'build/bin/Release/CyRSAssistantCLI.exe'

class Mcp:
    def __init__(self, *args):
        self.process = subprocess.Popen([str(CLI), *args, 'mcp'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
        self.ident = 0
        self.messages=queue.Queue()
        self.notifications=[]
        self.reader=threading.Thread(target=lambda:[self.messages.put(json.loads(line)) for line in self.process.stdout],daemon=True);self.reader.start()
        self.call('initialize', {'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'integration','version':'1'}})
    def call(self, method, params=None):
        self.ident += 1
        self.process.stdin.write(json.dumps({'jsonrpc':'2.0','id':self.ident,'method':method,'params':params or {}})+'\n');self.process.stdin.flush()
        while True:
            result=self.messages.get(timeout=20)
            if result.get('id')==self.ident: return result
            self.notifications.append(result)
    def close(self):
        self.process.stdin.close(); self.process.wait(timeout=10)
        self.reader.join(timeout=2)
        self.process.stdout.close(); self.process.stderr.close()

class SDKTests(unittest.TestCase):
    @unittest.skipUnless(CLI.is_file(),'Build the native SDK frontend first')
    def test_discovery_schema_and_write_denial_without_game(self):
        p=subprocess.run([str(CLI),'tools'],capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
        rows=json.loads(p.stdout)
        self.assertGreaterEqual(len(rows),21)
        op=json.loads(subprocess.check_output([str(CLI),'describe','cyrs_apply_patch'],text=True))
        self.assertIn('generation',op['inputSchema']['required'])
        refused=subprocess.run([str(CLI),'call','cyrs_apply_patch','{}'],capture_output=True,text=True,timeout=10)
        self.assertEqual(refused.returncode,3)
        self.assertIn('AccessDenied',refused.stderr)
        self.assertEqual(refused.stdout,'')

@unittest.skipUnless(os.environ.get('CYRS_LIVE_PIPE'),'Opt in with CYRS_LIVE_PIPE for the owned ReShade test host')
class RealReShadeTests(unittest.TestCase):
    def setUp(self):
        self.pipe=os.environ['CYRS_LIVE_PIPE']; self.client=Client(self.pipe)
        self.runtime=self.client.call('list_sessions')['runtimes'][0]['runtime']
        state=self.client.state(self.runtime)
        self.assertEqual(Path(state['base_path']).resolve(),(ROOT/'build/live-sdk').resolve(),'Use only the owned integration host')
        deadline=time.monotonic()+20
        while not state['parameters'] and time.monotonic()<deadline:
            time.sleep(.1);state=self.client.state(self.runtime)
        self.assertTrue(any(p['effect']=='SDKFixture.fx' for p in state['parameters']), 'This test only modifies its own FX fixture')
        self.client.call('set_permission_mode',runtime=self.runtime,session=state['session'],mode=0)
    def cli(self, name, args, write=False, options=None):
        command=[str(CLI),'--pipe',self.pipe,'--runtime',str(self.runtime)]
        if write:command+=['--allow-write']
        if options:command+=['--options',str(options)]
        return subprocess.run(command+['call',name,json.dumps(args)],capture_output=True,text=True,encoding='utf-8',timeout=15)
    def parameter_id(self):
        return next(p['id'] for p in self.client.state(self.runtime)['parameters'] if p['effect']=='SDKFixture.fx' and p['name']=='Exposure')
    def value(self):
        return next(p for p in self.client.state(self.runtime)['parameters'] if p['effect']=='SDKFixture.fx')['value'][0]
    def test_cli_and_mcp_operate_on_real_uniform_and_enforce_permissions(self):
        original=self.value();state=self.client.state(self.runtime)
        args={**version(state),'changes':[{'kind':'parameter','id':self.parameter_id(),'value':[1.25]}]}
        self.assertEqual(self.cli('cyrs_apply_patch',args).returncode,3)
        self.assertEqual(self.value(),original)
        applied=self.cli('cyrs_apply_patch',args,True)
        self.assertEqual(applied.returncode,0,applied.stderr);self.assertAlmostEqual(self.value(),1.25)
        state=self.client.state(self.runtime)
        self.assertEqual(self.cli('cyrs_undo',version(state),True).returncode,0)
        self.assertAlmostEqual(self.value(),original)
        mcp=Mcp('--pipe',self.pipe,'--allow-write')
        try:
            self.assertTrue(mcp.call('tools/list')['result']['tools'])
            read=mcp.call('tools/call',{'name':'cyrs_get_parameters','arguments':{'runtime':self.runtime}})
            self.assertFalse(read['result']['isError'])
            self.assertTrue(any(p['name']=='Exposure' for p in read['result']['structuredContent']['items']))
            state=self.client.state(self.runtime)
            args={**version(state),'changes':[{'kind':'parameter','id':self.parameter_id(),'value':[.75]}]}
            changed=mcp.call('tools/call',{'name':'cyrs_apply_patch','arguments':args})
            self.assertFalse(changed['result']['isError']);self.assertAlmostEqual(self.value(),.75)
            self.cli('cyrs_undo',version(self.client.state(self.runtime)),True)
            frame=mcp.call('tools/call',{'name':'cyrs_capture_frame','arguments':{'runtime':self.runtime}})
            image=frame['result']['content'][0]
            self.assertEqual(image['type'],'image');self.assertEqual(image['mimeType'],'image/png')
            self.assertTrue(base64.b64decode(image['data']).startswith(b'\x89PNG'))
        finally:mcp.close()
        state=self.client.state(self.runtime)
        self.client.call('set_permission_mode',runtime=self.runtime,session=state['session'],mode=1)
        try:
            denied=self.cli('cyrs_apply_patch',{**version(state),'changes':[{'kind':'parameter','id':self.parameter_id(),'value':[1.8]}]},True)
            self.assertEqual(denied.returncode,3,denied.stderr)
            self.assertIn('ApprovalRequired',denied.stderr);self.assertAlmostEqual(self.value(),original)
        finally:self.client.call('set_permission_mode',runtime=self.runtime,session=state['session'],mode=0)

    def test_generated_fx_source_catalogue_and_restore_use_real_handlers(self):
        original=self.client.state(self.runtime)
        (ROOT/'build/live-sdk/textures').mkdir(exist_ok=True)
        source=self.cli('cyrs_read_effect_source',{'runtime':self.runtime,'file':'SDKFixture.fx'})
        self.assertEqual(source.returncode,0,source.stderr)
        self.assertIn('Exposure',json.loads(source.stdout)['source'])
        scan=self.cli('cyrs_catalog_scan',version(self.client.state(self.runtime)),True)
        self.assertEqual(scan.returncode,0,scan.stderr)
        self.assertTrue(json.loads(scan.stdout)['complete'])
        exported=self.cli('cyrs_catalog_export',{'runtime':self.runtime})
        self.assertEqual(exported.returncode,0,exported.stderr)
        self.assertEqual(json.loads(exported.stdout)['schema_version'],1)
        spec={**version(self.client.state(self.runtime)),'name':'SDKValidation','title':'SDK validation',
              'body':'return color * CyRSP_Gain;', 'replace_effect':'SDKFixture.fx',
              'parameters':[{'name':'Gain','label':'Gain','min':0.0,'max':2.0,'default':1.0,'step':0.01}]}
        generated=self.cli('cyrs_generate_effect',spec,True)
        self.assertEqual(generated.returncode,0,generated.stderr)
        self.assertEqual(json.loads(generated.stdout)['generated']['phase'],'ready')
        current=self.client.state(self.runtime)
        self.assertTrue(any(p['name']=='CyRSP_Gain' for p in current['parameters']))
        restored=self.cli('cyrs_restore_generated_effect',version(current),True)
        self.assertEqual(restored.returncode,0,restored.stderr)
        current=self.client.state(self.runtime)
        self.assertTrue(next(t for t in current['techniques'] if t['effect']=='SDKFixture.fx')['value'])

    def test_retained_chunks_expiry_spooling_notifications_and_private_metrics(self):
        fixture=ROOT/'build/live-sdk/shaders'
        files=[fixture/('SDKBulk_'+str(i)+'_'+'x'*120+'.fxh') for i in range(190)]
        try:
            for path in files:path.write_text('// catalogue retention fixture',encoding='utf-8')
            self.assertEqual(self.cli('cyrs_catalog_scan',version(self.client.state(self.runtime)),True).returncode,0)
            with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='sdk-options-') as directory:
                root=Path(directory);options=root/'options.json';metrics=root/'metrics.jsonl'
                options.write_text(json.dumps({'large_results':True,'inline_bytes':100,'result_ttl_ms':2000,
                    'memory_quota_bytes':1024,'disk_spooling':True,'disk_quota_bytes':1048576,'spool_directory':'spool',
                    'notifications':True,'metrics':True,'metrics_file':'metrics.jsonl'}),encoding='utf-8')
                mcp=Mcp('--pipe',self.pipe,'--runtime',str(self.runtime),'--options',str(options))
                def tool(name,args):
                    r=mcp.call('tools/call',{'name':name,'arguments':args})['result']
                    self.assertFalse(r['isError'],r);return r['structuredContent']
                try:
                    tool('cyrs_get_parameters',{'runtime':self.runtime,'query':'SDK_PRIVATE_CANARY'})
                    value=tool('cyrs_catalog_export',{'runtime':self.runtime})
                    uri=value['resource']['uri'];self.assertTrue(value['resource']['chunked'])
                    manifest=json.loads(mcp.call('resources/read',{'uri':uri})['result']['contents'][0]['text'])
                    uri_next=manifest['firstUri'];chunks=[]
                    while uri_next:
                        result=mcp.call('resources/read',{'uri':uri_next})['result'];chunks.append(result['contents'][0]['text'])
                        uri_next=result['_meta']['com.cymcp/chunk'].get('nextUri')
                    complete=json.loads(''.join(chunks));self.assertEqual(len(complete['catalog']['files']),193+len([p for p in fixture.glob('CyRS*.fx')]))
                    self.assertGreater(len(list((root/'spool').rglob('*'))),0)
                    # Modern stdio subscriptions notify before the 30-second discovery TTL.
                    mcp.call('tools/call',{'name':'cyrs_refresh','arguments':{'runtime':self.runtime}})
                    mcp.ident+=1;subscription=mcp.ident
                    mcp.process.stdin.write(json.dumps({'jsonrpc':'2.0','id':subscription,'method':'subscriptions/listen','params':{
                        '_meta':{'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{}},
                        'notifications':{'resourcesListChanged':True,'resourceSubscriptions':['cyrs://runtime/state']}}})+'\n');mcp.process.stdin.flush()
                    ack=mcp.messages.get(timeout=5);self.assertEqual(ack.get('method'),'notifications/subscriptions/acknowledged',ack)
                    state=self.client.state(self.runtime);original=self.value()
                    self.assertEqual(self.cli('cyrs_apply_patch',{**version(state),'changes':[{'kind':'parameter','id':self.parameter_id(),'value':[1.1]}]},True).returncode,0)
                    until=time.monotonic()+5;changed=False
                    while time.monotonic()<until:
                        message=mcp.messages.get(timeout=5)
                        if message.get('method')=='notifications/resources/updated':changed=True;break
                    self.assertTrue(changed)
                    snapshot=mcp.call('resources/read',{'uri':'cyrs://runtime/state'})['result']
                    self.assertIn('1.100000',snapshot['contents'][0]['text'])
                    mcp.process.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/cancelled','params':{'requestId':subscription}})+'\n');mcp.process.stdin.flush()
                    self.cli('cyrs_undo',version(self.client.state(self.runtime)),True)
                    time.sleep(2.1)
                    expired=mcp.call('resources/read',{'uri':uri});self.assertIn('error',expired)
                    self.assertAlmostEqual(self.value(),original)
                finally:mcp.close()
                raw=metrics.read_text(encoding='utf-8');self.assertNotIn('SDK_PRIVATE_CANARY',raw)
                self.assertNotIn(self.pipe,raw);self.assertNotIn(self.client.state(self.runtime)['session'],raw)
                allowed={'stage','name','status','elapsed_ms','input_bytes','output_bytes','cache_hit','timestamp_ms'}
                self.assertTrue(raw.strip());self.assertTrue(all(set(json.loads(line))<=allowed for line in raw.splitlines()))
        finally:
            for path in files:path.unlink(missing_ok=True)

    def test_remote_resources_and_remote_mutation_refusal(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='sdk-remote-') as directory:
            options=Path(directory)/'options.json'
            options.write_text(json.dumps({'remote_tools':[{'id':'peer','executable':str(CLI),
                'arguments':['--pipe',self.pipe,'mcp'],'tools':['cyrs_get_state','cyrs_apply_patch'],'allow_resources':True}]}),encoding='utf-8')
            m=Mcp('--pipe',self.pipe,'--options',str(options),'--allow-write')
            def call(name,args):return m.call('tools/call',{'name':name,'arguments':args})['result']
            try:
                self.assertFalse(call('remote_peer_cyrs_get_state',{'runtime':self.runtime})['isError'])
                listed=call('remote_peer_resources',{});self.assertFalse(listed['isError'])
                self.assertTrue(listed['structuredContent']['resources'])
                resource=call('remote_peer_resource_read',{'uri':'cyrs://runtime/state'})
                self.assertFalse(resource['isError']);self.assertIn('SDKFixture.fx',resource['structuredContent']['contents'][0]['text'])
                original=self.value();state=self.client.state(self.runtime)
                denied=call('remote_peer_cyrs_apply_patch',{**version(state),'changes':[{'kind':'parameter','id':self.parameter_id(),'value':[1.9]}]})
                self.assertTrue(denied['isError']);self.assertAlmostEqual(self.value(),original)
            finally:m.close()

    def test_local_http_profiles_free_validation_and_protected_authentication(self):
        state=self.client.state(self.runtime);base=Path(state['base_path']);options=base/'CyRSAssistant/sdk-options.json'
        options.parent.mkdir(exist_ok=True);saved=options.read_bytes() if options.exists() else None
        options.write_text(json.dumps({'wait_for_approval':False}),encoding='utf-8')
        original=self.value();old_mode=state['permissions']['mode']
        self.client.call('set_permission_mode',runtime=self.runtime,session=state['session'],mode=1)
        def configure(profile=None,enabled=True):
            args={'runtime':self.runtime,'session':state['session'],'enabled':enabled}
            if profile is not None:args['profile']=profile
            self.client.call('configure_mcp_local',**args)
            until=time.monotonic()+25
            while enabled and time.monotonic()<until:
                value=self.client.state(self.runtime)['local_mcp']
                if value['phase']=='ready':return value
                if value['phase']=='error':self.fail(value['message'])
                time.sleep(.1)
            if enabled:self.fail('Local HTTP MCP startup timed out')
        counter=0
        sessions={}
        def rpc(url,method,params=None,token=None):
            nonlocal counter
            counter+=1;headers={'Content-Type':'application/json','MCP-Protocol-Version':'2025-06-18'}
            if method!='initialize' and url in sessions:headers['Mcp-Session-Id']=sessions[url]
            if token:headers['Authorization']='Bearer '+token
            data=json.dumps({'jsonrpc':'2.0','id':counter,'method':method,'params':params or {}}).encode()
            with urllib.request.urlopen(urllib.request.Request(url,data,headers),timeout=10) as response:
                if method=='initialize':sessions[url]=response.headers['Mcp-Session-Id']
                return json.load(response)
        def initialize(url,token=None):
            return rpc(url,'initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'http-integration','version':'1'}},token)
        def read(url,token=None):return rpc(url,'tools/call',{'name':'cyrs_get_parameters','arguments':{'runtime':self.runtime}},token)['result']
        def write(url,value,token=None):
            current=self.client.state(self.runtime)
            return rpc(url,'tools/call',{'name':'cyrs_apply_patch','arguments':{**version(current),'changes':[{'kind':'parameter','id':self.parameter_id(),'value':[value]}]}},token)['result']
        try:
            # No profile argument: use the migrated/default choice. A fresh host defaults to Free.
            info=configure(0);self.assertEqual(info['profile'],0);self.assertFalse(info['requires_token'])
            url=info['url'];initialize(url)
            self.assertEqual(len(rpc(url,'tools/list')['result']['tools']),27)
            self.assertFalse(read(url)['isError'])
            for value in [1.2,1.3,1.4]:
                self.assertFalse(write(url,value)['isError']);self.assertAlmostEqual(self.value(),value,places=5)
            source=rpc(url,'tools/call',{'name':'cyrs_read_effect_source','arguments':{'runtime':self.runtime,'file':'SDKFixture.fx'}})['result']
            self.assertFalse(source['isError']);self.assertIn('Exposure',source['structuredContent']['source'])
            scan=rpc(url,'tools/call',{'name':'cyrs_catalog_scan','arguments':version(self.client.state(self.runtime))})['result']
            self.assertFalse(scan['isError'],scan)
            invalid=write(url,9);self.assertTrue(invalid['isError']);self.assertAlmostEqual(self.value(),1.4,places=5)
            bad=rpc(url,'tools/call',{'name':'cyrs_get_parameters','arguments':{'runtime':'invalid'}})['result'];self.assertTrue(bad['isError'])
            snapshot=self.client.state(self.runtime)
            self.assertEqual(snapshot['permissions']['mode'],1);self.assertIsNone(snapshot['permissions']['request'])
            private=self.client.call('get_mcp_connection',runtime=self.runtime)['connection']
            self.assertNotIn(private['capability'],json.dumps(snapshot))
            # Controlled without token retains application approval; it must not silently become Free.
            info=configure(1);initialize(info['url']);self.assertFalse(read(info['url'])['isError'])
            self.assertTrue(write(info['url'],1.8)['isError']);self.assertAlmostEqual(self.value(),1.4,places=5)
            # Token only has free business access, with transport authentication.
            info=configure(2)
            with self.assertRaises(urllib.error.HTTPError) as refused:initialize(info['url'])
            self.assertEqual(refused.exception.code,401)
            token=self.client.call('get_mcp_connection',runtime=self.runtime)['connection']['token']
            initialize(info['url'],token);self.assertFalse(write(info['url'],1.5,token)['isError'])
            # Protected combines transport authentication with the existing controlled business policy.
            info=configure(3)
            for token in [None,'invalid-token']:
                with self.assertRaises(urllib.error.HTTPError) as refused:initialize(info['url'],token)
                self.assertEqual(refused.exception.code,401)
            token=self.client.call('get_mcp_connection',runtime=self.runtime)['connection']['token']
            initialize(info['url'],token);self.assertFalse(read(info['url'],token)['isError'])
            self.assertTrue(write(info['url'],1.8,token)['isError']);self.assertAlmostEqual(self.value(),1.5)
            self.assertNotIn(token,json.dumps(self.client.state(self.runtime)))
            configure(enabled=False)
            until=time.monotonic()+5
            while time.monotonic()<until:
                try:read(info['url'],token)
                except (OSError,urllib.error.HTTPError):break
                time.sleep(.1)
            else:self.fail('Disabled MCP listener stayed reachable')
        finally:
            self.client.call('configure_mcp_local',runtime=self.runtime,session=state['session'],enabled=False,profile=0)
            self.client.call('set_permission_mode',runtime=self.runtime,session=state['session'],mode=old_mode)
            self.cli('cyrs_apply_patch',{**version(self.client.state(self.runtime)),'changes':[{'kind':'parameter','id':self.parameter_id(),'value':[original]}]},True)
            if saved is None:options.unlink(missing_ok=True)
            else:options.write_bytes(saved)

    def test_context_projection_preserves_checkpoint_and_restores_without_resend(self):
        requests=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                data=json.dumps({'data':[{'id':'fixture'}]}).encode();self.send_response(200);self.end_headers();self.wfile.write(data)
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));requests.append(body)
                self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
                value={'choices':[{'index':0,'delta':{'content':'Saved reply '+('r'*1200)},'finish_reason':'stop'}]}
                self.wfile.write(('data: '+json.dumps(value)+'\n\ndata: [DONE]\n\n').encode())
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='sdk-history-') as directory:
                root=Path(directory);options=root/'options.json'
                config={'persist_history':True,'history_directory':'history','context_bytes':7000,'context_recent_turns':2}
                options.write_text(json.dumps(config),encoding='utf-8')
                def start():
                    proc=subprocess.Popen([str(CLI),'--pipe',self.pipe,'--options',str(options),'worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
                    return proc
                ident=0
                def command(proc,name,**args):
                    nonlocal ident
                    ident+=1;proc.stdin.write(json.dumps({'id':ident,'command':name,**args})+'\n');proc.stdin.flush()
                    while True:
                        response=json.loads(proc.stdout.readline())
                        if response.get('id')==ident and 'event' not in response:
                            self.assertNotIn('error',response,response);return response['result']
                def close(proc):
                    proc.stdin.close();proc.wait(timeout=10);proc.stdout.close();proc.stderr.close()
                connect={'provider':'openai-compatible','model':'fixture','key':'SDK_SECRET_KEY_CANARY','runtime':self.runtime,'endpoint':f'http://127.0.0.1:{server.server_port}/v1'}
                proc=start()
                try:
                    command(proc,'connect',**connect)
                    for i in range(6):command(proc,'send',state=self.client.state(self.runtime),text=f'private turn {i} '+('q'*1200))
                    history=command(proc,'history');self.assertEqual(sum(m['role']=='user' for m in history),6)
                    self.assertLess(sum(m['role']=='user' for m in requests[-1]['messages']),6)
                    self.assertTrue(any(m['role']=='system' for m in requests[-1]['messages']))
                finally:close(proc)
                checkpoints=list((root/'history').glob('*.json'));self.assertEqual(len(checkpoints),1)
                checkpoint=checkpoints[0].read_text(encoding='utf-8');self.assertNotIn('SDK_SECRET_KEY_CANARY',checkpoint)
                self.assertEqual(sum(m['role']=='user' for m in json.loads(checkpoint)['messages']),6)
                config['restore_history']=True;options.write_text(json.dumps(config),encoding='utf-8');before=len(requests)
                proc=start()
                try:
                    command(proc,'connect',**connect);restored=command(proc,'history')
                    self.assertEqual(history,restored);self.assertEqual(len(requests),before)
                finally:close(proc)
        finally:server.shutdown();server.server_close()

    def test_integrated_stream_tool_mutation_and_cancellation(self):
        owner=self
        requests=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                data=json.dumps({'data':[{'id':'fixture','object':'model'}]}).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append(body)
                self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
                def event(delta,finish=None):
                    data={'choices':[{'index':0,'delta':delta,'finish_reason':finish}]}
                    self.wfile.write(('data: '+json.dumps(data)+'\n\n').encode());self.wfile.flush()
                try:
                    last_user=max(i for i,m in enumerate(body['messages']) if m.get('role')=='user')
                    content=body['messages'][last_user]['content']
                    if isinstance(content,list):content=''.join(b.get('text','') for b in content)
                    current_request=json.loads(content).get('request',content)
                    cancel=current_request=='SDK_CANCEL_TEST'
                    count=sum(m.get('role')=='tool' for m in body['messages'][last_user+1:])
                    if cancel:
                        for i in range(100):event({'content':'streaming '});time.sleep(.1)
                    elif count<2:
                        args={'runtime':owner.runtime if count==0 else 999999}
                        event({'tool_calls':[{'index':0,'id':'remote'+str(count),'type':'function','function':{'name':'remote_peer_cyrs_get_parameters','arguments':json.dumps(args)}}]},'tool_calls')
                    elif count==2:
                        event({'tool_calls':[{'index':0,'id':'parameters','type':'function','function':{'name':'cyrs_get_parameters','arguments':json.dumps({'runtime':owner.runtime})}}]},'tool_calls')
                    elif count==3:
                        state=owner.client.state(owner.runtime)
                        args={**version(state),'changes':[{'kind':'parameter','id':owner.parameter_id(),'value':[1.25]}]}
                        event({'tool_calls':[{'index':0,'id':'apply','type':'function','function':{'name':'cyrs_apply_patch','arguments':json.dumps(args)}}]},'tool_calls')
                    else:
                        for text in ['SDK streamed ', 'the reply. ', 'Exposure is 1.25.']:event({'content':text});time.sleep(.2)
                        event({},'stop')
                    self.wfile.write(b'data: [DONE]\n\n');self.wfile.flush()
                except (BrokenPipeError,ConnectionResetError):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        state=self.client.state(self.runtime)
        options=Path(state['base_path'])/'CyRSAssistant/sdk-options.json'
        saved_options=options.read_bytes() if options.exists() else None
        options.parent.mkdir(exist_ok=True)
        options.write_text(json.dumps({'remote_tools':[{'id':'peer','executable':str(CLI),'arguments':['--pipe',self.pipe,'mcp'],'tools':['cyrs_get_parameters'],'allow_resources':True}]}),encoding='utf-8')
        try:
            self.client.call('connect_provider',runtime=self.runtime,provider=2,endpoint=f'http://127.0.0.1:{server.server_port}/v1/chat/completions',model='fixture')
            until=time.monotonic()+90
            while time.monotonic()<until:
                current=self.client.state(self.runtime)
                if current['connection']['ready']:break
                if current['connection']['phase']=='error':self.fail(current['connection']['message'])
                time.sleep(.1)
            else:self.fail('SDK provider did not become ready')
            self.client.call('send_chat',runtime=self.runtime,session=state['session'],text='Use the application tool to set the fixture Exposure to 1.25, then confirm the readback.')
            partial=False;until=time.monotonic()+30
            while time.monotonic()<until:
                current=self.client.state(self.runtime)
                partial|=current['prompt']['pending'] and bool(current['prompt'].get('partial'))
                if not current['prompt']['pending']:break
                time.sleep(.05)
            self.assertFalse(current['prompt']['pending']);self.assertTrue(partial,'No streamed UI state observed')
            self.assertAlmostEqual(self.value(),1.25,msg=str([m for m in requests[-1]['messages'] if m['role']=='tool'])[-2000:])
            self.assertIn('SDK streamed',current['conversation'][-1]['content'])
            self.assertIn('RemoteToolError',json.dumps(requests))
            self.assertTrue(any('remote_peer_cyrs_get_parameters' in json.dumps(r) for r in requests))
            self.client.call('send_chat',runtime=self.runtime,session=state['session'],text='SDK_CANCEL_TEST')
            until=time.monotonic()+10
            while time.monotonic()<until:
                if self.client.state(self.runtime)['prompt'].get('partial'):break
                time.sleep(.05)
            self.client.call('cancel_chat',runtime=self.runtime,session=state['session'])
            time.sleep(.5)
            self.assertFalse(self.client.state(self.runtime)['prompt']['pending'])
            self.assertAlmostEqual(self.value(),1.25)
        finally:
            self.client.call('disconnect_provider',runtime=self.runtime)
            server.shutdown();server.server_close()
            if saved_options is None:options.unlink(missing_ok=True)
            else:options.write_bytes(saved_options)
            current=self.client.state(self.runtime)
            self.cli('cyrs_apply_patch',{**version(current),'changes':[{'kind':'parameter','id':self.parameter_id(),'value':[1.0]}]},True)

if __name__=='__main__':unittest.main()
