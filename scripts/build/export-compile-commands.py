"""Export commands actually executed by the existing AMBuild 2.1 backend.

This backend predates AMBuild's native compilation database support. Read its
successful local graph without changing build APIs, command lines or SDKs.
"""
import io
import json
from pathlib import Path
import pickle
import sqlite3
import sys


class PrimitiveUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise ValueError('Only primitive AMBuild command data is allowed')


def export(build):
    entries=[]
    graph=build/'.ambuild2/graph'
    with sqlite3.connect(graph.as_uri()+'?mode=ro', uri=True) as db:
        for dirty, folder, blob in db.execute("SELECT n.dirty, f.path, n.data FROM nodes n LEFT JOIN nodes f ON f.id=n.folder WHERE n.type='cxx'"):
            if dirty:
                raise ValueError('Unfinished compilation task in AMBuild graph')
            args=PrimitiveUnpickler(io.BytesIO(blob)).load()['argv']
            if not isinstance(args,list) or not all(isinstance(a,str) for a in args):
                raise ValueError('Invalid compiler argv')
            directory=(build/(folder or '')).resolve()
            # GCC and MSVC both record the original source as an argv element.
            sources=[a for a in args if Path(a).suffix.lower() in {'.cpp','.c','.cc','.cxx'} and (directory/a).is_file()]
            if len(sources)!=1:
                raise ValueError('Expected exactly one input translation unit')
            entries.append({'directory':str(directory),'arguments':args,'file':str((directory/sources[0]).resolve())})
    if not entries:
        raise ValueError('No successful compile commands in AMBuild graph')
    (build/'compile_commands.json').write_text(json.dumps(entries,indent=2)+'\n')


if __name__=='__main__':export(Path(sys.argv[1]).resolve())
