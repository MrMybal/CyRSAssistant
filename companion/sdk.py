"""CyMCPSDK worker adapter. Credentials travel only over the owned child's stdin."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from .localization import tr as _

PROVIDERS = ('codex', 'claude-code', 'openai-compatible', 'openai-compatible', 'opencode', 'antigravity', 'openai', 'anthropic', 'ollama', 'lmstudio')

def executable():
    explicit = os.environ.get('CYRS_SDK_EXE')
    root = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
    if not explicit and not (root / 'CyRSAssistantCLI.exe').is_file(): root = root / 'build/bin/Release'
    path = Path(explicit) if explicit else root / 'CyRSAssistantCLI.exe'
    if not path.is_file():
        raise RuntimeError('CyRSAssistantCLI.exe is missing. Reinstall the complete package or run tools/build.py.')
    return path

class SdkProvider:
    def __init__(self, config, client, runtime):
        self.model = config.get('model', '')
        self.config = dict(config)
        self.client, self.runtime = client, runtime
        state = client.state(runtime)
        self._pending, self._lock, self._write = {}, threading.Lock(), threading.Lock()
        self._counter, self._stream, self._sent = 0, None, False
        args = [str(executable()), '--pipe', client.pipe, '--runtime', str(runtime)]
        options = Path(state['base_path']) / 'CyRSAssistant/sdk-options.json'
        if options.is_file():
            args += ['--options', str(options)]
        args += ['worker']
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding='utf-8', bufsize=1, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        provider = PROVIDERS[config['provider']]
        try:
            self.request('connect', runtime=runtime, conversation_id=state.get('conversation_id',0), provider=provider, model=self.model, endpoint=config.get('endpoint',''), key=config.get('key','')).result(timeout=75)
            try:
                models = self.request('models').result(timeout=30)
                if isinstance(models, dict): models = models.get('data', models.get('models',[]))
                if isinstance(models,list): client.call('sdk_models',runtime=runtime,epoch=config['epoch'],models=models[:1000])
            except (RuntimeError, concurrent.futures.TimeoutError): pass
            transcript = self.request('history').result(timeout=10)
            restored = []
            for entry in transcript:
                role, content = entry.get('role'), entry.get('content','')
                if role not in ('user','assistant'): continue
                if isinstance(content,list): content = '\n'.join(b.get('text','') for b in content if b.get('type')=='text')
                if not isinstance(content,str) or not content: continue
                if role=='user':
                    try: content = json.loads(content).get('request',content)
                    except (ValueError,AttributeError): pass
                restored.append({'role':role,'content':content[:100000]})
            if restored:
                self._sent = True
                if not state.get('conversation'):
                    for offset in range(0,len(restored),4):
                        client.call('restore_chat_history',runtime=runtime,epoch=config['epoch'],messages=restored[offset:offset+4])
        except BaseException:
            self.close()
            raise

    def _read(self):
        try:
            for line in self.process.stdout:
                response = json.loads(line)
                if 'event' in response:
                    if response['event']=='ModelCatalogue':
                        try: self.client.call('sdk_models',runtime=self.runtime,epoch=self.config['epoch'],models=response['data'][:1000])
                        except (RuntimeError,OSError,ValueError): pass
                    callback = self._stream
                    if callback:
                        try: callback(response)
                        except (RuntimeError, OSError, ValueError): self.cancel()
                    continue
                with self._lock:
                    pending = self._pending.pop(response.get('id'), None)
                if pending:
                    if 'error' in response:
                        error = response['error']
                        pending.set_exception(RuntimeError(error.get('code','SDKError') + ': ' + error.get('message','SDK request failed')))
                    else: pending.set_result(response.get('result'))
        except (OSError, ValueError):
            pass
        finally:
            with self._lock:
                pending = list(self._pending.values()); self._pending.clear()
            for future in pending:
                if not future.done(): future.set_exception(RuntimeError('SDK worker disconnected; no action was retried.'))

    def request(self, command, **values):
        with self._lock:
            self._counter += 1; ident = self._counter
            future = concurrent.futures.Future(); self._pending[ident] = future
        try:
            with self._write:
                self.process.stdin.write(json.dumps({'id':ident, 'command':command, **values}, ensure_ascii=False, allow_nan=False)+'\n')
                self.process.stdin.flush()
        except (OSError, ValueError):
            with self._lock: self._pending.pop(ident,None)
            future.set_exception(RuntimeError('SDK worker unavailable.'))
        return future

    def cancel(self):
        if self.process.poll() is None:
            self.request('cancel')

    def close(self):
        if self.process.poll() is None:
            self.cancel()
            try: self.process.stdin.close()
            except OSError: pass
            try: self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill(); self.process.wait(timeout=5)

    def complete(self, system, content):
        # Legacy JSON planning commands retain their established non-chat contract.
        from .service import CliProvider
        from .provider import Provider
        provider = CliProvider(self.config) if self.config['provider'] in (0,1) else Provider(self.config)
        return provider.complete(system, content)

    def chat(self, client, runtime, state):
        text, last_sent = '', 0.0
        def stream(event):
            nonlocal text, last_sent
            if event['event'] == 'TextDelta':
                text += event.get('data',{}).get('text','')
                if time.monotonic()-last_sent >= .08:
                    client.call('assistant_delta', runtime=runtime, session=state['session'], prompt_id=state['prompt']['id'], text=text.encode('utf-8')[:500000].decode('utf-8',errors='ignore'))
                    last_sent = time.monotonic()
            elif event['event']=='ToolStarted':
                client.call('assistant_progress',runtime=runtime,session=state['session'],prompt_id=state['prompt']['id'],message=str(_('Calling an application tool...')))
        self._stream = stream
        context = {'request':state['prompt']['text'],'language':state.get('language','en'),
                   'runtime':runtime,'selected_shader':state['prompt'].get('shader_hash','')}
        if not self._sent:
            from .conversation import context_history
            history = context_history(state)
            context['previous_conversation'] = history
        future = self.request('send', text=json.dumps(context,ensure_ascii=False), state=state, attachment=state['prompt'].get('attachment',''))
        self._sent = True
        try:
            while True:
                try:
                    return future.result(timeout=.15)['text']
                except concurrent.futures.TimeoutError:
                    current = client.state(runtime)
                    if current['session']!=state['session'] or current['prompt']['id']!=state['prompt']['id'] or not current['prompt']['pending']:
                        self.cancel()
                        raise RuntimeError('Request cancelled. Previously applied changes remain active.')
        finally:
            self._stream = None


def connect(config, client, runtime):
    provider = SdkProvider(config, client, runtime)
    return provider, _('SDK provider connected. Model access is verified by the next message.')


def cli(arguments):
    return subprocess.call([str(executable()), *arguments])


class LocalMcpServer:
    """Owned local HTTP service; the native host supplies the selected access profile."""
    def __init__(self, client, runtime, epoch):
        self.epoch=epoch
        self.status={'phase':'starting','url':'','message':''}
        state=client.state(runtime)
        args=[str(executable()),'--pipe',client.pipe,'--runtime',str(runtime)]
        options=Path(state['base_path'])/'CyRSAssistant/sdk-options.json'
        if options.is_file():args+=['--options',str(options)]
        self.process=subprocess.Popen(args+['http'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            text=True,encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.reader=threading.Thread(target=self._read,daemon=True);self.reader.start()
    def _read(self):
        try:
            line=self.process.stdout.readline()
            value=json.loads(line)
            if value['epoch']!=self.epoch:raise ValueError('Local MCP epoch changed')
            self.status={'phase':'ready','url':value['url'],'message':''}
        except (OSError,ValueError,KeyError):
            self.status={'phase':'error','url':'','message':'Local MCP service could not start. Check the SDK settings and restart local MCP.'}
    def poll(self):
        if self.process.poll() is not None:
            return {'phase':'error','url':'','message':'Local MCP service stopped. Disable and re-enable local MCP to restart it.'}
        return self.status
    def close(self):
        if self.process.poll() is None:
            try:self.process.stdin.close();self.process.wait(timeout=5)
            except (OSError,subprocess.TimeoutExpired):self.process.kill();self.process.wait(timeout=5)
        self.reader.join(timeout=1)
        self.process.stdout.close()
