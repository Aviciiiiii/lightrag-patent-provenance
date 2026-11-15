"""Selectively execute unchanged official parser AST nodes, avoiding unrelated imports.

This is an execution harness, not a replacement parser. Every parsing, cleaning,
normalizing and repairing function is compiled unchanged from the pinned official
source. The loader records exact source spans/hashes and rejects unresolved globals.
"""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import __future__
import ast
import asyncio
import builtins
from collections import defaultdict
import dis
import hashlib
import html
import logging
from pathlib import Path
import re
import types

ROOT=legacy_root('round3')
from parser_source import SOURCE, EXPECTED_COMMIT, verify_source
SELECTION=[
 ('lightrag/_version.py',['__version__']),
 ('lightrag/constants.py',['DEFAULT_ENTITY_NAME_MAX_LENGTH','DEFAULT_ENTITY_NAME_MAX_BYTES']),
 ('lightrag/utils.py',['_SURROGATE_PATTERN','_CONTROL_CHAR_PATTERN_ALL','TruncatedResponse','is_truncated_response','split_string_by_multi_markers','_cooperative_yield','normalize_extracted_info','sanitize_text_for_encoding','sanitize_and_normalize_extracted_text','normalize_entity_name','fix_tuple_delimiter_corruption']),
 ('lightrag/operate.py',['_RESERVED_ENTITY_TYPES','_truncate_entity_identifier','_normalize_and_validate_entity_type','_handle_single_entity_extraction','_handle_single_relationship_extraction','_normalize_text_extraction_record_attributes','_truncation_cause_suffix','_process_extraction_result']),
]


def defined_names(node):
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
        return [node.name]
    if isinstance(node,ast.Assign):
        return [t.id for t in node.targets if isinstance(t,ast.Name)]
    if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name):
        return [node.target.id]
    return []


def load():
    source_check=verify_source([p for p,_ in SELECTION])
    commit=source_check['official_commit']
    ns={'__name__':'official_lightrag_parser_selective_control','re':re,'html':html,'asyncio':asyncio,'defaultdict':defaultdict,'logger':logging.getLogger('lightrag')}
    selected=[]
    for relative,names in SELECTION:
        path=SOURCE/relative
        source=path.read_text()
        tree=ast.parse(source,filename=str(path))
        mapping={name:node for node in tree.body for name in defined_names(node)}
        for name in names:
            node=mapping[name]
            if hashlib.sha256(source.encode()).hexdigest()!=source_check['selected_file_sha256'][relative]:
                raise RuntimeError('Official parser source changed after verification')
            exact=ast.get_source_segment(source,node)
            module=ast.Module(body=[node],type_ignores=[])
            code=compile(module,str(path),'exec',flags=__future__.annotations.compiler_flag,dont_inherit=True)
            exec(code,ns)
            selected.append({'name':name,'file':relative,'first_line':node.lineno,'last_line':node.end_lineno,'source_sha256':hashlib.sha256(exact.encode()).hexdigest(),'ast_sha256':hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest(),'file_sha256':hashlib.sha256(source.encode()).hexdigest()})
    assert ns['__version__']=='1.5.7'
    unresolved={}
    def check_code(name,code):
        missing=sorted({i.argval for i in dis.get_instructions(code) if i.opname in ('LOAD_GLOBAL','LOAD_NAME') and i.argval not in ns and not hasattr(builtins,i.argval)})
        if missing:unresolved[name]=missing
        for n,constant in enumerate(code.co_consts):
            if isinstance(constant,types.CodeType):check_code(name+f'.nested{n}',constant)
    for name,value in ns.items():
        if isinstance(value,types.FunctionType):check_code(name,value.__code__)
    if unresolved:raise RuntimeError(f'Unresolved official parser dependencies: {unresolved}')
    metadata={**source_check,'load_mode':'selective execution of unchanged official AST nodes; not normal package import','official_version':ns['__version__'],'official_commit':commit,'tracked_source_diff_empty':True,'selected_nodes':selected,'all_loaded_global_dependencies_resolved':True,'injected_standard_library_dependencies':['re','html','asyncio','collections.defaultdict'],'logger_binding':'logging.getLogger("lightrag"), same name as official logger; no semantic adapter','functions_rewritten':False,'normal_package_import_performed':False,'historical_loader_note':'Original experiment used selective AST loading after unrelated GraphML/networkx startup stalled; this does not describe a new import test.'}
    return ns,metadata
