"""One operation catalogue for the native SDK registry and every frontend."""
from pathlib import Path
import json, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from companion.mcp import tools, VERSION

def schema(properties, required=None):
    return {'type':'object','properties':properties,'required':list(properties) if required is None else required,'additionalProperties':False}

def catalogue():
    entries=tools(True)
    runtime={'runtime':VERSION['runtime']}
    paging={'offset':{'type':'integer','minimum':0},'limit':{'type':'integer','minimum':1,'maximum':100},'query':{'type':'string','maxLength':200},'effect':{'type':'string','maxLength':260}}
    for name,description,properties,required in [
        ('refresh','Refresh live metadata and explicitly invalidate configured remote discovery/read caches.',runtime,None),
        ('catalog_read','Read the reusable disk catalogue and descriptions; run catalog_scan to refresh.',runtime,None),
        ('catalog_scan','Scan configured shader roots into the existing portable catalogue. Writes only catalogue metadata.',VERSION,None),
        ('catalog_export','Return portable catalogue/description JSON without choosing an output path.',runtime,None),
        ('catalog_import','Import validated description metadata into this game catalogue; no arbitrary filesystem paths.',{**VERSION,'data':{'type':'object'}},None),
        ('store_effect_description','Store an AI-generated description for an exact current fingerprint. Never claim visual verification.',{**VERSION,'fingerprint':{'type':'string','minLength':64,'maxLength':64},'text':{'type':'string','minLength':1,'maxLength':20000},'model':{'type':'string','maxLength':160}},[*VERSION,'fingerprint','text']),
        ('get_effects','Find installed FX filenames and their techniques; page through the full inventory.',{**runtime,**paging},['runtime']),
        ('get_parameters','Read named parameters, current values, limits and readonly flags; filter by exact effect and page.',{**runtime,**paging},['runtime']),
        ('read_effect_source','Read one exact FX/FXH filename under configured shader roots. Requires source approval in Ask mode. Follow next_offset.',{**runtime,'file':{'type':'string','maxLength':260},'offset':{'type':'integer','minimum':0}},['runtime','file']),
        ('scan_effects','Rescan effects and invalidate old identifiers and undo. Read fresh state afterwards.',VERSION,None),
        ('get_help_state','Read the current documentation topic and any help error.',runtime,None),
        ('result_read','Read a retained large result resource by its opaque URI; never replay the original operation.',{'uri':{'type':'string','maxLength':2048}},None),
        ('resource_grep','Search registered text snapshots without filesystem traversal.',{'text':{'type':'string','minLength':1,'maxLength':200},'cursor':{'type':'string'}},['text'])
    ]:
        entries.append({'name':'cyrs_'+name,'description':description,'inputSchema':schema(properties,required),'annotations':{'readOnlyHint':name not in ('scan_effects','catalog_scan','catalog_import','store_effect_description')}})
    def clean(value):
        if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k!='pattern'}
        if isinstance(value,list):return [clean(x) for x in value]
        return value
    def obj(properties, required=()):
        return {'type':'object','properties':properties,'required':list(required)}
    integer={'type':'integer','minimum':0}
    array={'type':'array'}
    resource=obj({'uri':{'type':'string'},'bytes':integer,'chunked':{'type':'boolean'},'expiresInMs':integer},['uri','bytes'])
    state=obj({'session':{'type':'string'},'runtime':integer,'generation':integer,'revision':integer,'parameters':array,'techniques':array},['session','runtime','generation','revision'])
    outputs={
      'get_state':obj({'ok':{'const':True},'state':state},['ok','state']),
      'get_effects':obj({'items':array,'total':integer,'next_offset':{'type':['integer','null']}},['items','total','next_offset']),
      'get_parameters':obj({'items':array,'total':integer,'next_offset':{'type':['integer','null']}},['items','total','next_offset']),
      'read_effect_source':obj({'file':{'type':'string'},'source':{'type':'string'},'sha256':{'type':'string'},'offset':integer,'bytes':integer,'next_offset':{'type':['integer','null']}},['file','source','sha256','offset','next_offset']),
      'catalog_read':obj({'effects':array},['effects']),
      'catalog_scan':obj({'schema_version':{'const':1},'effects':array,'errors':array,'complete':{'type':'boolean'}},['schema_version','effects','complete']),
      'catalog_export':obj({'schema_version':{'const':1},'catalog':{'type':'object'},'descriptions':array},['schema_version','catalog','descriptions']),
      'catalog_import':obj({'imported':integer},['imported']),
      'store_effect_description':obj({'fingerprint':{'type':'string'},'text':{'type':'string'},'model':{'type':'string'},'validation':{'type':'string'}},['fingerprint','text','validation']),
      'capture_frame':obj({'capture':obj({'mimeType':{'const':'image/png'},'data':{'type':'string'},'width':integer,'height':integer},['mimeType','width','height'])},['capture']),
      'resource_grep':obj({'matches':array,'complete':{'type':'boolean'}},['matches','complete']),
      'result_read':obj({'contents':array},['contents']),
      'refresh':obj({'refreshed':{'const':True},'revision':integer},['refreshed','revision'])}
    for entry in entries:
        name=entry['name'].removeprefix('cyrs_')
        ordinary=outputs.get(name,obj({'ok':{'const':True},'state':state,'inventory':{'type':'object'},'shader':{'type':'object'},'generated':{'type':'object'},'runtimes':array},['ok']))
        entry['outputSchema']={'type':'object','anyOf':[ordinary,obj({'resource':resource,'instructions':{'type':'string'},'version':{'type':'object'}},['resource'])]}
    return clean(entries)
if __name__=='__main__':
    output=Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(catalogue(),ensure_ascii=True,separators=(',',':'))
    lock=json.loads((Path(__file__).resolve().parents[1]/'tools/cymcpsdk.lock.json').read_text(encoding='utf-8'))
    literals='\n'.join('R"CYRS('+data[i:i+8000]+')CYRS"' for i in range(0,len(data),8000))
    output.write_text('#pragma once\ninline constexpr const char *sdk_revision = '+json.dumps(lock['commit'])+';\ninline constexpr const char *sdk_catalogue =\n'+literals+';\n',encoding='utf-8')
